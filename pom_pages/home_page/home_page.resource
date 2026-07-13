*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL}    http://localhost/washtabui/login?data=undefined
${CUSTOMER_SEARCH_PAGE_PATH}    customer-search
${VEHICLE_SURVEY_PAGE_PATH}    vehicle-survey
${SURVEY_PAGE_PATH}    survey
${PERSON_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Navigate to the home page URL.
    Go To Url    ${HOME_PAGE_URL}

Open Home Page In Browser
    [Documentation]    Open browser session and navigate to the home page.
    Open Browser To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded

Verify Home Page Is Loaded
    [Documentation]    Verify the home page is loaded successfully.
    Wait Until Location Is    ${HOME_PAGE_URL}    ${DEFAULT_TIMEOUT}
    Verify Home Page Controls Are Visible

Verify Home Page Controls Are Visible
    [Documentation]    Verify all approved controls are visible and enabled on the home page.
    Wait For Element To Be Ready    ${PERSON_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify User Is Navigated To Login Page
    [Documentation]    Verify navigation to the login page using the expected URL.
    Wait Until Location Is    ${LOGIN_PAGE_URL}    ${DEFAULT_TIMEOUT}

Verify Customer Search Page Navigation
    [Documentation]    Verify navigation to the customer-search page.
    Wait Until Keyword Succeeds    10s    1s    Location Should Contain    ${CUSTOMER_SEARCH_PAGE_PATH}

Verify Vehicle Survey Page Navigation
    [Documentation]    Verify navigation to the vehicle-survey page.
    Wait Until Keyword Succeeds    10s    1s    Location Should Contain    ${VEHICLE_SURVEY_PAGE_PATH}

Verify Survey Page Navigation
    [Documentation]    Verify navigation to the survey page.
    Wait Until Keyword Succeeds    10s    1s    Location Should Contain    ${SURVEY_PAGE_PATH}

Verify Notification Button Is Functional
    [Documentation]    Verify the notification button remains visible and interactable.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

Click Person Button
    [Documentation]    Click the person button from the home page.
    Click When Ready    ${PERSON_BUTTON}

Click Back Button
    [Documentation]    Click the back button from the home page.
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    [Documentation]    Click the notification button from the home page.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    [Documentation]    Click the home button from the home page.
    Click When Ready    ${HOME_BUTTON}

Click Customer Signup Button
    [Documentation]    Click the customer signup button from the home page.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Click the clean survey button from the home page.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Click the site survey button from the home page.
    Click When Ready    ${SITE_SURVEY_BUTTON}
