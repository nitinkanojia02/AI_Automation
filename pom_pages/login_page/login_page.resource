*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    http://localhost/washtabui/home
${USER_NAME_TEXTBOX}    id=ion-input-0
${PASSWORD_TEXTBOX}    id=ion-input-1
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${GENERIC_FAILED_MESSAGE}    xpath=//*[contains(normalize-space(.),'Failed')]
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPassword#1
${WRONG_PASSWORD}    WrongPassword#1
${LOWERCASE_PASSWORD_VARIANT}    carwash#1
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

Background Content
    Click When Ready    body

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
    Element Attribute Value Should Be    ${PASSWORD_TEXTBOX}    type    password

Verify Back Button
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Generic Failed Message
    Wait For Element To Be Ready    ${GENERIC_FAILED_MESSAGE}

Verify Login Page Remains Accessible
    Verify Login Form Loaded
    Verify Generic Failed Message
