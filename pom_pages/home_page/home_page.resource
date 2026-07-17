*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${LOGIN_PAGE_IDENTIFIER}    login
${CUSTOMER_SEARCH_PAGE_IDENTIFIER}    customer-search
${VEHICLE_SURVEY_PAGE_IDENTIFIER}    vehicle-survey
${SURVEY_PAGE_IDENTIFIER}    survey
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Navigate directly to the Home page guest state URL.
    Go To Url    ${HOME_PAGE_URL}
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

Verify Guest Home Page Loaded
    [Documentation]    Verify the Home page is loaded in guest state with approved controls visible and enabled.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}
    Verify Home Guest State Controls Are Visible
    Verify Home Guest State Controls Are Enabled

Verify Home Guest State Controls Are Visible
    [Documentation]    Verify approved guest-state Home controls are visible.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Home Guest State Controls Are Enabled
    [Documentation]    Verify approved guest-state Home controls are enabled.
    Wait Until Element Is Enabled    ${PERSON_PROFILE_BUTTON}
    Wait Until Element Is Enabled    ${BACK_BUTTON}
    Wait Until Element Is Enabled    ${NOTIFICATION_BUTTON}
    Wait Until Element Is Enabled    ${HOME_BUTTON}
    Wait Until Element Is Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Wait Until Element Is Enabled    ${CLEAN_SURVEY_BUTTON}
    Wait Until Element Is Enabled    ${SITE_SURVEY_BUTTON}

Verify Person Profile Button
    [Documentation]    Verify the Person/Profile button is visible and enabled.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

Verify Back Button
    [Documentation]    Verify the Back button is visible and enabled.
    Wait For Element To Be Ready    ${BACK_BUTTON}

Verify Notification Button
    [Documentation]    Verify the Notification button is visible and enabled.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

Verify Home Button
    [Documentation]    Verify the Home button is visible and enabled.
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Customer Signup Button
    [Documentation]    Verify the Customer signup button is visible and enabled.
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}

Verify Clean Survey Button
    [Documentation]    Verify the Clean survey button is visible and enabled.
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}

Verify Site Survey Button
    [Documentation]    Verify the Site survey button is visible and enabled.
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Login Page Opened
    [Documentation]    Verify the Login page or Login view is opened from the Home page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${LOGIN_PAGE_IDENTIFIER}

Verify Customer Search Page Opened
    [Documentation]    Verify navigation to the customer-search workflow.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${CUSTOMER_SEARCH_PAGE_IDENTIFIER}

Verify Vehicle Survey Page Opened
    [Documentation]    Verify navigation to the vehicle-survey workflow.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${VEHICLE_SURVEY_PAGE_IDENTIFIER}

Verify Survey Page Opened
    [Documentation]    Verify navigation to the survey workflow.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${SURVEY_PAGE_IDENTIFIER}

Verify Home Page Remains In Guest State
    [Documentation]    Verify the Home page remains in guest state with approved guest controls visible and enabled.
    Verify Guest Home Page Loaded

Click Person Profile Button
    [Documentation]    Click the Person/Profile button from the Home page guest state.
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    [Documentation]    Click the shared Back button from the Home page shell.
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    [Documentation]    Click the Notification button from the Home page shell.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    [Documentation]    Click the shared Home button from the Home page shell.
    Click When Ready    ${HOME_BUTTON}

Click Customer Signup Button
    [Documentation]    Click the Customer signup button from the Home guest state.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Click the Clean survey button from the Home guest state.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Click the Site survey button from the Home guest state.
    Click When Ready    ${SITE_SURVEY_BUTTON}
