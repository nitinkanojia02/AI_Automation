*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${HOME_GUEST_STATE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${LOGIN_PAGE_IDENTIFIER}    login
${CUSTOMER_SEARCH_PAGE_IDENTIFIER}    customer-search
${VEHICLE_SURVEY_PAGE_IDENTIFIER}    vehicle-survey
${SURVEY_PAGE_IDENTIFIER}    survey
${LOGIN_VIEW_NAME}    Login page or Login view
${CUSTOMER_SEARCH_VIEW_NAME}    customer-search page
${VEHICLE_SURVEY_VIEW_NAME}    vehicle-survey page
${SITE_SURVEY_VIEW_NAME}    survey page
${EXPECTED_GUEST_STATE_MESSAGE}    The Home page loads successfully in guest state with guest-accessible controls visible and no authenticated user state displayed.
${EXPECTED_UNAUTHENTICATED_STATE_MESSAGE}    No logged-in user name button or authenticated identity indicator is visible while the user remains unauthenticated.
${EXPECTED_AUTH_ONLY_CONTROLS_HIDDEN_MESSAGE}    Authenticated-only controls and feature buttons are not visible or remain non-actionable in guest state.
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page In Guest State
    [Documentation]    Open the Home page using the approved guest-state entry URL.
    Open Browser To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Page Loaded In Guest State

Verify Home Page Loaded In Guest State
    [Documentation]    Verify the Home page is loaded in guest state and approved guest controls are visible and enabled.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}
    Verify Guest State Controls Are Visible
    Verify Guest State Controls Are Enabled

Verify Guest State Controls Are Visible
    [Documentation]    Verify approved guest-state controls are visible.
    Wait Until Element Is Visible    ${PERSON_PROFILE_BUTTON}
    Wait Until Element Is Visible    ${BACK_BUTTON}
    Wait Until Element Is Visible    ${NOTIFICATION_BUTTON}
    Wait Until Element Is Visible    ${HOME_BUTTON}
    Wait Until Element Is Visible    ${CUSTOMER_SIGNUP_BUTTON}
    Wait Until Element Is Visible    ${CLEAN_SURVEY_BUTTON}
    Wait Until Element Is Visible    ${SITE_SURVEY_BUTTON}

Verify Guest State Controls Are Enabled
    [Documentation]    Verify approved guest-state controls are enabled.
    Wait Until Element Is Enabled    ${PERSON_PROFILE_BUTTON}
    Wait Until Element Is Enabled    ${BACK_BUTTON}
    Wait Until Element Is Enabled    ${NOTIFICATION_BUTTON}
    Wait Until Element Is Enabled    ${HOME_BUTTON}
    Wait Until Element Is Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Wait Until Element Is Enabled    ${CLEAN_SURVEY_BUTTON}
    Wait Until Element Is Enabled    ${SITE_SURVEY_BUTTON}

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
    [Documentation]    Verify the application remains in Home guest state after navigation or interaction.
    Verify Home Page Loaded In Guest State

Click Person Button
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
