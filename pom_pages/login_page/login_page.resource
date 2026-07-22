*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/login?data=undefined
${HOME_PAGE_URL}    http://localhost/washtabui/home
${USERNAME_FIELD}    xpath=//input[@placeholder='User Name']
${PASSWORD_FIELD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${AUTHENTICATION_FAILED_MESSAGE}    text=Failed
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    WrongPassword1
${ALTERNATE_INVALID_USERNAME}    wronguser
${UPPERCASE_USERNAME}    KRISADMIN
${UPPERCASE_PASSWORD}    CARWASH#1
${GENERIC_FAILED_MESSAGE}    Failed

*** Keywords ***
Enter Username
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_FIELD}    ${text}

Enter Password
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Click Back Button
    Click When Ready    ${BACK_BUTTON}

Click Home Button
    Click When Ready    ${HOME_BUTTON}

Verify Login Form Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Password Is Masked
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Element Attribute Value Should Be    ${PASSWORD_FIELD}    type    password

Verify Authentication Failed Message
    Wait For Element To Be Ready    ${AUTHENTICATION_FAILED_MESSAGE}
