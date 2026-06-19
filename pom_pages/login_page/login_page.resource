*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_FIELD}    xpath=//input[@aria-labelledby='ion-input-0-lbl']
${PASSWORD_FIELD}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${BACK_BUTTON}    xpath=(//ion-fab-button)[1]
${HOME_BUTTON}    xpath=(//ion-fab-button)[last()]

*** Keywords ***
Verify On Login Page
    [Documentation]    Verifies that the browser is currently on the login page URL.
    ${current_url}=    Get Location
    Should Contain    ${current_url}    /login

Verify Login Page Loaded
    [Documentation]    Verifies that the core login page controls are visible and ready for interaction.
    Verify On Login Page
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Login Navigation Controls Visible
    [Documentation]    Verifies that the Home and Arrow Back navigation controls are visible on the login page.
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}

Enter Username
    [Documentation]    Enter the provided username into the User Name field.
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_FIELD}    ${username}

Enter Password
    [Documentation]    Enter the provided password into the Password field.
    [Arguments]    ${password}
    Input Text When Ready    ${PASSWORD_FIELD}    ${password}

Click Sign In Button
    [Documentation]    Submits the login form using the Sign In button.
    Click When Ready    ${SIGN_IN_BUTTON}

Attempt Login With Credentials
    [Documentation]    Attempts login using the provided credentials without asserting outcome.
    [Arguments]    ${username}    ${password}
    Verify Login Page Loaded
    Enter Username    ${username}
    Enter Password    ${password}
    Click Sign In Button

Login With Credentials
    [Documentation]    Performs login using provided credentials expecting successful authentication.
    [Arguments]    ${username}    ${password}
    Attempt Login With Credentials    ${username}    ${password}

Verify Login Rejected
    [Documentation]    Verifies that login was rejected and the user remains on the login page.
    Verify On Login Page
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Username Required Validation
    [Documentation]    Verifies that username is required by confirming the login page remains visible after submission without a username.
    Verify On Login Page
    Wait For Element To Be Ready    ${USERNAME_FIELD}

Verify Password Required Validation
    [Documentation]    Verifies that password is required by confirming the login page remains visible after submission without a password.
    Verify On Login Page
    Wait For Element To Be Ready    ${PASSWORD_FIELD}

Click Home Button
    [Documentation]    Navigates to the home page using the Home navigation button.
    Click When Ready    ${HOME_BUTTON}

Click Arrow Back Button
    [Documentation]    Navigates using the Arrow Back navigation button.
    Click When Ready    ${BACK_BUTTON}