*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Setup    Open Login Page    http://172.21.166.115/washtabui/login?data=undefined
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads with correct URL and login form
    [Tags]    WT-LOGIN01    positive
    Verify Login Page Loaded
    ${url}=    Get Location
    Should Be Equal    ${url}    http://172.21.166.115/washtabui/login?data=undefined

AUT-WT-LOGIN02: Verify User Name, Password fields and SIGN IN button are visible and enabled
    [Tags]    WT-LOGIN02    positive
    Verify Login Page Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}
    Element Should Be Enabled    ${USERNAME_FIELD}
    Element Should Be Enabled    ${PASSWORD_FIELD}
    Element Should Be Enabled    ${SIGN_IN_BUTTON}

AUT-WT-LOGIN03: Verify Home and Arrow Back controls are visible on login page
    [Tags]    WT-LOGIN03    positive
    Verify Login Navigation Controls Visible
    Element Should Be Enabled    ${HOME_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}

AUT-WT-LOGIN04: Successful login with valid credentials using SIGN IN button
    [Tags]    WT-LOGIN04    positive
    Login With Credentials    haklarr    Icstunnel1
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN05: Successful login using Enter key from Password field
    [Tags]    WT-LOGIN05    positive
    Verify Login Page Loaded
    Enter Username    haklarr
    Enter Password    Icstunnel1
    Press Keys    ${PASSWORD_FIELD}    ENTER
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN06: Login fails with incorrect password
    [Tags]    WT-LOGIN06    negative
    Attempt Login With Credentials    haklarr    WrongPassword123
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN07: Login fails with incorrect username
    [Tags]    WT-LOGIN07    negative
    Attempt Login With Credentials    invaliduser    Icstunnel1
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN08: Validation when both username and password fields are blank
    [Tags]    WT-LOGIN08    negative
    Verify Login Page Loaded
    Click Sign In Button
    Verify Username Required Validation
    Verify Password Required Validation

AUT-WT-LOGIN09: Validation when username is blank and password is entered
    [Tags]    WT-LOGIN09    negative
    Verify Login Page Loaded
    Enter Password    Icstunnel1
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN10: Validation when password is blank and username is entered
    [Tags]    WT-LOGIN10    negative
    Verify Login Page Loaded
    Enter Username    haklarr
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN11: Login attempt using whitespace-only values
    [Tags]    WT-LOGIN11    edge
    Attempt Login With Credentials    ${SPACE}${SPACE}    ${SPACE}${SPACE}
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN12: Login with leading and trailing spaces around username
    [Tags]    WT-LOGIN12    edge
    Attempt Login With Credentials    ${SPACE}haklarr${SPACE}    Icstunnel1
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN13: Verify password field masks entered characters
    [Tags]    WT-LOGIN13    positive
    Verify Login Page Loaded
    Input Text When Ready    ${PASSWORD_FIELD}    Icstunnel1
    ${type}=    Get Element Attribute    ${PASSWORD_FIELD}    type
    Should Be Equal    ${type}    password

AUT-WT-LOGIN14: Login fails when password case is incorrect
    [Tags]    WT-LOGIN14    negative
    Attempt Login With Credentials    haklarr    icstunnel1
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN15: Login fails when username case differs
    [Tags]    WT-LOGIN15    edge
    Attempt Login With Credentials    HAKLARR    Icstunnel1
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN16: Verify Home control redirects to home page
    [Tags]    WT-LOGIN16    positive
    Verify Login Navigation Controls Visible
    Click Home Button
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN17: Verify Arrow Back control redirects to home page
    [Tags]    WT-LOGIN17    positive
    Verify Login Navigation Controls Visible
    Click Arrow Back Button
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN18: Verify handling of extremely long username input
    [Tags]    WT-LOGIN18    edge
    ${long}=    Evaluate    "a"*300
    Attempt Login With Credentials    ${long}    Icstunnel1
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN19: Login attempt with special characters in username
    [Tags]    WT-LOGIN19    edge
    Attempt Login With Credentials    haklarr!@#    Icstunnel1
    Verify Login Rejected
    ${url}=    Get Location
    Should Contain    ${url}    /login

AUT-WT-LOGIN20: Verify multiple rapid clicks on SIGN IN button do not create duplicate submissions
    [Tags]    WT-LOGIN20    edge
    Verify Login Page Loaded
    Enter Username    haklarr
    Enter Password    Icstunnel1
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login

AUT-WT-LOGIN21: Successful login using copied and pasted credentials
    [Tags]    WT-LOGIN21    edge
    Verify Login Page Loaded
    Input Text When Ready    ${USERNAME_FIELD}    haklarr
    Input Text When Ready    ${PASSWORD_FIELD}    Icstunnel1
    Click Sign In Button
    ${url}=    Get Location
    Should Contain    ${url}    /home
    Should Not Contain    ${url}    /login
