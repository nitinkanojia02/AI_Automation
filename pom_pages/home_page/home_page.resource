*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL_PATH}    /washtabui/login
${CUSTOMER_SEARCH_PAGE_PATH}    customer-search
${VEHICLE_SURVEY_PAGE_PATH}    vehicle-survey
${SURVEY_PAGE_PATH}    survey
${HOME_PAGE_LOAD_TIMEOUT}    10s
${PERSON_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Navigate to the guest Home page.
    Go To Url    ${HOME_PAGE_URL}

Open Home Page In Guest State
    [Documentation]    Open the Home page directly in guest state and wait for approved guest controls to be ready.
    Open Home Page
    Verify Guest State Controls Are Visible

Verify Home Page URL
    [Documentation]    Verify the browser is currently on the Home page.
    ${current_url}=    Get Location
    Should Be Equal    ${current_url}    ${HOME_PAGE_URL}

Verify Login Page URL
    [Documentation]    Verify navigation to the login page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${LOGIN_PAGE_URL_PATH}

Verify Home Page Is Loaded
    [Documentation]    Verify the Home page is loaded successfully with approved guest controls available.
    Verify Home Page URL
    Verify Guest State Controls Are Visible
    Verify Guest Home Controls Are Enabled

Verify Guest State Controls Are Visible
    [Documentation]    Verify all approved guest-state controls are visible and enabled on the Home page.
    Wait For Element To Be Ready    ${PERSON_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${BACK_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${HOME_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Verify Guest Home Controls Are Enabled
    [Documentation]    Verify all approved guest-state controls are enabled and actionable.
    Element Should Be Enabled    ${PERSON_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

Verify Home Page Remains In Guest State
    [Documentation]    Verify the Home page remains in guest state with approved guest controls visible.
    Verify Home Page Is Loaded

Verify User Is Navigated To Login Page
    [Documentation]    Verify the user is redirected to the login page after clicking the Person/Profile button.
    Verify Login Page URL

Verify Customer Search Page Navigation
    [Documentation]    Verify navigation to the customer-search page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${CUSTOMER_SEARCH_PAGE_PATH}

Verify Vehicle Survey Page Navigation
    [Documentation]    Verify navigation to the vehicle-survey page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${VEHICLE_SURVEY_PAGE_PATH}

Verify Survey Page Navigation
    [Documentation]    Verify navigation to the survey page.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    ${SURVEY_PAGE_PATH}

Verify Person Button
    [Documentation]    Verify the Login page or Login view opens after clicking the Person/Profile button.
    Click Person Button
    Verify User Is Navigated To Login Page

Refresh Home Page
    [Documentation]    Refresh the current Home page view and verify guest controls remain available.
    Reload Page
    Verify Home Page Remains In Guest State

Click Person Button
    [Documentation]    Click the Person/Profile button from the Home page guest state.
    Click When Ready    ${PERSON_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Back Button
    [Documentation]    Click the Back button from the Home page shell.
    Click When Ready    ${BACK_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Notification Button
    [Documentation]    Click the Notification button from the Home page shell.
    Click When Ready    ${NOTIFICATION_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Home Button
    [Documentation]    Click the Home button from the Home page shell.
    Click When Ready    ${HOME_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Customer Signup Button
    [Documentation]    Click the Customer signup button from the Home page guest state.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Clean Survey Button
    [Documentation]    Click the Clean survey button from the Home page guest state.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}

Click Site Survey Button
    [Documentation]    Click the Site survey button from the Home page guest state.
    Click When Ready    ${SITE_SURVEY_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
