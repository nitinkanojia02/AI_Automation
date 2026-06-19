*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads with correct URL and required controls
    [Tags]    WT-LOGIN01    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify login page input fields accept user input
    [Tags]    WT-LOGIN02    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    ${entered_user}=    Get Element Attribute    ${USERNAME_TEXTBOX}    value
    Should Be Equal    ${entered_user}    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN03: Verify successful login with valid credentials
    [Tags]    WT-LOGIN03    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN04: Verify login fails with incorrect password
    [Tags]    WT-LOGIN04    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN05: Verify login fails with incorrect username
    [Tags]    WT-LOGIN05    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN06: Verify login fails when both username and password are incorrect
    [Tags]    WT-LOGIN06    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${WRONG_USERNAME}
    Enter Password    ${WRONG_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN07: Verify login attempt when username field is empty
    [Tags]    WT-LOGIN07    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN08: Verify login attempt when password field is empty
    [Tags]    WT-LOGIN08    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN09: Verify login attempt when both username and password fields are empty
    [Tags]    WT-LOGIN09    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN10: Verify password field masks entered characters
    [Tags]    WT-LOGIN10    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN11: Verify navigation to home page using home button
    [Tags]    WT-LOGIN11    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Click Home Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN12: Verify navigation to home page using back button
    [Tags]    WT-LOGIN12    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Click Back Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN13: Verify login submission using Enter key
    [Tags]    WT-LOGIN13    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER
    Verify Successful Login Redirect

AUT-WT-LOGIN14: Verify login attempt with leading and trailing spaces in username
    [Tags]    WT-LOGIN14    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN15: Verify login attempt with whitespace-only values
    [Tags]    WT-LOGIN15    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${SPACE}
    Enter Password    ${SPACE}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN16: Verify system behavior when clicking SIGN IN multiple times rapidly
    [Tags]    WT-LOGIN16    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN17: Verify login attempt using extremely long username and password values
    [Tags]    WT-LOGIN17    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN18: Verify login with copied and pasted credentials
    [Tags]    WT-LOGIN18    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect
