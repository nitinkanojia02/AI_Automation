*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL}    /washtabui/login?data=undefined
${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}    customer-search
${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}    vehicle-survey
${EXPECTED_SITE_SURVEY_URL_FRAGMENT}    survey?data
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Click Person Profile Button
    [Documentation]    Click the Person/Profile button.
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    [Documentation]    Click the Back button.
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    [Documentation]    Click the Notification button.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    [Documentation]    Click the Home button.
    Click When Ready    ${HOME_BUTTON}

Click Customer Signup Button
    [Documentation]    Click the Customer signup button.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Click the Clean survey button.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Click the Site survey button.
    Click When Ready    ${SITE_SURVEY_BUTTON}

Verify Home Page Loaded In Guest State
    [Documentation]    Verify the Home page is loaded in guest state and all approved navigation controls are visible and enabled.
    Location Should Be    ${PAGE_URL}
    Verify All Home Navigation Controls Are Enabled

Verify All Home Navigation Controls Are Enabled
    [Documentation]    Verify all approved Home page navigation controls are enabled and interactive.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Person Profile Navigation Redirect
    [Documentation]    Verify navigation to the login page URL.
    Wait Until Location Is    ${EXPECTED_LOGIN_URL}

Verify Customer Signup Navigation Redirect
    [Documentation]    Verify navigation to the customer-search workflow entry URL.
    Wait Until Location Contains    ${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}

Verify Clean Survey Navigation Redirect
    [Documentation]    Verify navigation to the vehicle-survey workflow entry URL.
    Wait Until Location Contains    ${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}

Verify Site Survey Navigation Redirect
    [Documentation]    Verify navigation to the survey workflow entry URL.
    Wait Until Location Contains    ${EXPECTED_SITE_SURVEY_URL_FRAGMENT}
