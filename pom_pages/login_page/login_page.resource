*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_TEXTBOX}    xpath=//input[@placeholder='User Name']
${PASSWORD_TEXTBOX}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[contains(.,'SIGN IN') or @text='Login']
${HOME_PAGE_URL}    http://localhost/washtabui/home
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass123
${WRONG_PASSWORD}    wrongpassword
${SPECIAL_CHARACTER_USERNAME}    krisadmin@@@
${AUTHENTICATION_ERROR_TEXT}    invalid
${REQUIRED_FIELD_VALIDATION_TEXT}    required

*** Keywords ***
Enter Username Textbox
    [Documentation]    Enter text into the username field.
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Documentation]    Enter password into the password field.
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    [Documentation]    Click the sign in button.
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Login Form Loaded
    [Documentation]    Verify username field, password field, and sign in button are visible and enabled.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Username Textbox
    [Documentation]    Verify username field retains the entered value.
    [Arguments]    ${expected_username}
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    ${actual_username}=    Get Value    ${USERNAME_TEXTBOX}
    Should Be Equal    ${actual_username}    ${expected_username}

Verify Password Textbox
    [Documentation]    Verify password field masks entered values.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Element Attribute Value Should Be    ${PASSWORD_TEXTBOX}    type    password

Login With Valid Credentials
    [Documentation]    Login using approved valid credentials.
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button

Login With Invalid Credentials
    [Documentation]    Login using invalid credentials.
    Enter Username Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button

Login With Invalid Username
    [Documentation]    Attempt login using invalid username and valid password.
    Enter Username Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button

Login With Invalid Password
    [Documentation]    Attempt login using valid username and invalid password.
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button

Verify Login Failed And User Remains On Login Page
    [Documentation]    Verify failed login keeps the user on the login page with login controls visible.
    Verify Login Form Loaded

Verify Authentication Error Message
    [Documentation]    Verify authentication error feedback is displayed.
    Page Should Contain    ${AUTHENTICATION_ERROR_TEXT}

Verify Required Field Validation
    [Documentation]    Verify required field validation feedback is displayed.
    Page Should Contain    ${REQUIRED_FIELD_VALIDATION_TEXT}
