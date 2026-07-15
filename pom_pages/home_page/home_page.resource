*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL_PATH}    /washtabui/login
${CUSTOMER_SEARCH_PAGE_PATH}    customer-search
${VEHICLE_SURVEY_PAGE_PATH}    vehicle-survey
${SURVEY_PAGE_PATH}    survey
${ELEMENT_WAIT_TIMEOUT}    10s
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
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

Verify Home Page URL
    [Documentation]    Verify the browser is currently on the Home page.
    Location Should Be    ${HOME_PAGE_URL}

Verify Login Page URL
    [Documentation]    Verify navigation to the login page.
    Wait Until Location Contains    ${LOGIN_PAGE_URL_PATH}    ${DEFAULT_TIMEOUT}

Verify Home Page Is Loaded
    [Documentation]    Verify the Home page is loaded successfully with approved guest controls available.
    Wait Until Location Contains    ${HOME_PAGE_URL}    ${DEFAULT_TIMEOUT}
    Verify Guest Home Controls Are Visible
    Verify Guest Home Controls Are Enabled

Verify Guest Home Controls Are Visible
    [Documentation]    Verify all approved guest-state controls are visible on the Home page.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Element Should Be Visible    ${BACK_BUTTON}
    Element Should Be Visible    ${NOTIFICATION_BUTTON}
    Element Should Be Visible    ${HOME_BUTTON}
    Element Should Be Visible    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Visible    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Visible    ${SITE_SURVEY_BUTTON}

Verify Guest Home Controls Are Enabled
    [Documentation]    Verify all approved guest-state controls are enabled and actionable.
    Element Should Be Enabled    ${PERSON_PROFILE_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

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
    Verify Home Page Is Loaded

Click Person Profile Button
    [Documentation]    Open the login page or login view from guest Home state.
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
    [Documentation]    Navigate to the customer signup or customer search workflow.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Navigate to the clean survey workflow.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Navigate to the site survey workflow.
    Click When Ready    ${SITE_SURVEY_BUTTON}
