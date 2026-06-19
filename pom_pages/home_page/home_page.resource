*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_BUTTON}    xpath=//ion-fab-button[.//ion-icon[@aria-label='home'] or normalize-space(.)='home']
${NOTIFICATIONS_BUTTON}    id=notifications-button
${CUSTOMER_SIGNUP_BUTTON}    id=btn_CustomerSignup
${CLEAN_SURVEY_BUTTON}    id=btn_CleanSurvey
${SITE_SURVEY_BUTTON}    id=btn_SiteSurvey
${CLOSE_LINK}    xpath=//a[normalize-space(.)='close']

*** Keywords ***
Click Home Button
    [Documentation]    Click action for Home Button (button) using page object locator.
    Wait Until Element Is Visible    ${HOME_BUTTON}    10s
    Click Element    ${HOME_BUTTON}

Click Notifications Button
    [Documentation]    Click action for Notifications Button (button) using page object locator.
    Wait Until Element Is Visible    ${NOTIFICATIONS_BUTTON}    10s
    Click Element    ${NOTIFICATIONS_BUTTON}

Click Customer Signup Button
    [Documentation]    Click action for Customer Signup Button (button) using page object locator.
    Wait Until Element Is Visible    ${CUSTOMER_SIGNUP_BUTTON}    10s
    Click Element    ${CUSTOMER_SIGNUP_BUTTON}

Click Clean Survey Button
    [Documentation]    Click action for Clean Survey Button (button) using page object locator.
    Wait Until Element Is Visible    ${CLEAN_SURVEY_BUTTON}    10s
    Click Element    ${CLEAN_SURVEY_BUTTON}

Click Site Survey Button
    [Documentation]    Click action for Site Survey Button (button) using page object locator.
    Wait Until Element Is Visible    ${SITE_SURVEY_BUTTON}    10s
    Click Element    ${SITE_SURVEY_BUTTON}

Click Close
    [Documentation]    Click action for Close (link) using page object locator.
    Wait Until Element Is Visible    ${CLOSE_LINK}    10s
    Click Element    ${CLOSE_LINK}
