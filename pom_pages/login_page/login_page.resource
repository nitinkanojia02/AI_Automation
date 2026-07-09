*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    https://opensource-demo.orangehrmlive.com/web/index.php/auth/login
${DASHBOARD_PAGE_URL}    https://opensource-demo.orangehrmlive.com/web/index.php/dashboard/index
${LOGIN_PAGE_TITLE_TEXT}    Login
${INVALID_CREDENTIALS_MESSAGE_TEXT}    Invalid credentials
${REQUIRED_FIELD_MESSAGE_TEXT}    Required
${FORGOT_PASSWORD_TEXT}    Forgot your password?
${VALID_USERNAME}    Admin
${VALID_PASSWORD}    admin123
${INVALID_USERNAME}    InvalidAdmin
${INVALID_PASSWORD}    wrongPassword123
${INVALID_USERNAME_AND_PASSWORD_USERNAME}    wrongUser
${INVALID_USERNAME_AND_PASSWORD_PASSWORD}    wrongPassword
${LOWERCASE_USERNAME}    admin
${UPPERCASE_PASSWORD}    ADMIN123
${SPECIAL_CHARACTER_USERNAME}    @@@###
${SPECIAL_CHARACTER_PASSWORD}    @@@###$$$
${LOGIN_PAGE_TITLE}    xpath=//h5[normalize-space()='Login']
${USERNAME_TEXTBOX}    xpath=//input[@name='username']
${PASSWORD_TEXTBOX}    xpath=//input[@name='password']
${LOGIN_BUTTON}    xpath=//button[@type='submit']
${FORGOT_PASSWORD_LINK}    xpath=//p[normalize-space()='Forgot your password?']
${INVALID_CREDENTIALS_MESSAGE}    xpath=//p[normalize-space()='Invalid credentials']
${REQUIRED_FIELD_MESSAGE}    xpath=//span[normalize-space()='Required']
${ORANGE_HRM_INC_LINK}    xpath=//a[normalize-space(.)='OrangeHRM, Inc']
${APP_ELEMENT}    id=app

*** Keywords ***
Open Login Page
    [Documentation]    Navigate to OrangeHRM login page and wait for login form.
    Go To Url    ${LOGIN_PAGE_URL}
    Wait For Element To Be Ready    ${LOGIN_PAGE_TITLE}

Enter Username
    [Documentation]    Enter text into username textbox.
    [Arguments]    ${text}
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Clear Element Text    ${USERNAME_TEXTBOX}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${text}

Enter Password
    [Documentation]    Enter password into password textbox.
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Clear Element Text    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Login Button
    [Documentation]    Click Login button on login page.
    Click When Ready    ${LOGIN_BUTTON}

Click Forgot Your Password
    [Documentation]    Click Forgot your password link.
    Click When Ready    ${FORGOT_PASSWORD_LINK}

Login With Valid Credentials
    [Documentation]    Perform login using valid credentials.
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button

Submit Login Form Using Enter Key
    [Documentation]    Submit login form using Enter key from password textbox.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER

Verify Login Page Is Displayed
    [Documentation]    Verify login page and all primary login controls are visible.
    Wait Until Location Contains    /auth/login    ${DEFAULT_TIMEOUT}
    Wait For Element To Be Ready    ${LOGIN_PAGE_TITLE}
    Element Text Should Be    ${LOGIN_PAGE_TITLE}    ${LOGIN_PAGE_TITLE_TEXT}
    Element Should Be Visible    ${USERNAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${LOGIN_BUTTON}
    Element Should Be Visible    ${FORGOT_PASSWORD_LINK}

Verify Successful Login
    [Documentation]    Verify successful login redirects user to dashboard page.
    Wait Until Location Contains    /dashboard/index    ${DEFAULT_TIMEOUT}
    Location Should Be    ${DASHBOARD_PAGE_URL}
    Element Should Be Visible    ${APP_ELEMENT}

Verify User Remains On Login Page
    [Documentation]    Verify application remains on login page after failed authentication.
    Wait Until Location Contains    /auth/login    ${DEFAULT_TIMEOUT}
    Element Should Be Visible    ${LOGIN_BUTTON}
    Element Should Be Visible    ${USERNAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}

Verify Invalid Credentials Message
    [Documentation]    Verify invalid credentials message is displayed.
    Wait For Element To Be Ready    ${INVALID_CREDENTIALS_MESSAGE}
    Element Text Should Be    ${INVALID_CREDENTIALS_MESSAGE}    ${INVALID_CREDENTIALS_MESSAGE_TEXT}

Verify Invalid Credentials Message Is Cleared
    [Documentation]    Verify invalid credentials message is no longer visible.
    Element Should Not Be Visible    ${INVALID_CREDENTIALS_MESSAGE}

Verify Required Field Message
    [Documentation]    Verify required field validation message is displayed.
    Wait For Element To Be Ready    ${REQUIRED_FIELD_MESSAGE}
    Element Text Should Be    ${REQUIRED_FIELD_MESSAGE}    ${REQUIRED_FIELD_MESSAGE_TEXT}

Verify Password Field Is Masked
    [Documentation]    Verify password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    ${field_type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${field_type}    password

Verify Login Page Remains Accessible
    [Documentation]    Verify login form controls remain usable after failed authentication.
    Element Should Be Visible    ${USERNAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${LOGIN_BUTTON}
    Element Should Be Visible    ${FORGOT_PASSWORD_LINK}
    Element Should Be Enabled    ${LOGIN_BUTTON}

Verify Forgot Password Navigation
    [Documentation]    Verify forgot password navigation succeeds.
    Wait Until Page Does Not Contain Element    ${LOGIN_BUTTON}    ${DEFAULT_TIMEOUT}
    Location Should Not Contain    /auth/login

Click Orange Hrm Inc
    [Documentation]    Click action for Orange Hrm Inc link.
    Click When Ready    ${ORANGE_HRM_INC_LINK}
