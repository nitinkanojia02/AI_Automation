*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_TEXTBOX}    xpath=//input[@placeholder='User Name']
${PASSWORD_TEXTBOX}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[contains(normalize-space(.),'SIGN IN') or @text='Login']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${AUTHENTICATION_FAILED_MESSAGE}    xpath=//*[contains(normalize-space(.),'Failed')]
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass#1
${INVALID_PASSWORD_FOR_VALID_USER}    WrongPassword#1
${CASE_SENSITIVE_USERNAME}    KRISADMIN
${CASE_SENSITIVE_PASSWORD}    CARWASH#1
${GENERIC_AUTH_FAILED_MESSAGE_TEXT}    Failed

*** Keywords ***
Enter Username Textbox
    [Documentation]    Enter text into the Username field.
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Documentation]    Enter password into the Password field.
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    [Documentation]    Click the Sign In button.
    Click When Ready    ${SIGN_IN_BUTTON}

Click Back Button
    [Documentation]    Click the Back button on the Login page.
    Click When Ready    ${BACK_BUTTON}

Click Home Button
    [Documentation]    Click the Home button on the Login page.
    Click When Ready    ${HOME_BUTTON}

Verify Login Form Loaded
    [Documentation]    Verify login form controls are visible and enabled.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Navigation Buttons Loaded
    [Documentation]    Verify back and home navigation buttons are visible and enabled.
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Password Field Is Masked
    [Documentation]    Verify the password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    ${password_field_type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${password_field_type}    password

Verify Authentication Failed Message Displayed
    [Documentation]    Verify the generic failed authentication message is displayed.
    Wait For Element To Be Ready    ${AUTHENTICATION_FAILED_MESSAGE}

Verify Login Page Still Visible
    [Documentation]    Verify the login page remains visible after failed authentication.
    Verify Login Form Loaded

Login With Credentials
    [Documentation]    Perform login using provided credentials.
    [Arguments]    ${username}    ${password}
    Enter Username Textbox    ${username}
    Enter Password Textbox    ${password}
    Click Sign In Button
