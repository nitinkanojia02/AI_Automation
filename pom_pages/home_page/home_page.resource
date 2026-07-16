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
    [Documentation]    Open the Home page using the configured Home page URL.
    Go To Url    ${HOME_PAGE_URL}

Open Home Page In Guest State
    [Documentation]    Open the Home page directly in guest state and verify approved guest controls are available.
    Open Home Page
    Verify Home Page Guest Controls Are Visible

Verify Browser Url Contains Home Path
    [Documentation]    Verify the current browser URL contains the Home page path.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}

Verify Home Page Is Loaded
    [Documentation]    Verify the Home page is loaded successfully in guest state.
    Verify Browser Url Contains Home Path
    Verify Home Page Guest Controls Are Visible

Verify Home Page Guest Controls Are Visible
    [Documentation]    Verify all approved guest-state Home page controls are visible and enabled.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Person Profile Button
    [Documentation]    Verify the Person/Profile button is visible and enabled.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

Verify Notification Button
    [Documentation]    Verify the Notification button is visible and enabled.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

Verify Guest Accessible Feature Buttons
    [Documentation]    Verify guest-accessible feature buttons are visible and enabled.
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
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
    [Documentation]    Verify the Home page remains in guest state with approved guest controls visible.
    Verify Home Page Guest Controls Are Visible

Click Person Profile Button
    [Documentation]    Click the Person/Profile button from the Home page guest state.
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

Refresh Home Page
    [Documentation]    Refresh the current Home page view and verify guest controls remain available.
    Reload Page
    Verify Home Page Remains In Guest State
