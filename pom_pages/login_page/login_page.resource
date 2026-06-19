*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    http://172.21.166.115/washtabui/login?data=undefined
${HOME_PAGE_URL}    http://172.21.166.115/washtabui/home
${LOGIN_PATH_FRAGMENT}    /washtabui/login
${HOME_PATH_FRAGMENT}    /washtabui/home
${VALID_USERNAME}    hacklarr
${VALID_PASSWORD}    Icstunnel1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    IncorrectPassword
${WRONG_USERNAME}    wronguser
${WRONG_PASSWORD}    wrongpassword
${USERNAME_TEXTBOX}    xpath=//input[@name='ion-input-0']
${PASSWORD_TEXTBOX}    id=password
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space()='SIGN IN']
${BACK_NAVIGATION_BUTTON}    xpath=//ion-fab-button[.//ion-icon[@aria-label='arrow back'] or normalize-space(.)='arrow back']
${HOME_NAVIGATION_BUTTON}    xpath=//ion-fab-button[.//ion-icon[@aria-label='home'] or normalize-space(.)='home']

*** Keywords ***
Verify Login Page Loaded
    [Documentation]    Verifies login page URL and that all required login controls are visible.
    Location Should Contain    ${LOGIN_PATH_FRAGMENT}
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}
    Wait For Element To Be Ready    ${BACK_NAVIGATION_BUTTON}
    Wait For Element To Be Ready    ${HOME_NAVIGATION_BUTTON}

Enter Username
    [Documentation]    Enter username into the username textbox.
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${username}

Enter Password
    [Documentation]    Enter password into the password textbox.
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Clear Element Text    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    [Documentation]    Click the SIGN IN button.
    Click When Ready    ${SIGN_IN_BUTTON}

Click Home Navigation Button
    [Documentation]    Click the home navigation button.
    Click When Ready    ${HOME_NAVIGATION_BUTTON}

Click Back Navigation Button
    [Documentation]    Click the back navigation button.
    Click When Ready    ${BACK_NAVIGATION_BUTTON}

Verify Successful Login Redirect
    [Documentation]    Verifies that successful authentication redirects to the home page.
    Wait Until Location Contains    ${HOME_PATH_FRAGMENT}    10s
    Location Should Contain    ${HOME_PATH_FRAGMENT}

Verify Login Rejected
    [Documentation]    Verifies authentication failure keeps the user on the login page.
    Location Should Contain    ${LOGIN_PATH_FRAGMENT}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Username Required Validation
    [Documentation]    Verifies login submission without username keeps the user on the login page.
    Location Should Contain    ${LOGIN_PATH_FRAGMENT}
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}

Verify Password Required Validation
    [Documentation]    Verifies login submission without password keeps the user on the login page.
    Location Should Contain    ${LOGIN_PATH_FRAGMENT}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}

Verify Password Field Is Masked
    [Documentation]    Verifies that the password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    ${type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${type}    password
