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
${INVALID_PASSWORD}    InvalidPassword1!
${UPPERCASE_USERNAME}    KRISADMIN
${SPECIAL_CHARACTER_USERNAME}    !@#$%^&*
${SPECIAL_CHARACTER_PASSWORD}    <>?:{}|+_

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
    [Documentation]    Verify the Username field, Password field, and Sign In button are visible and enabled on the Login page.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Navigation Buttons Loaded
    [Documentation]    Verify the Back button and Home button are visible and enabled on the Login page.
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Password Field Is Masked
    [Documentation]    Verify the Password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    ${password_type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${password_type}    password

Verify Authentication Failed Message Displayed
    [Documentation]    Verify the generic Failed authentication message is displayed.
    Wait For Element To Be Ready    ${AUTHENTICATION_FAILED_MESSAGE}

Verify Login Page Still Visible
    [Documentation]    Verify the Login page remains visible and interactive after failed authentication.
    Verify Login Form Loaded

Login With Credentials
    [Documentation]    Perform login using provided credentials.
    [Arguments]    ${username}    ${password}
    Enter Username Textbox    ${username}
    Enter Password Textbox    ${password}
    Click Sign In Button

Login With Valid Credentials
    [Documentation]    Perform login using approved valid credentials.
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}

Login With Invalid Credentials
    [Documentation]    Perform login using approved invalid credentials.
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
