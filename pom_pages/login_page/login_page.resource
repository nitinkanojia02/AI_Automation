*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
${DASHBOARD_URL}    https://opensource-demo.orangehrmlive.com/web/index.php/dashboard/index
${LOGIN_PAGE_TITLE_TEXT}    Login
${INVALID_CREDENTIALS_MESSAGE}    Invalid credentials
${REQUIRED_FIELD_MESSAGE}    Required
${VALID_USERNAME}    Admin
${VALID_PASSWORD}    admin123
${INVALID_USERNAME}    InvalidAdmin
${INVALID_PASSWORD}    wrongPassword123
${INVALID_USERNAME_ALT}    WrongUser
${INVALID_PASSWORD_ALT}    WrongPassword
${LOWERCASE_USERNAME}    admin
${MIXED_CASE_PASSWORD}    Admin123
${SPECIAL_CHARACTER_USERNAME}    @@@###$$$
${LOGIN_PAGE_TITLE}    xpath=//h5[normalize-space()='Login']
${USERNAME_TEXTBOX}    xpath=//input[@name='username']
${PASSWORD_TEXTBOX}    xpath=//input[@name='password']
${LOGIN_BUTTON}    xpath=//button[@type='submit']
${FORGOT_PASSWORD_LINK}    xpath=//p[normalize-space()='Forgot your password?']
${LOGIN_ERROR_MESSAGE}    xpath=//p[normalize-space()='Invalid credentials']

*** Keywords ***
Open Login Page
    [Documentation]    Navigate to the OrangeHRM login page.
    Go To    ${LOGIN_PAGE_URL}
    Wait Until Element Is Visible    ${LOGIN_PAGE_TITLE}    10s

Enter Username
    [Documentation]    Enter username into username textbox.
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${USERNAME_TEXTBOX}    10s
    Clear Element Text    ${USERNAME_TEXTBOX}
    Input Text    ${USERNAME_TEXTBOX}    ${text}

Enter Password
    [Documentation]    Enter password into password textbox.
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Clear Element Text    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Login Button
    [Documentation]    Click the Login button.
    Wait Until Element Is Visible    ${LOGIN_BUTTON}    10s
    Click Element    ${LOGIN_BUTTON}

Click Forgot Password Link
    [Documentation]    Click the Forgot your password link.
    Wait Until Element Is Visible    ${FORGOT_PASSWORD_LINK}    10s
    Click Element    ${FORGOT_PASSWORD_LINK}

Login With Credentials
    [Documentation]    Perform login using provided username and password.
    [Arguments]    ${username}    ${password}
    Enter Username    ${username}
    Enter Password    ${password}
    Click Login Button

Login With Valid Credentials
    [Documentation]    Perform login using valid application credentials.
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}

Submit Login Using Enter Key
    [Documentation]    Submit login form using Enter key from password textbox.
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER

Verify Login Page Is Displayed
    [Documentation]    Verify login page title and controls are visible.
    Wait Until Location Contains    /auth/login    10s
    Element Text Should Be    ${LOGIN_PAGE_TITLE}    ${LOGIN_PAGE_TITLE_TEXT}
    Element Should Be Visible    ${USERNAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${LOGIN_BUTTON}
    Element Should Be Visible    ${FORGOT_PASSWORD_LINK}

Verify Login Button Is Enabled
    [Documentation]    Verify Login button is enabled for interaction.
    Element Should Be Enabled    ${LOGIN_BUTTON}

Verify Successful Login
    [Documentation]    Verify successful authentication redirects user to dashboard page.
    Wait Until Location Contains    /dashboard/index    10s
    Location Should Be    ${DASHBOARD_URL}

Verify Invalid Credentials Message
    [Documentation]    Verify invalid credentials error message is displayed.
    Wait Until Element Is Visible    ${LOGIN_ERROR_MESSAGE}    10s
    Element Text Should Be    ${LOGIN_ERROR_MESSAGE}    ${INVALID_CREDENTIALS_MESSAGE}

Verify Required Field Message
    [Documentation]    Verify required field validation message is displayed.
    Wait Until Page Contains    ${REQUIRED_FIELD_MESSAGE}    10s
    Page Should Contain    ${REQUIRED_FIELD_MESSAGE}

Verify User Remains On Login Page
    [Documentation]    Verify failed authentication keeps the user on login page.
    Wait Until Location Contains    /auth/login    10s
    Element Should Be Visible    ${LOGIN_BUTTON}
    Element Should Be Visible    ${USERNAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}

Verify Password Field Is Masked
    [Documentation]    Verify password textbox masks entered characters.
    ${type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${type}    password

Verify Forgot Password Navigation
    [Documentation]    Verify forgot password navigation succeeds.
    Wait Until Page Does Not Contain Element    ${LOGIN_BUTTON}    10s
    Location Should Not Contain    /auth/login
