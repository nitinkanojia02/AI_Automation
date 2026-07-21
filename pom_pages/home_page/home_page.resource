*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${HOME_GUEST_STATE_URL}    http://localhost/washtabui/home
${HOME_PAGE_PATH}    /washtabui/home
${HOME_GUEST_STATE_NAME}    Home page guest state
${LOGIN_VIEW_NAME}    Login page or Login view
${CUSTOMER_SEARCH_PAGE_NAME}    customer-search page
${VEHICLE_SURVEY_PAGE_NAME}    vehicle-survey page
${SURVEY_PAGE_NAME}    survey page
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
Open Home Page In Guest State
    [Documentation]    Open the Home page using the approved guest-state entry URL.
    Open Browser To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled

Verify Home Guest State Loaded
    [Documentation]    Verify the Home page guest state is loaded with approved guest controls visible and enabled.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${HOME_PAGE_PATH}
    Verify Person Profile Button Visible And Enabled
    Verify Back Button Visible And Enabled
    Verify Notification Button Visible And Enabled
    Verify Home Button Visible And Enabled
    Verify Customer Signup Button Visible And Enabled
    Verify Clean Survey Button Visible And Enabled
    Verify Site Survey Button Visible And Enabled

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

Verify Guest State Controls Are Enabled
    [Documentation]    Verify approved guest-state controls are enabled.
    Element Should Be Enabled    ${PERSON_PROFILE_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

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
    [Documentation]    Verify the application remains in guest state after navigation or interaction.
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled

Click Auto Person Btn Button
    [Documentation]    Click the Person/Profile button.
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Auto Back Btn Button
    [Documentation]    Click the Back button.
    Click When Ready    ${BACK_BUTTON}

Click Auto Notification Btn Button
    [Documentation]    Click the Notification button.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Auto Home Btn Button
    [Documentation]    Click the Home button.
    Click When Ready    ${HOME_BUTTON}

Click Auto Btn Customer Signup Button
    [Documentation]    Click the Customer signup button.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Auto Btn Clean Survey Button
    [Documentation]    Click the Clean survey button.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Auto Btn Site Survey Button
    [Documentation]    Click the Site survey button.
    Click When Ready    ${SITE_SURVEY_BUTTON}
