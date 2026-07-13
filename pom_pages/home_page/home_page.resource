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
${HOME_NAVIGATION_LINK}    id=auto_home_btn
${CUSTOMER_SIGNUP_BUTTON}    id=auto_btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=auto_btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=auto_btn_SiteSurvey
${BACKGROUND_CONTENT_ELEMENT}    id=background-content
${GENERIC_LINK_ELEMENT}    xpath=//a

*** Keywords ***
Open Home Page
    [Documentation]    Navigate to the Home page URL.
    Go To Url    ${HOME_PAGE_URL}
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}

Wait Until Home Page Loads
    [Documentation]    Wait until the home page is fully loaded and primary controls are visible.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}

Verify Home Page Loaded
    [Documentation]    Verify the Home page is loaded with all primary controls visible and enabled.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${BACK_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_NAVIGATION_LINK}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}
    Location Should Be    ${HOME_PAGE_URL}

Verify Home Page Is Displayed
    [Documentation]    Verify the home page is displayed with all primary controls visible.
    Verify Home Page Loaded

Verify All Home Navigation Controls Are Visible
    [Documentation]    Verify all approved Home page navigation controls are visible.
    Wait Until Element Is Visible    ${PERSON_NAVIGATION_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${BACK_NAVIGATION_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${NOTIFICATION_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${HOME_NAVIGATION_LINK}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${CUSTOMER_SIGNUP_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${CLEAN_SURVEY_BUTTON}    ${DEFAULT_TIMEOUT}
    Wait Until Element Is Visible    ${SITE_SURVEY_BUTTON}    ${DEFAULT_TIMEOUT}

Verify Home Page Controls Are Interactable
    [Documentation]    Verify all approved home page controls are visible and enabled.
    Wait For Element To Be Ready    ${PERSON_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${BACK_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_NAVIGATION_LINK}
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

Verify Notification Button Is Functional
    [Documentation]    Verify the notification button is visible and interactable.
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

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
    [Documentation]    Click the Home navigation link.
    Click When Ready    ${HOME_NAVIGATION_LINK}

Click Auto Btn Customer Signup Button
    [Documentation]    Click the Customer Signup button.
    Click When Ready    ${CUSTOMER_SIGNUP_BUTTON}

Click Auto Btn Clean Survey Button
    [Documentation]    Click the Clean Survey button.
    Click When Ready    ${CLEAN_SURVEY_BUTTON}

Click Auto Btn Site Survey Button
    [Documentation]    Click the Site Survey button.
    Click When Ready    ${SITE_SURVEY_BUTTON}

Click Background Content
    [Documentation]    Click a non-interactive background area on the Home page.
    Click When Ready    ${BACKGROUND_CONTENT_ELEMENT}

Click Generic Link
    [Documentation]    Click a generic link element on the page.
    Click When Ready    ${GENERIC_LINK_ELEMENT}
