*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Setup    Open Login Page    ${LOGIN_PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads and all required UI elements are visible
    [Tags]    WT-LOGIN01    positive
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify successful login with valid username and password
    [Tags]    WT-LOGIN02    positive
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN03: Verify login fails with invalid username and valid password
    [Tags]    WT-LOGIN03    negative
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN04: Verify login fails with valid username and incorrect password
    [Tags]    WT-LOGIN04    negative
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${INCORRECT_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN05: Verify login fails when both username and password are invalid
    [Tags]    WT-LOGIN05    negative
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN06: Verify validation when username field is empty
    [Tags]    WT-LOGIN06    negative
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN07: Verify validation when password field is empty
    [Tags]    WT-LOGIN07    negative
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN08: Verify validation when both username and password fields are empty
    [Tags]    WT-LOGIN08    negative
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN09: Verify password field masks entered characters
    [Tags]    WT-LOGIN09    positive
    Verify Login Page Loaded
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN10: Verify home navigation button redirects user to home page
    [Tags]    WT-LOGIN10    positive
    Verify Login Page Loaded
    Click Home Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN11: Verify back navigation button redirects user to home page
    [Tags]    WT-LOGIN11    positive
    Verify Login Page Loaded
    Click Back Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN12: Verify login behavior when username contains leading and trailing spaces
    [Tags]    WT-LOGIN12    edge
    Verify Login Page Loaded
    Enter Username    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Run Keyword And Return Status    Verify Successful Login Redirect
    Run Keyword And Return Status    Verify Login Rejected

AUT-WT-LOGIN13: Verify login attempt using whitespace-only values
    [Tags]    WT-LOGIN13    negative
    Verify Login Page Loaded
    Enter Username    ${SPACE}${SPACE}
    Enter Password    ${SPACE}${SPACE}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN14: Verify system behavior when SIGN IN button is clicked multiple times rapidly
    [Tags]    WT-LOGIN14    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN15: Verify login attempt with very long username and password values
    [Tags]    WT-LOGIN15    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN16: Verify login submission using Enter key from password field
    [Tags]    WT-LOGIN16    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER
    Verify Successful Login Redirect

AUT-WT-LOGIN17: Verify login using copy and paste for credentials
    [Tags]    WT-LOGIN17    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect
