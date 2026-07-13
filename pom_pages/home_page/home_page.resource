*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_URL}    http://localhost/washtabui/login?data=undefined
${HOME_PAGE_URL_PATH}    /home
${AUTO_PERSON_BTN_BUTTON}    id=auto_person_btn
${AUTO_BACK_BTN_BUTTON}    id=auto_back_btn
${AUTO_NOTIFICATION_BTN_BUTTON}    id=auto_notification_btn
${AUTO_HOME_BTN_BUTTON}    id=auto_home_btn
${AUTO_BTN_CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${AUTO_BTN_CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${AUTO_BTN_SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey

*** Keywords ***
Open Home Page
    [Documentation]    Navigate directly to the home page URL.
    Go To Url    ${HOME_PAGE_URL}
    Wait For Element To Be Ready    ${AUTO_PERSON_BTN_BUTTON}

Wait Until Home Page Loads
    [Documentation]    Wait until the home page is fully loaded and primary controls are visible.
    Wait Until Location Contains    ${HOME_PAGE_URL_PATH}    ${DEFAULT_TIMEOUT}
    Wait For Element To Be Ready    ${AUTO_PERSON_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_BTN_CUSTOMER_SIGNUP_BUTTON}

Verify Home Page Loaded
    [Documentation]    Verify all approved home page controls are visible and ready for interaction.
    Wait Until Location Contains    ${HOME_PAGE_URL_PATH}    ${DEFAULT_TIMEOUT}
    Wait For Element To Be Ready    ${AUTO_PERSON_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_BACK_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_NOTIFICATION_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_HOME_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_BTN_CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${AUTO_BTN_CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${AUTO_BTN_SITE_SURVEY_BUTTON}

Verify Home Page Controls Visible
    [Documentation]    Verify all approved home page controls are visible and ready for interaction.
    Verify Home Page Loaded

Verify Home Page Is Displayed
    [Documentation]    Verify the home page is displayed with all primary controls visible.
    Verify Home Page Loaded

Verify Home Page Controls Are Enabled
    [Documentation]    Verify all approved home page controls are enabled for interaction.
    Wait Until Element Is Enabled    ${AUTO_PERSON_BTN_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_BACK_BTN_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_NOTIFICATION_BTN_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_HOME_BTN_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_BTN_CUSTOMER_SIGNUP_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_BTN_CLEAN_SURVEY_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Enabled    ${AUTO_BTN_SITE_SURVEY_BUTTON}    ${DEFAULT_TIMEOUT}

Verify Home Page Controls Are Interactable
    [Documentation]    Verify all approved home page controls are visible and enabled.
    Verify Home Page Loaded
    Verify Home Page Controls Are Enabled

Verify Notification Button Is Functional
    [Documentation]    Verify the notification button is visible and interactable.
    Wait For Element To Be Ready    ${AUTO_NOTIFICATION_BTN_BUTTON}

Verify User Is On Login Page
    [Documentation]    Verify the user is redirected to the login page.
    Wait Until Location Is    ${LOGIN_PAGE_URL}    ${DEFAULT_TIMEOUT}

Verify Home Page Still Visible
    [Documentation]    Verify the user remains on the home page with primary controls visible.
    Wait Until Location Contains    ${HOME_PAGE_URL_PATH}    ${DEFAULT_TIMEOUT}
    Wait For Element To Be Ready    ${AUTO_HOME_BTN_BUTTON}
    Wait For Element To Be Ready    ${AUTO_PERSON_BTN_BUTTON}

Click Auto Person Btn Button
    [Documentation]    Click the person navigation button from the home page.
    Click When Ready    ${AUTO_PERSON_BTN_BUTTON}

Click Auto Back Btn Button
    [Documentation]    Click the back navigation button from the home page.
    Click When Ready    ${AUTO_BACK_BTN_BUTTON}

Click Auto Notification Btn Button
    [Documentation]    Click the notification button from the home page.
    Click When Ready    ${AUTO_NOTIFICATION_BTN_BUTTON}

Click Auto Home Btn Button
    [Documentation]    Click the home navigation link from the home page.
    Click When Ready    ${AUTO_HOME_BTN_BUTTON}

Click Auto Btn Customer Signup Button
    [Documentation]    Click the customer signup button from the home page.
    Click When Ready    ${AUTO_BTN_CUSTOMER_SIGNUP_BUTTON}

Click Auto Btn Clean Survey Button
    [Documentation]    Click the clean survey button from the home page.
    Click When Ready    ${AUTO_BTN_CLEAN_SURVEY_BUTTON}

Click Auto Btn Site Survey Button
    [Documentation]    Click the site survey button from the home page.
    Click When Ready    ${AUTO_BTN_SITE_SURVEY_BUTTON}
