*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_HOME_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL_FRAGMENT}    /washtabui/login?data=undefined
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPassword1
${INVALID_PASSWORD_FOR_VALID_USER}    Carwash#999
${UPPERCASE_USERNAME}    KRISADMIN
${UPPERCASE_PASSWORD}    CARWASH#1
${FAILED_AUTHENTICATION_MESSAGE}    Failed
${LONG_USERNAME_VALUE}    krisadminkrisadminkrisadminkrisadminkrisadminkrisadminkrisadmin
${LONG_PASSWORD_VALUE}    Carwash#1Carwash#1Carwash#1Carwash#1Carwash#1Carwash#1
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${USERNAME_FIELD}    xpath=//input[@placeholder='User Name']
${PASSWORD_FIELD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[normalize-space(.)='Login']
${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}    text=Failed
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn

*** Keywords ***
Click Person Profile Button
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    Click When Ready    ${BACK_BUTTON}

Click Notification Button
    Click When Ready    ${NOTIFICATION_BUTTON}

Click Home Button
    Click When Ready    ${HOME_BUTTON}

Enter Username
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_FIELD}    ${username}

Enter Password
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Perform Login
    [Arguments]    ${username}    ${password}
    Enter Username    ${username}
    Enter Password    ${password}
    Click Login Button

Verify Login Page Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Login Page Controls Visible And Enabled
    Verify Login Page Loaded

Verify Username Field Visible And Enabled
    Wait For Element To Be Ready    ${USERNAME_FIELD}

Verify Password Field Visible And Enabled
    Wait For Element To Be Ready    ${PASSWORD_FIELD}

Verify Login Button Visible And Enabled
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Verify Failed Authentication Message Displayed
    Wait Until Element Is Visible    ${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}
    Element Text Should Be    ${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}    ${FAILED_AUTHENTICATION_MESSAGE}

Verify Login Page Remains Unauthenticated
    Verify Failed Authentication Message Displayed
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Verify Password Field Is Masked
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Element Attribute Value Should Be    ${PASSWORD_FIELD}    type    password
