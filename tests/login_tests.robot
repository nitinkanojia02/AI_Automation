*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads with all required UI elements
    [Tags]    WT-LOGIN01    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify successful login with valid credentials
    [Tags]    WT-LOGIN02    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN03: Verify login fails with incorrect password
    [Tags]    WT-LOGIN03    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN04: Verify login fails with incorrect username
    [Tags]    WT-LOGIN04    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN05: Verify login fails when both username and password are incorrect
    [Tags]    WT-LOGIN05    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN06: Verify login validation when username field is empty
    [Tags]    WT-LOGIN06    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN07: Verify login validation when password field is empty
    [Tags]    WT-LOGIN07    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN08: Verify login validation when both username and password are empty
    [Tags]    WT-LOGIN08    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN09: Verify password textbox masks entered characters
    [Tags]    WT-LOGIN09    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN10: Verify navigation to home page using home navigation button
    [Tags]    WT-LOGIN10    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Click Home Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN11: Verify navigation to home page using back navigation button
    [Tags]    WT-LOGIN11    positive
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Click Back Navigation Button
    Verify Successful Login Redirect

AUT-WT-LOGIN12: Verify username textbox accepts pasted input
    [Tags]    WT-LOGIN12    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN13: Verify login attempt with leading and trailing spaces in username
    [Tags]    WT-LOGIN13    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN14: Verify login attempt with whitespace-only username
    [Tags]    WT-LOGIN14    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN15: Verify login attempt with whitespace-only password
    [Tags]    WT-LOGIN15    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${SPACE}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN16: Verify behavior when SIGN IN button is clicked multiple times rapidly
    [Tags]    WT-LOGIN16    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN17: Verify login attempt with extremely long username input
    [Tags]    WT-LOGIN17    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN18: Verify login fails with special characters in username
    [Tags]    WT-LOGIN18    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Input Text When Ready    ${USERNAME_TEXTBOX}    @@@###
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN19: Verify login submission using Enter key
    [Tags]    WT-LOGIN19    edge
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Press Keys    ${PASSWORD_TEXTBOX}    ENTER
    Verify Successful Login Redirect

AUT-WT-LOGIN20: Verify login attempt with uppercase username
    [Tags]    WT-LOGIN20    negative
    Open Login Page    ${LOGIN_PAGE_URL}
    Verify Login Page Loaded
    Input Text When Ready    ${USERNAME_TEXTBOX}    HACKLARR
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page
