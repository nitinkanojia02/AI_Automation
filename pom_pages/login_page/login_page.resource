*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_HOME_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL}    /washtabui/login?data=undefined
${USERNAME_FIELD}    xpath=//input[@placeholder='User Name']
${PASSWORD_FIELD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${AUTHENTICATION_FAILED_MESSAGE_LOCATOR}    text=Failed
${AUTHENTICATION_FAILED_MESSAGE}    Failed
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass123
${WRONG_USERNAME}    wronguser
${WRONG_PASSWORD}    WrongPassword1

*** Keywords ***
Enter Username
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_FIELD}    ${username}

Enter Password
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Verify Login Page Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Authentication Failed Message Displayed
    Wait Until Element Is Visible    ${AUTHENTICATION_FAILED_MESSAGE_LOCATOR}
    Element Text Should Be    ${AUTHENTICATION_FAILED_MESSAGE_LOCATOR}    ${AUTHENTICATION_FAILED_MESSAGE}

Verify Password Field Is Masked
    Wait Until Element Is Visible    ${PASSWORD_FIELD}
    Element Attribute Value Should Be    ${PASSWORD_FIELD}    type    password

Login With Credentials
    [Arguments]    ${username}    ${password}
    Enter Username    ${username}
    Enter Password    ${password}
    Click Login Button
