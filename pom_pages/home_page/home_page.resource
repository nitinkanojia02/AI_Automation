*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL_PATH}    /washtabui/login
${CUSTOMER_SEARCH_PAGE_PATH}    customer-search
${VEHICLE_SURVEY_PAGE_PATH}    vehicle-survey
${SURVEY_PAGE_PATH}    survey
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Open the Home page in guest state.
    Open Browser To Url    ${HOME_PAGE_URL}

Open Home Page In Guest State
    [Documentation]    Open the Home page directly in guest state and wait for approved guest controls to be ready.
    Open Home Page
    Verify Guest State Controls Are Visible

Verify Home Page URL
    [Documentation]    Verify the browser is currently on the Home page.
    Location Should Be    ${HOME_PAGE_URL}

Verify Login Page URL
    [Documentation]    Verify navigation to the login page.
    Wait Until Location Contains    ${LOGIN_PAGE_URL_PATH}    ${DEFAULT_TIMEOUT}

Verify Home Page Is Loaded
    [Documentation]    Verify the Home page is loaded successfully with approved guest controls available.
    Verify Home Page URL
    Verify Guest State Controls Are Visible
    Verify Guest Home Controls Are Enabled

Verify Guest State Controls Are Visible
    [Documentation]    Verify all approved guest-state controls are visible and enabled on the Home page.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Guest Home Controls Are Enabled
    [Documentation]    Verify all approved guest-state controls are enabled and actionable.
    Element Should Be Enabled    ${PERSON_PROFILE_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

Verify Home Page Remains In Guest State
    [Documentation]    Verify the Home page remains in guest state with approved controls available.
    Verify Home Page Is Loaded

Verify User Is Navigated To Login Page
    [Documentation]    Verify the user is redirected to the login page after clicking the Person/Profile button.
    Verify Login Page URL

Verify Customer Search Page Navigation
    [Documentation]    Verify navigation to the customer-search page.
    Wait Until Location Contains    ${CUSTOMER_SEARCH_PAGE_PATH}    ${DEFAULT_TIMEOUT}

Verify Vehicle Survey Page Navigation
    [Documentation]    Verify navigation to the vehicle-survey page.
    Wait Until Location Contains    ${VEHICLE_SURVEY_PAGE_PATH}    ${DEFAULT_TIMEOUT}

Verify Survey Page Navigation
    [Documentation]    Verify navigation to the survey page.
    Wait Until Location Contains    ${SURVEY_PAGE_PATH}    ${DEFAULT_TIMEOUT}

Refresh Home Page
    [Documentation]    Refresh the current Home page view and verify guest controls remain available.
    Reload Page
    Verify Home Page Remains In Guest State

Click Person Profile Button
    [Documentation]    Click the Person/Profile button from the guest Home state.
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    [Documentation]    Click the shared back navigation control.
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    [Documentation]    Click the shared notification control.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    [Documentation]    Click the home navigation control.
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
