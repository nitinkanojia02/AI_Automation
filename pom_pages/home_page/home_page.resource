*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${HOME_GUEST_STATE_DESCRIPTION}    Home page guest state
${UNAUTHENTICATED_STATE_MESSAGE}    User remains unauthenticated
${LOGIN_PAGE_IDENTIFIER}    login
${LOGIN_VIEW_NAME}    Login page or Login view
${CUSTOMER_SEARCH_PAGE_IDENTIFIER}    customer-search
${CUSTOMER_SEARCH_PAGE_NAME}    customer-search page
${VEHICLE_SURVEY_PAGE_IDENTIFIER}    vehicle-survey
${VEHICLE_SURVEY_PAGE_NAME}    vehicle-survey page
${SURVEY_PAGE_IDENTIFIER}    survey
${SURVEY_PAGE_NAME}    survey page
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page In Guest State
    [Documentation]    Open the Home page in guest state.
    Open Browser To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded In Guest State

Verify Home Guest State Controls Are Visible
    [Documentation]    Verify all approved guest-state controls are visible.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Home Guest State Controls Are Enabled
    [Documentation]    Verify all approved guest-state controls are enabled.
    Element Should Be Enabled    ${PERSON_PROFILE_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

Verify Home Page Loaded In Guest State
    [Documentation]    Verify the Home page is loaded in guest state.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}
    Verify Home Guest State Controls Are Visible
    Verify Home Guest State Controls Are Enabled

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
    [Documentation]    Verify the application returns to the Home page guest state.
    Verify Home Page Loaded In Guest State

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
