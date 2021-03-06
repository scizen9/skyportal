import uuid
import datetime
import pytest

from skyportal.tests import api

from tdtax import taxonomy, __version__


@pytest.mark.flaky(reruns=2)
def test_candidate_group_filtering(
    driver,
    user,
    public_candidate,
    public_filter,
    public_group,
    upload_data_token,
    super_admin_token,
):
    candidate_id = str(uuid.uuid4())
    for i in range(5):
        status, data = api(
            "POST",
            "candidates",
            data={
                "id": f"{candidate_id}_{i}",
                "ra": 234.22,
                "dec": -22.33,
                "redshift": 3,
                "altdata": {"simbad": {"class": "RRLyr"}},
                "transient": False,
                "ra_dis": 2.3,
                "passed_at": str(datetime.datetime.utcnow()),
                "filter_ids": [public_filter.id],
            },
            token=upload_data_token,
        )
        assert status == 200

    status, data = api(
        "POST",
        "groups",
        data={"name": str(uuid.uuid4()), "group_admins": [user.id]},
        token=super_admin_token,
    )
    new_group_id = data['data']['id']
    assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    group_checkbox = driver.wait_for_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]'
    )
    driver.scroll_to_element_and_click(group_checkbox)
    submit_button = driver.wait_for_xpath('//span[text()="Search"]')
    driver.scroll_to_element_and_click(submit_button)
    for i in range(5):  # data-testid
        driver.wait_for_xpath(f'//a[@data-testid="{candidate_id}_{i}"]')
    driver.scroll_to_element_and_click(group_checkbox)
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{new_group_id}"]',
        wait_clickable=False,
    )
    driver.scroll_to_element_and_click(submit_button)
    for i in range(5):
        driver.wait_for_xpath_to_disappear(f'//a[@data-testid="{candidate_id}_{i}"]')


@pytest.mark.flaky(reruns=2)
def test_candidate_saved_status_filtering(
    driver,
    user,
    public_candidate,
    public_filter,
    public_group,
    upload_data_token,
    manage_groups_token,
):
    # This test just tests basic unsaved/saved filtering to test integration of
    # the front-end form. More detailed testing of all options are covered in
    # the API tests.
    candidate_id = str(uuid.uuid4())
    for i in range(5):
        status, data = api(
            "POST",
            "sources",
            data={
                "id": f"{candidate_id}_{i}",
                "ra": 234.22,
                "dec": -22.33,
                "redshift": 3,
                "altdata": {"simbad": {"class": "RRLyr"}},
                "transient": False,
                "ra_dis": 2.3,
                "group_ids": [public_group.id],
            },
            token=upload_data_token,
        )
        assert status == 200
        status, data = api(
            "POST",
            "candidates",
            data={
                "id": f"{candidate_id}_{i}",
                "ra": 234.22,
                "dec": -22.33,
                "redshift": 3,
                "altdata": {"simbad": {"class": "RRLyr"}},
                "transient": False,
                "ra_dis": 2.3,
                "filter_ids": [public_filter.id],
                "passed_at": str(datetime.datetime.utcnow()),
            },
            token=upload_data_token,
        )
        assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    # Set to candidates not saved to any accessibe groups
    driver.click_xpath("//*[@data-testid='savedStatusSelect']")
    driver.click_xpath(
        "//li[@data-value='notSavedToAnyAccessible']", scroll_parent=True
    )
    driver.click_xpath('//span[text()="Search"]')
    for i in range(5):
        driver.wait_for_xpath_to_disappear(f'//a[@data-testid="{candidate_id}_{i}"]')

    # Set to candidates is saved to any accessibe groups and submit again
    driver.click_xpath("//*[@data-testid='savedStatusSelect']")
    driver.click_xpath("//li[@data-value='savedToAnyAccessible']", scroll_parent=True)
    driver.click_xpath('//span[text()="Search"]')
    for i in range(5):
        driver.wait_for_xpath(f'//a[@data-testid="{candidate_id}_{i}"]')


