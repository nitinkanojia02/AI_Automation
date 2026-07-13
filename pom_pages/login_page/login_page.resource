*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    http://localhost/washtabui/login?data=undefined
${HOME_PAGE_URL}    http://localhost/washtabui/home
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    WrongPassword1
${INVALID_USERNAME_ALT}    wronguser
${INVALID_PASSWORD_ALT}    wrongpassword
${USERNAME_TEXTBOX}    xpath=//input[@placeholder='User Name']
${PASSWORD_TEXTBOX}    xpath=//ion-input[@id='password']
${LOGIN_BUTTON}    xpath=//ion-button[@text='Login']
${LOGIN_FAILED_MESSAGE}    login failed
${REQUIRED_FIELD_MESSAGE}    required
${BACKGROUND_CONTENT_ELEMENT}    id=background-content

*** Keywords ***
Open Login Page
    [Documentation]    Navigate directly to the login page URL.
    Open Browser To Url    ${LOGIN_PAGE_URL}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Enter User Name
    [Documentation]    Enter text into Username textbox.
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_TEXTBOX}    ${text}

Enter Password
    [Documentation]    Enter password into Password textbox.
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Login Button
    [Documentation]    Click Login button on login page.
    Click When Ready    ${LOGIN_BUTTON}

Login With Credentials
    [Documentation]    Perform login using provided credentials.
    [Arguments]    ${username}    ${password}
    Enter User Name    ${username}
    Enter Password    ${password}
    Click Login Button

Login With Valid Credentials
    [Documentation]    Perform login using valid application credentials.
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}

Submit Login Using Enter Key
    [Documentation]    Submit login form using Enter key from Password textbox.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER

Verify Login Page Loaded
    [Documentation]    Verify login page elements are visible and interactive.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Verify Login Successful
    [Documentation]    Verify successful authentication redirects user to home page.
    Wait Until Location Contains    ${HOME_PAGE_URL}    ${DEFAULT_TIMEOUT}

Verify Login Failed
    [Documentation]    Verify failed authentication keeps user on login page.
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}

Verify Authentication Error Message
    [Documentation]    Verify authentication failure message is displayed.
    Page Should Contain    ${LOGIN_FAILED_MESSAGE}

Verify Required Field Validation
    [Documentation]    Verify required field validation is displayed.
    Page Should Contain    ${REQUIRED_FIELD_MESSAGE}

Verify Password Field Is Masked
    [Documentation]    Verify password field masks entered characters.
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Element Attribute Value Should Be    ${PASSWORD_TEXTBOX}    type    password

Verify Login Page Remains Accessible
    [Documentation]    Verify login page remains interactive after failed authentication.
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Click Background Content
    [Documentation]    Click Background Content element.
    Click When Ready    ${BACKGROUND_CONTENT_ELEMENT}
