*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session
Test Setup    Open Home Page And Click User Button    about:blank

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page opens from Home page using the person/profile button
    [Tags]    WT-LOGIN01    positive
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after navigation from Home page
    [Tags]    WT-LOGIN02    positive
    Verify Login Form Loaded

AUT-WT-LOGIN03: Verify password field masks entered characters by default
    [Tags]    WT-LOGIN03    positive
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN04: Verify successful login using approved valid credentials returns user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Login With Valid Credentials
    Wait Until Element Is Not Visible    ${SIGN_IN_BUTTON}

AUT-WT-LOGIN05: Verify invalid username prevents authentication and displays login error
    [Tags]    WT-LOGIN05    negative
    Login With Invalid Username
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN06: Verify invalid password prevents authentication and displays login error
    [Tags]    WT-LOGIN06    negative
    Login With Invalid Password
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN07: Verify login attempt with both invalid username and invalid password is rejected
    [Tags]    WT-LOGIN07    negative
    Login With Invalid Credentials
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN08: Verify required field validation when Login button is clicked with both fields empty
    [Tags]    WT-LOGIN08    negative
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN09: Verify Username required validation when Password is entered and Username is blank
    [Tags]    WT-LOGIN09    negative
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN10: Verify Password required validation when Username is entered and Password is blank
    [Tags]    WT-LOGIN10    negative
    Enter Username Textbox    ${VALID_USERNAME}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN11: Verify Back button on Login page returns user to Home page guest state
    [Tags]    WT-LOGIN11    positive
    Go To Url    about:blank
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN12: Verify Home button on Login page returns user to Home page guest state
    [Tags]    WT-LOGIN12    positive
    Go To Url    about:blank
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN13: Verify leading and trailing spaces in valid username and password are handled during login
    [Tags]    WT-LOGIN13    edge
    Enter Username Textbox    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Textbox    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Sign In Button
    Wait Until Page Contains Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN14: Verify whitespace-only Username and Password values are not accepted
    [Tags]    WT-LOGIN14    negative
    Enter Username Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN19: Verify special characters in invalid credentials do not bypass authentication
    [Tags]    WT-LOGIN19    negative
    Enter Username Textbox    ${INVALID_SPECIAL_CHARACTER_USERNAME}
    Enter Password Textbox    ${INVALID_SPECIAL_CHARACTER_PASSWORD}
    Click Sign In Button
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN20: Verify long Username and Password input values are handled without application crash
    [Tags]    WT-LOGIN20    edge
    Enter Username Textbox    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Sign In Button
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN21: Verify user remains in guest state after failed authentication attempt
    [Tags]    WT-LOGIN21    negative
    Login With Invalid Credentials
    Verify Authentication Error Message
    Verify Login Page Remains Visible After Failed Login

AUT-WT-LOGIN22: Verify authenticated Home page displays logged-in user identity after successful login
    [Tags]    WT-LOGIN22    positive
    Login With Valid Credentials
    Wait Until Element Is Not Visible    ${SIGN_IN_BUTTON}
