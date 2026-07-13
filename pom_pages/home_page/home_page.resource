*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL}    http://localhost/washtabui/login?data=undefined
${CUSTOMER_SEARCH_PAGE_PATH}    customer-search
${VEHICLE_SURVEY_PAGE_PATH}    vehicle-survey
${SURVEY_PAGE_PATH}    survey
${PERSON_NAVIGATION_BUTTON}    id=auto_person_btn
${BACK_NAVIGATION_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_NAVIGATION_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Navigate to the Home page URL and verify the page is loaded.
    Open Browser To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded

Wait Until Home Page Loads
    [Documentation]    Wait until the primary home page controls are ready for interaction.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}

Verify Home Page Loaded
    [Documentation]    Verify the Home page is loaded with all approved controls visible and enabled.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${BACK_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify All Home Navigation Controls Are Visible
    [Documentation]    Verify all approved Home page navigation controls are visible.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${BACK_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Login Page Navigation
    [Documentation]    Verify navigation to the login page after clicking the Person button.
    Wait Until Location Is    ${LOGIN_PAGE_URL}    ${DEFAULT_TIMEOUT}

Verify Customer Search Page Navigation
    [Documentation]    Verify navigation to the customer-search page.
    Wait Until Keyword Succeeds    ${DEFAULT_TIMEOUT}    1s    Location Should Contain    ${CUSTOMER_SEARCH_PAGE_PATH}

Verify Vehicle Survey Page Navigation
    [Documentation]    Verify navigation to the vehicle-survey page.
    Wait Until Keyword Succeeds    ${DEFAULT_TIMEOUT}    1s    Location Should Contain    ${VEHICLE_SURVEY_PAGE_PATH}

Verify Survey Page Navigation
    [Documentation]    Verify navigation to the survey page.
    Wait Until Keyword Succeeds    ${DEFAULT_TIMEOUT}    1s    Location Should Contain    ${SURVEY_PAGE_PATH}

Verify Notification Button Is Functional
    [Documentation]    Verify the Notification button remains interactable after user interaction.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

Click Auto Person Btn Button
    [Documentation]    Click the Person navigation button.
    Click When Ready    ${PERSON_NAVIGATION_BUTTON}

Click Auto Back Btn Button
    [Documentation]    Click the Back navigation button.
    Click When Ready    ${BACK_NAVIGATION_BUTTON}

Click Auto Notification Btn Button
    [Documentation]    Click the Notification button.
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Auto Home Btn Button
    [Documentation]    Click the Home navigation button.
    Click When Ready    ${HOME_NAVIGATION_BUTTON}

Click Auto Btn Customer Signup Button
    [Documentation]    Click the Customer Signup button.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Auto Btn Clean Survey Button
    [Documentation]    Click the Clean Survey button.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Auto Btn Site Survey Button
    [Documentation]    Click the Site Survey button.
    Click When Ready    ${SITE_SURVEY_BUTTON}
