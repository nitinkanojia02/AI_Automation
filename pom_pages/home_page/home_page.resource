*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${LOGIN_PAGE_IDENTIFIER}    login
${CUSTOMER_SEARCH_PAGE_IDENTIFIER}    customer-search
${VEHICLE_SURVEY_PAGE_IDENTIFIER}    vehicle-survey
${SURVEY_PAGE_IDENTIFIER}    survey
${LOGIN_VIEW_NAME}    Login page or Login view
${CUSTOMER_SEARCH_PAGE_NAME}    customer-search page
${VEHICLE_SURVEY_PAGE_NAME}    vehicle-survey page
${SURVEY_PAGE_NAME}    survey page
${GUEST_STATE_NAME}    guest state
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Open the Home page and verify the guest state is loaded.
    Open Browser To Url    ${PAGE_URL}
    Verify Home Page Guest State Loaded

Verify Home Page Guest State Loaded
    [Documentation]    Verify the Home page is loaded in guest state.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}
    Verify Guest State Controls Visible And Enabled

Verify Guest State Controls Visible And Enabled
    [Documentation]    Verify approved guest-state controls are visible and enabled.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Login Page Opened
    [Documentation]    Verify navigation to the Login page or Login view.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${LOGIN_PAGE_IDENTIFIER}

Verify Customer Search Page Opened
    [Documentation]    Verify navigation to the customer-search page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${CUSTOMER_SEARCH_PAGE_IDENTIFIER}

Verify Vehicle Survey Page Opened
    [Documentation]    Verify navigation to the vehicle-survey page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${VEHICLE_SURVEY_PAGE_IDENTIFIER}

Verify Survey Page Opened
    [Documentation]    Verify navigation to the survey page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${SURVEY_PAGE_IDENTIFIER}

Verify Home Page Remains In Guest State
    [Documentation]    Verify the application remains in Home guest state.
    Verify Home Page Guest State Loaded

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