@pytest.mark.flaky(reruns=2)
def test_candidate_date_filtering(
    driver,
    user,
    public_candidate,
    public_filter,
    public_group,
    upload_data_token,
    ztf_camera,
):
    candidate_id = str(uuid.uuid4())
    for i in range(5):
        status, data = api(
            "POST",
            "candidates",
            data={
                "id": f"{candidate_id}_{i}",
                "ra": 234.22,
                "dec": -22.33,
                "redshift": 3,
                "altdata": {"simbad": {"class": "RRLyr"}},
                "transient": False,
                "ra_dis": 2.3,
                "filter_ids": [public_filter.id],
                "passed_at": str(datetime.datetime.utcnow()),
            },
            token=upload_data_token,
        )
        assert status == 200

        status, data = api(
            "POST",
            "photometry",
            data={
                "obj_id": f"{candidate_id}_{i}",
                "mjd": 58000.0,
                "instrument_id": ztf_camera.id,
                "flux": 12.24,
                "fluxerr": 0.031,
                "zp": 25.0,
                "magsys": "ab",
                "filter": "ztfr",
                "group_ids": [public_group.id],
            },
            token=upload_data_token,
        )
        assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    start_date_input = driver.wait_for_xpath(
        "//*[@data-testid='startDatePicker']//input"
    )
    start_date_input.clear()
    start_date_input.send_keys("200012120000")
    end_date_input = driver.wait_for_xpath("//*[@data-testid='endDatePicker']//input")
    end_date_input.clear()
    end_date_input.send_keys("200112120000")
    submit_button = driver.wait_for_xpath_to_be_clickable('//span[text()="Search"]')
    driver.scroll_to_element_and_click(submit_button)
    for i in range(5):
        driver.wait_for_xpath_to_disappear(
            f'//a[@data-testid="{candidate_id}_{i}"]', 10
        )
    end_date_input.clear()
    end_date_input.send_keys("209012120000")
    submit_button = driver.wait_for_xpath_to_be_clickable('//span[text()="Search"]')
    driver.scroll_to_element_and_click(submit_button)
    for i in range(5):
        driver.wait_for_xpath(f'//a[@data-testid="{candidate_id}_{i}"]', 10)


