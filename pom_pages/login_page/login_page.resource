*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}              http://172.21.166.115/washtabui/login?data=undefined
${HOME_PAGE_URL}               http://172.21.166.115/washtabui/home
${VALID_USERNAME}              hacklarr
${VALID_PASSWORD}              Icstunnel1
${INVALID_USERNAME}            invaliduser
${INVALID_PASSWORD}            WrongPassword123
${ALT_INVALID_USERNAME}        wronguser
${ALT_INVALID_PASSWORD}        wrongpass
${SPECIAL_CHAR_USERNAME}       user!@#
${USERNAME_TEXTBOX}            xpath=//input[@name='ion-input-0']
${PASSWORD_TEXTBOX}            id=password
${SIGN_IN_BUTTON}              xpath=//ion-button[normalize-space()='SIGN IN']
${HOME_NAVIGATION_BUTTON}      xpath=//ion-fab-button[.//ion-icon[@aria-label='home']]
${BACK_NAVIGATION_BUTTON}      xpath=//ion-fab-button[.//ion-icon[@aria-label='arrow back']]

*** Keywords ***
Verify Login Page Loaded
    [Documentation]    Verify login page loads and required UI elements are visible.
    Wait Until Location Is    ${LOGIN_PAGE_URL}    10s
    Wait Until Element Is Visible    ${USERNAME_TEXTBOX}    10s
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${SIGN_IN_BUTTON}
    Element Should Be Visible    ${HOME_NAVIGATION_BUTTON}
    Element Should Be Visible    ${BACK_NAVIGATION_BUTTON}

Enter Username
    [Documentation]    Enter username into username textbox.
    [Arguments]    ${username}
    Wait Until Element Is Visible    ${USERNAME_TEXTBOX}    10s
    Input Text    ${USERNAME_TEXTBOX}    ${username}

Enter Password
    [Documentation]    Enter password into password textbox.
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Clear Element Text    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    [Documentation]    Click the SIGN IN button.
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Click Element    ${SIGN_IN_BUTTON}

Click Home Navigation Button
    [Documentation]    Click the home navigation button.
    Wait Until Element Is Visible    ${HOME_NAVIGATION_BUTTON}    10s
    Click Element    ${HOME_NAVIGATION_BUTTON}

Click Back Navigation Button
    [Documentation]    Click the back navigation button.
    Wait Until Element Is Visible    ${BACK_NAVIGATION_BUTTON}    10s
    Click Element    ${BACK_NAVIGATION_BUTTON}

Verify Successful Login Redirect
    [Documentation]    Verify successful authentication redirects the user to the home page.
    Wait Until Location Is    ${HOME_PAGE_URL}    10s

Verify Login Rejected
    [Documentation]    Verify authentication failure keeps the user on the login page.
    Wait Until Location Is    ${LOGIN_PAGE_URL}    10s
    Element Should Be Visible    ${SIGN_IN_BUTTON}

Verify Password Field Is Masked
    [Documentation]    Verify password textbox masks entered characters.
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    ${type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${type}    password
