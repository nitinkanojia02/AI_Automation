*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${LOGIN_PAGE_IDENTIFIER}    login
${CUSTOMER_SEARCH_PAGE_IDENTIFIER}    customer-search
${VEHICLE_SURVEY_PAGE_IDENTIFIER}    vehicle-survey
${SURVEY_PAGE_IDENTIFIER}    survey
${LOGOUT_TEXT}    Logout
${SIGN_OUT_TEXT}    Sign Out
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

Verify Home Page Guest Controls Visible
    [Documentation]    Verify all approved guest-state controls are visible on the Home page.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Home Page Guest Controls Enabled
    [Documentation]    Verify all approved guest-state controls are enabled on the Home page.
    Wait Until Element Is Enabled    ${PERSON_PROFILE_BUTTON}
    Wait Until Element Is Enabled    ${BACK_BUTTON}
    Wait Until Element Is Enabled    ${NOTIFICATION_BUTTON}
    Wait Until Element Is Enabled    ${HOME_BUTTON}
    Wait Until Element Is Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Wait Until Element Is Enabled    ${CLEAN_SURVEY_BUTTON}
    Wait Until Element Is Enabled    ${SITE_SURVEY_BUTTON}

Verify Authenticated User Indicators Are Not Visible
    [Documentation]    Verify authenticated user indicators and authenticated-only actions are not visible in guest state.
    Page Should Not Contain    ${LOGOUT_TEXT}
    Page Should Not Contain    ${SIGN_OUT_TEXT}

Verify Home Page Loaded In Guest State
    [Documentation]    Verify the Home page is loaded in guest state with approved controls visible and enabled.
    Location Should Contain    ${HOME_PAGE_PATH}
    Verify Home Page Guest Controls Visible
    Verify Home Page Guest Controls Enabled
    Verify Authenticated User Indicators Are Not Visible

Verify Login Page Opened
    [Documentation]    Verify the Login page or Login view is opened from the Home page.
    Location Should Contain    ${LOGIN_PAGE_IDENTIFIER}

Verify Customer Search Page Opened
    [Documentation]    Verify navigation to the customer-search page.
    Location Should Contain    ${CUSTOMER_SEARCH_PAGE_IDENTIFIER}

Verify Vehicle Survey Page Opened
    [Documentation]    Verify navigation to the vehicle-survey page.
    Location Should Contain    ${VEHICLE_SURVEY_PAGE_IDENTIFIER}

Verify Survey Page Opened
    [Documentation]    Verify navigation to the survey page.
    Location Should Contain    ${SURVEY_PAGE_IDENTIFIER}

Verify Home Page Remains In Guest State
    [Documentation]    Verify the Home page remains loaded in guest state after interaction.
    Verify Home Page Loaded In Guest State

Click Person Profile Button
    [Documentation]    Click the Person/Profile button from the Home page.
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    [Documentation]    Click the Back button from the Home page shell.
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    [Documentation]    Click the Notification button from the Home page shell.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    [Documentation]    Click the Home button from the Home page shell.
    Click When Ready    ${HOME_BUTTON}

Click Customer Signup Button
    [Documentation]    Click the Customer signup button from the Home page.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Click the Clean survey button from the Home page.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Click the Site survey button from the Home page.
    Click When Ready    ${SITE_SURVEY_BUTTON}
