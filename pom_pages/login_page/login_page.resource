*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    http://localhost/washtabui/home
${USER_NAME_TEXTBOX}    id=ion-input-0
${PASSWORD_TEXTBOX}    id=ion-input-1
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${GENERIC_FAILED_AUTHENTICATION_MESSAGE}    xpath=//*[contains(normalize-space(.),'Failed')]
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass#1
${UPPERCASE_INVALID_USERNAME}    KRISADMIN
${LOWERCASE_INVALID_PASSWORD}    carwash#1
${SPECIAL_CHARACTER_USERNAME}    !@#$%^&*()
${SPECIAL_CHARACTER_PASSWORD}    <>?:{}|+=_-
${LONG_USERNAME}    krisadminkrisadminkrisadminkrisadminkrisadminkrisadminkrisadminkrisadmin
${LONG_PASSWORD}    Carwash#1Carwash#1Carwash#1Carwash#1Carwash#1Carwash#1
${GENERIC_FAILED_MESSAGE_TEXT}    Failed

*** Keywords ***
Enter User Name Textbox
    [Arguments]    ${text}
    Input Text When Ready    ${USER_NAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Login Form Loaded
    Verify User Name Textbox
    Verify Password Textbox
    Verify Back Button

Verify User Name Textbox
    Wait For Element To Be Ready    ${USER_NAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Password Textbox
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}

Verify Back Button
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Generic Failed Authentication Message
    Wait For Element To Be Ready    ${GENERIC_FAILED_AUTHENTICATION_MESSAGE}

Verify Login Rejected
    Verify Login Form Loaded
    Verify Generic Failed Authentication Message
