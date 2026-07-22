*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_HOME_URL}    http://localhost/washtabui/home
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
    [Documentation]    Verify the Home page loads in guest state and all approved navigation controls are visible and enabled.
    Go To Url    ${PAGE_URL}
    Verify Person Profile Button Visible And Enabled
    Verify Back Button Visible And Enabled
    Verify Notification Button Visible And Enabled
    Verify Home Button Visible And Enabled
    Verify Customer Signup Button Visible And Enabled
    Verify Clean Survey Button Visible And Enabled
    Verify Site Survey Button Visible And Enabled
    Location Should Be    ${EXPECTED_HOME_URL}

Verify Person Profile Button Visible And Enabled
    [Documentation]    Verify the Person/Profile button is visible and enabled.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

Verify Back Button Visible And Enabled
    [Documentation]    Verify the Back button is visible and enabled.
    Wait For Element To Be Ready    ${BACK_BUTTON}

Verify Notification Button Visible And Enabled
    [Documentation]    Verify the Notification button is visible and enabled.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

Verify Home Button Visible And Enabled
    [Documentation]    Verify the Home button is visible and enabled.
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Customer Signup Button Visible And Enabled
    [Documentation]    Verify the Customer signup button is visible and enabled.
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}

Verify Clean Survey Button Visible And Enabled
    [Documentation]    Verify the Clean survey button is visible and enabled.
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}

Verify Site Survey Button Visible And Enabled
    [Documentation]    Verify the Site survey button is visible and enabled.
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Navigation To Login Page
    [Documentation]    Verify navigation to the login page URL.
    Location Should Be    ${EXPECTED_LOGIN_URL}

Verify Navigation To Customer Search Page
    [Documentation]    Verify navigation to the customer-search workflow URL.
    Location Should Contain    ${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}

Verify Navigation To Vehicle Survey Page
    [Documentation]    Verify navigation to the vehicle-survey workflow URL.
    Location Should Contain    ${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}

Verify Navigation To Site Survey Page
    [Documentation]    Verify navigation to the survey workflow URL.
    Location Should Contain    ${EXPECTED_SITE_SURVEY_URL_FRAGMENT}
