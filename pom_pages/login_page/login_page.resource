*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_FIELD}    id=ion-input-0
${PASSWORD_FIELD}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${VALID_USERNAME}    valid.user
${VALID_PASSWORD}    ValidPassword123!
${INVALID_USERNAME}    invalid.user
${INVALID_PASSWORD}    InvalidPassword123!
${EXPECTED_AUTHENTICATION_ERROR_TEXT}    invalid
${EXPECTED_REQUIRED_FIELD_TEXT}    required

*** Keywords ***
Enter Username Textbox
    [Documentation]    Enter text into the username textbox.
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_FIELD}    ${text}

Enter Password Textbox
    [Documentation]    Enter password into the password textbox.
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Input Password    ${PASSWORD_FIELD}    ${password}

Click Sign In Button
    [Documentation]    Click the sign in button.
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Username Textbox
    [Documentation]    Verify the username textbox is visible and enabled.
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Element Should Be Enabled    ${USERNAME_FIELD}

Verify Password Textbox
    [Documentation]    Verify the password textbox is visible and enabled.
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Element Should Be Enabled    ${PASSWORD_FIELD}

Verify Sign In Button
    [Documentation]    Verify the sign in button is visible and enabled.
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}
    Element Should Be Enabled    ${SIGN_IN_BUTTON}

Verify Login Page Loaded
    [Documentation]    Verify login page controls are displayed and interactive.
    Verify Username Textbox
    Verify Password Textbox
    Verify Sign In Button

Verify Password Field Is Masked
    [Documentation]    Verify the password field masks entered values.
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    ${password_type}=    Get Element Attribute    ${PASSWORD_FIELD}    type
    Should Be Equal As Strings    ${password_type}    password

Enter Valid Username
    [Documentation]    Enter reusable valid username credential.
    Enter Username Textbox    ${VALID_USERNAME}

Enter Valid Password
    [Documentation]    Enter reusable valid password credential.
    Enter Password Textbox    ${VALID_PASSWORD}

Enter Invalid Username
    [Documentation]    Enter reusable invalid username credential.
    Enter Username Textbox    ${INVALID_USERNAME}

Enter Invalid Password
    [Documentation]    Enter reusable invalid password credential.
    Enter Password Textbox    ${INVALID_PASSWORD}

Login With Credentials
    [Documentation]    Login using supplied username and password values.
    [Arguments]    ${username}    ${password}
    Enter Username Textbox    ${username}
    Enter Password Textbox    ${password}
    Click Sign In Button

Login With Valid Credentials
    [Documentation]    Perform login using reusable valid credentials.
    Enter Valid Username
    Enter Valid Password
    Click Sign In Button

Login With Invalid Credentials
    [Documentation]    Perform login using reusable invalid credentials.
    Enter Invalid Username
    Enter Invalid Password
    Click Sign In Button

Submit Login Form With Keyboard Enter
    [Documentation]    Submit the login form using keyboard Enter key from the password field.
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Press Keys    ${PASSWORD_FIELD}    ENTER

Verify Authentication Error Message
    [Documentation]    Verify authentication failure feedback is displayed and the login page remains available.
    Page Should Contain    ${EXPECTED_AUTHENTICATION_ERROR_TEXT}
    Verify Login Page Loaded

Verify Required Field Validation
    [Documentation]    Verify required-field validation feedback is displayed.
    Page Should Contain    ${EXPECTED_REQUIRED_FIELD_TEXT}
    Verify Login Page Loaded

Verify Login Successful
    [Documentation]    Verify successful authentication removed the login form.
    Page Should Not Contain Element    ${SIGN_IN_BUTTON}

Verify Username Field Editable
    [Documentation]    Verify the username field remains editable.
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Element Should Be Enabled    ${USERNAME_FIELD}

Verify Password Field Editable
    [Documentation]    Verify the password field remains editable.
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Element Should Be Enabled    ${PASSWORD_FIELD}
