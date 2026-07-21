*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL}    /washtabui/login?data=undefined
${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}    /customer-search
${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}    vehicle-survey
${EXPECTED_SITE_SURVEY_URL_FRAGMENT}    survey?data
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${BACK_BUTTON}    id=auto_back_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn
${HOME_BUTTON}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Open the Home page using the approved guest-state entry URL.
    Open Browser To Url    ${PAGE_URL}
    Verify Home Page Loaded In Guest State

Verify Home Page Loaded In Guest State
    [Documentation]    Verify the Home page is loaded in guest state and all approved navigation controls are ready for interaction.
    Wait Until Location Contains    ${PAGE_URL}
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify All Home Navigation Buttons Are Enabled
    [Documentation]    Verify all approved Home page navigation buttons are enabled and interactive.
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Navigation To Login Page
    [Documentation]    Verify navigation to the login page URL.
    Wait Until Location Contains    ${EXPECTED_LOGIN_URL}

Verify Navigation To Customer Search Page
    [Documentation]    Verify navigation to the customer-search workflow URL.
    Wait Until Location Contains    ${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}

Verify Navigation To Vehicle Survey Page
    [Documentation]    Verify navigation to the vehicle-survey workflow URL.
    Wait Until Location Contains    ${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}

Verify Navigation To Site Survey Page
    [Documentation]    Verify navigation to the survey workflow URL.
    Wait Until Location Contains    ${EXPECTED_SITE_SURVEY_URL_FRAGMENT}

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
