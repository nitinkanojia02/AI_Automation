*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Setup    Open Login Page    ${LOGIN_PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads with all required UI elements
    [Tags]    WT-LOGIN01    positive
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify successful login with valid credentials
    [Tags]    WT-LOGIN02    positive
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN03: Verify login fails with valid username and invalid password
    [Tags]    WT-LOGIN03    negative
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN04: Verify login fails with invalid username and valid password
    [Tags]    WT-LOGIN04    negative
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN05: Verify login fails when both username and password are incorrect
    [Tags]    WT-LOGIN05    negative
    Enter Username    ${ALT_INVALID_USERNAME}
    Enter Password    ${ALT_INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN06: Verify login validation when username field is empty
    [Tags]    WT-LOGIN06    negative
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN07: Verify login validation when password field is empty
    [Tags]    WT-LOGIN07    negative
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN08: Verify login validation when both username and password fields are empty
    [Tags]    WT-LOGIN08    negative
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Username Required Validation
    Verify Password Required Validation

AUT-WT-LOGIN09: Verify password textbox masks entered characters
    [Tags]    WT-LOGIN09    positive
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN10: Verify home navigation button redirects to home page
    [Tags]    WT-LOGIN10    positive
    Click Home Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN11: Verify back navigation button redirects to home page
    [Tags]    WT-LOGIN11    positive
    Click Back Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN12: Verify login fails when username contains only whitespace
    [Tags]    WT-LOGIN12    negative
    Enter Username    ${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN13: Verify login fails when password contains only whitespace
    [Tags]    WT-LOGIN13    negative
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${SPACE}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN14: Verify login behavior with leading and trailing spaces in username
    [Tags]    WT-LOGIN14    edge
    Enter Username    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN15: Verify login attempt with very long username input
    [Tags]    WT-LOGIN15    edge
    Enter Username    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN16: Verify login attempt with very long password input
    [Tags]    WT-LOGIN16    edge
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN17: Verify multiple rapid clicks on Sign In button with valid credentials
    [Tags]    WT-LOGIN17    edge
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN18: Verify login using copy and paste credentials
    [Tags]    WT-LOGIN18    edge
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN19: Verify login submission using Enter key
    [Tags]    WT-LOGIN19    edge
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER
    Verify Successful Login Redirect

AUT-WT-LOGIN20: Verify login attempt with special characters in username
    [Tags]    WT-LOGIN20    edge
    Enter Username    ${SPECIAL_CHAR_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected
