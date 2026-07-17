*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify unauthenticated guest user can open the Login page from the Home page person profile button
    [Tags]    WT-LOGIN01    positive
    Verify Login Form Loaded
    Verify Navigation Buttons Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and interactive after opening Login page from Home page
    [Tags]    WT-LOGIN02    positive
    Verify Login Form Loaded
    Verify Navigation Buttons Loaded
    Element Should Be Enabled    ${USERNAME_TEXTBOX}
    Element Should Be Enabled    ${PASSWORD_TEXTBOX}
    Element Should Be Enabled    ${SIGN_IN_BUTTON}

AUT-WT-LOGIN03: Verify password input is masked while typing valid credentials
    [Tags]    WT-LOGIN03    positive
    Verify Login Form Loaded
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN04: Verify successful authentication using approved credentials returns user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Wait Until Element Is Not Visible    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN05: Verify authenticated Home page state persists immediately after successful login transition
    [Tags]    WT-LOGIN05    positive
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Wait Until Element Is Not Visible    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN06: Verify invalid username and password combination displays generic Failed message and keeps user unauthenticated
    [Tags]    WT-LOGIN06    negative
    Verify Login Form Loaded
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only generic Failed message
    [Tags]    WT-LOGIN07    negative
    Verify Login Form Loaded
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN08: Verify submission with Username populated and Password blank displays generic Failed message
    [Tags]    WT-LOGIN08    negative
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN09: Verify submission with Password populated and Username blank displays generic Failed message
    [Tags]    WT-LOGIN09    negative
    Verify Login Form Loaded
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN10: Verify leading and trailing whitespace handling for approved credentials
    [Tags]    WT-LOGIN10    edge
    Verify Login Form Loaded
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN11: Verify whitespace only Username and Password values are rejected with generic Failed message
    [Tags]    WT-LOGIN11    negative
    Verify Login Form Loaded
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN12: Verify Back button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Verify Login Form Loaded
    Click Back Button
    Wait Until Element Is Not Visible    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN13: Verify Home button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN13    positive
    Verify Login Form Loaded
    Click Home Button
    Wait Until Element Is Not Visible    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN14: Verify invalid password for approved username does not authenticate the user
    [Tags]    WT-LOGIN14    negative
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD_FOR_VALID_USER}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN17: Verify repeated invalid login submissions consistently display the same generic Failed message
    [Tags]    WT-LOGIN17    edge
    Verify Login Form Loaded
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Still Visible

AUT-WT-LOGIN19: Verify user remains unauthenticated after failed login followed by Home page navigation
    [Tags]    WT-LOGIN19    negative
    Verify Login Form Loaded
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Click Home Button
    Wait Until Element Is Not Visible    ${USERNAME_TEXTBOX}
