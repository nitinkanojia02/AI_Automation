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
${INVALID_PASSWORD}    WrongPass#1
${CASE_SENSITIVE_INVALID_USERNAME}    KRISADMIN
${CASE_SENSITIVE_INVALID_PASSWORD}    CARWASH#1
${AUTHENTICATION_FAILED_TEXT}    Failed
${LONG_INPUT_MULTIPLIER}    50

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
    [Documentation]    Verify Login page controls are visible and enabled.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Password Field Is Masked
    [Documentation]    Verify the Password field uses masked input behavior.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Element Attribute Value Should Be    ${PASSWORD_TEXTBOX}    type    password

Verify Authentication Failed Message
    [Documentation]    Verify the generic Failed authentication message is displayed.
    Wait For Element To Be Ready    ${AUTHENTICATION_FAILED_MESSAGE}

Verify Login Page Remains Visible
    [Documentation]    Verify the application remains on the Login page in unauthenticated state.
    Verify Login Form Loaded

Login With Credentials
    [Documentation]    Enter username and password credentials and submit the login form.
    [Arguments]    ${username}    ${password}
    Enter Username Textbox    ${username}
    Enter Password Textbox    ${password}
    Click Sign In Button

Login With Valid Credentials
    [Documentation]    Authenticate using approved valid credentials.
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}

Login With Invalid Credentials
    [Documentation]    Attempt login using invalid username and invalid password.
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}

Login With Case Sensitive Invalid Credentials
    [Documentation]    Attempt login using uppercase credential variants to validate case sensitivity.
    Login With Credentials    ${CASE_SENSITIVE_INVALID_USERNAME}    ${CASE_SENSITIVE_INVALID_PASSWORD}

Generate Long Username Value
    [Documentation]    Generate a long username value for edge validation scenarios.
    ${long_username}=    Evaluate    "${VALID_USERNAME}" * ${LONG_INPUT_MULTIPLIER}
    [Return]    ${long_username}

Generate Long Password Value
    [Documentation]    Generate a long password value for edge validation scenarios.
    ${long_password}=    Evaluate    "${VALID_PASSWORD}" * ${LONG_INPUT_MULTIPLIER}
    [Return]    ${long_password}
