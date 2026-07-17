*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_TEXTBOX}    xpath=//input[@placeholder='User Name']
${PASSWORD_TEXTBOX}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[contains(normalize-space(.),'SIGN IN') or @text='Login']
${HOME_PAGE_URL}    http://localhost/washtabui/home
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    invalidpass
${INVALID_USERNAME_WITH_VALID_PASSWORD}    krisadmin1
${INVALID_PASSWORD_WITH_VALID_USERNAME}    Carwash#123
${USERNAME_UPPERCASE_VARIANT}    KRISADMIN
${PASSWORD_LOWERCASE_VARIANT}    carwash#1
${LOGIN_ERROR_TEXT}    invalid
${REQUIRED_FIELD_VALIDATION_TEXT}    required

*** Keywords ***
Enter Username Textbox
    [Documentation]    Enter text into the username textbox.
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Documentation]    Enter password into the password textbox.
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    [Documentation]    Click the sign in button.
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Login Form Loaded
    [Documentation]    Verify login form fields and sign in button are visible and enabled.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Password Field Is Masked
    [Documentation]    Verify the password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    ${password_type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${password_type}    password

Login With Credentials
    [Documentation]    Enter username and password credentials and submit the login form.
    [Arguments]    ${username}    ${password}
    Enter Username Textbox    ${username}
    Enter Password Textbox    ${password}
    Click Sign In Button

Login With Valid Credentials
    [Documentation]    Authenticate using approved valid credentials.
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}

Verify Login Page Remains Visible
    [Documentation]    Verify the login page remains visible after failed authentication or validation.
    Verify Login Form Loaded

Verify Authentication Error Message
    [Documentation]    Verify authentication error feedback is displayed.
    Page Should Contain    ${LOGIN_ERROR_TEXT}

Verify Required Validation
    [Documentation]    Verify required field validation feedback is displayed.
    Page Should Contain    ${REQUIRED_FIELD_VALIDATION_TEXT}

Generate Long Username Value
    [Documentation]    Generate a long username value for edge validation scenarios.
    ${long_username}=    Evaluate    "${VALID_USERNAME}" * 50
    [Return]    ${long_username}

Generate Long Password Value
    [Documentation]    Generate a long password value for edge validation scenarios.
    ${long_password}=    Evaluate    "${VALID_PASSWORD}" * 50
    [Return]    ${long_password}