@pytest.mark.flaky(reruns=2)
def test_save_candidate_quick_save(
    driver, group_admin_user, public_group, public_candidate
):
    driver.get(f"/become_user/{group_admin_user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath('//span[text()="Search"]', wait_clickable=False)
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')
    save_button = driver.wait_for_xpath(
        f'//button[@name="initialSaveCandidateButton{public_candidate.id}"]'
    )
    driver.scroll_to_element_and_click(save_button)
    driver.wait_for_xpath_to_disappear(
        f'//button[@name="initialSaveCandidateButton{public_candidate.id}"]'
    )
    driver.wait_for_xpath('//span[text()="Previously Saved"]')


@pytest.mark.flaky(reruns=2)
def test_save_candidate_select_groups(
    driver, group_admin_user, public_group, public_candidate
):
    driver.get(f"/become_user/{group_admin_user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath('//span[text()="Search"]')
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')
    carat = driver.wait_for_xpath(
        f'//button[@name="saveCandidateButtonDropDownArrow{public_candidate.id}"]'
    )
    driver.scroll_to_element_and_click(carat)
    driver.execute_script(
        "arguments[0].click();",
        driver.wait_for_xpath_to_be_clickable(
            f'//*[@name="buttonMenuOption{public_candidate.id}_Select groups & save"]'
        ),
    )
    save_button = driver.wait_for_xpath_to_be_clickable(
        f'//button[@name="initialSaveCandidateButton{public_candidate.id}"]'
    )
    driver.scroll_to_element_and_click(save_button)

    second_save_button = driver.wait_for_xpath(
        f'//button[@name="finalSaveCandidateButton{public_candidate.id}"]'
    )
    second_save_button.click()
    driver.wait_for_xpath_to_disappear(
        f'//button[@name="initialSaveCandidateButton{public_candidate.id}"]'
    )
    driver.wait_for_xpath('//span[text()="Previously Saved"]')


@pytest.mark.flaky(reruns=2)
def test_save_candidate_no_groups_error_message(
    driver, group_admin_user, public_group, public_candidate
):
    driver.get(f"/become_user/{group_admin_user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath('//span[text()="Search"]')
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')
    carat = driver.wait_for_xpath_to_be_clickable(
        f'//button[@name="saveCandidateButtonDropDownArrow{public_candidate.id}"]'
    )
    driver.scroll_to_element_and_click(carat)
    driver.execute_script(
        "arguments[0].click();",
        driver.wait_for_xpath_to_be_clickable(
            f'//*[@name="buttonMenuOption{public_candidate.id}_Select groups & save"]'
        ),
    )
    save_button = driver.wait_for_xpath_to_be_clickable(
        f'//button[@name="initialSaveCandidateButton{public_candidate.id}"]'
    )
    driver.scroll_to_element_and_click(save_button)

    group_checkbox = driver.wait_for_xpath(
        f"//*[@data-testid='saveCandGroupCheckbox-{public_group.id}']"
    )
    group_checkbox.click()
    second_save_button = driver.wait_for_xpath_to_be_clickable(
        f'//button[@name="finalSaveCandidateButton{public_candidate.id}"]'
    )
    second_save_button.click()
    driver.wait_for_xpath('//div[contains(.,"Select at least one group")]')


@pytest.mark.flaky(reruns=2)
def test_submit_annotations_sorting(
    driver,
    view_only_user,
    public_group,
    public_candidate,
    public_candidate2,
    annotation_token,
):
    origin = str(uuid.uuid4())[:5]
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"numeric_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    driver.get(f"/become_user/{view_only_user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath('//span[text()="Search"]')
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')

    driver.click_xpath("//p[text()='numeric_field: 1.0000']")
    # Check to see that selected annotation appears in info column
    driver.wait_for_xpath(
        '//td[contains(@data-testid, "MuiDataTableBodyCell")][.//span[text()=1.0000]]'
    )

    # Check to see that sorting button has become enabled, and click
    driver.wait_for_xpath_to_be_clickable(
        "//button[@data-testid='sortOnAnnotationButton']"
    )
    driver.click_xpath("//button[@data-testid='sortOnAnnotationButton']")

    # Check that results come back as expected
    # Col 1, Row 0 should be the first candidate's info (MuiDataTableBodyCell-1-0)
    driver.wait_for_xpath(
        '//td[contains(@data-testid, "MuiDataTableBodyCell-1-0")][.//span[text()="1.0000"]]'
    )
    # Col 1, Row 1 should be the second candidate's info (MuiDataTableBodyCell-1-1)
    driver.wait_for_xpath(
        '//td[contains(@data-testid, "MuiDataTableBodyCell-1-1")][.//span[text()="2.0000"]]'
    )


@pytest.mark.flaky(reruns=2)
def test_submit_annotations_filtering(
    driver,
    view_only_user,
    public_group,
    public_candidate,
    public_candidate2,
    annotation_token,
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"numeric_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    driver.get(f"/become_user/{view_only_user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath('//span[text()="Search"]')
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')

    # scroll to top of page so dialog doesn't get cut off
    element = driver.wait_for_xpath("//button[@data-testid='Filter Table-iconButton']")
    scroll_element_to_top = '''
        const viewPortHeight = Math.max(document.documentElement.clientHeight, window.innerHeight || 0);
        const elementTop = arguments[0].getBoundingClientRect().top;
        window.scrollBy(0, viewPortHeight - elementTop);
    '''
    driver.execute_script(scroll_element_to_top, element)
    element.click()

    # Filter by numeric_field < 1.5
    driver.click_xpath("//div[@id='root_origin']")
    driver.click_xpath(f'//li[@data-value="{origin}"]', scroll_parent=True)
    driver.click_xpath("//div[@id='root_key']")
    driver.click_xpath(
        f"//li[@data-value='{origin}<>numeric_field']", scroll_parent=True
    )
    min_box = driver.wait_for_xpath("//*[@id='root_min']")
    min_text = "0"
    min_box.send_keys(min_text)
    max_box = driver.wait_for_xpath("//*[@id='root_max']")
    max_text = "1.5"
    max_box.send_keys(max_text)
    driver.click_xpath("//span[text()='Submit']")

    # Check that results come back as expected
    # The first candidate should exist
    driver.wait_for_xpath(f'//a[@data-testid="{public_candidate.id}"]')
    # The second candidate should not exist
    driver.wait_for_xpath_to_disappear(f'//a[@data-testid="{public_candidate2.id}"]')


def test_candidate_classifications_filtering(
    driver,
    user,
    public_candidate,
    public_filter,
    public_group,
    upload_data_token,
    taxonomy_token,
    classification_token,
):
    # Post an object with a classification
    candidate_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": candidate_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "sources",
        data={"id": candidate_id},
        token=upload_data_token,
    )
    assert status == 200
    status, data = api(
        'POST',
        'taxonomy',
        data={
            'name': "test taxonomy" + str(uuid.uuid4()),
            'hierarchy': taxonomy,
            'group_ids': [public_group.id],
            'provenance': f"tdtax_{__version__}",
            'version': __version__,
            'isLatest': True,
        },
        token=taxonomy_token,
    )
    assert status == 200
    taxonomy_id = data['data']['taxonomy_id']

    status, data = api(
        'POST',
        'classification',
        data={
            'obj_id': candidate_id,
            'classification': 'Algol',
            'taxonomy_id': taxonomy_id,
            'probability': 1.0,
            'group_ids': [public_group.id],
        },
        token=classification_token,
    )
    assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    driver.click_xpath("//div[@id='classifications-select']")
    driver.click_xpath("//li[@data-value='Algol']", scroll_parent=True)
    driver.click_xpath('//span[text()="Search"]')
    # Should see the posted classification
    driver.wait_for_xpath(f'//a[@data-testid="{candidate_id}"]')

    # Now search for a different classification
    driver.click_xpath("//div[@id='classifications-select']")
    # Clear old classification selection
    driver.click_xpath("//li[@data-value='Algol']", scroll_parent=True)
    driver.click_xpath("//li[@data-value='AGN']", scroll_parent=True)
    driver.click_xpath('//span[text()="Search"]')
    # Should no longer see the classification
    driver.wait_for_xpath_to_disappear(f'//a[@data-testid="{candidate_id}"]')


def test_candidate_redshift_filtering(
    driver,
    user,
    public_filter,
    public_group,
    upload_data_token,
):
    # Post candidates with different redshifts
    obj_id1 = str(uuid.uuid4())
    obj_id2 = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id1,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 0,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id2,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 1,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )
    min_box = driver.wait_for_xpath("//input[@id='minimum-redshift']")
    min_text = "0"
    min_box.send_keys(min_text)
    max_box = driver.wait_for_xpath("//input[@id='maximum-redshift']")
    max_text = "0.5"
    max_box.send_keys(max_text)
    driver.click_xpath('//span[text()="Search"]')
    # Should see the obj_id1 but not obj_id2
    driver.wait_for_xpath(f'//a[@data-testid="{obj_id1}"]')
    driver.wait_for_xpath_to_disappear(f'//a[@data-testid="{obj_id2}"]')


def test_candidate_rejection_filtering(
    driver,
    user,
    public_group,
    upload_data_token,
    public_filter,
):

    candidate_id = str(uuid.uuid4())

    status, data = api(
        "POST",
        "candidates",
        data={
            "id": candidate_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "altdata": {"simbad": {"class": "RRLyr"}},
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    driver.get(f"/become_user/{user.id}")
    driver.get("/candidates")
    driver.click_xpath(
        f'//*[@data-testid="filteringFormGroupCheckbox-{public_group.id}"]',
        wait_clickable=False,
    )

    driver.click_xpath('//span[text()="Search"]')

    # make sure candidate appears and click the icon to reject it
    driver.click_xpath(f'//*[@data-testid="rejected-visible_{candidate_id}"]')

    driver.click_xpath('//span[text()="Search"]')

    # now the candidate doesn't show up anymore
    driver.wait_for_xpath('//*[contains(text(), "no matching records found")]')

    # choose to show rejected now
    driver.click_xpath('//div[@id="mui-component-select-rejectedStatus"]')
    driver.click_xpath("//li[@data-value='show']", scroll_parent=True)
    driver.click_xpath('//span[text()="Search"]')

    # make sure candidate appears and that it has a "rejected" icon
    driver.wait_for_xpath(f'//*[@data-testid="rejected_invisible_{candidate_id}"]')
