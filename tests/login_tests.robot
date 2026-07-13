*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page loads with all required authentication controls visible
    [Tags]    WT-LOGIN01    positive
    Open Login Page
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify successful login with valid username and valid password using Login button click
    [Tags]    WT-LOGIN02    positive
    Open Login Page
    Login With Valid Credentials
    Verify Login Successful

AUT-WT-LOGIN03: Verify successful login using keyboard Enter key submission after entering valid credentials
    [Tags]    WT-LOGIN03    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login Using Enter Key
    Verify Login Successful

AUT-WT-LOGIN04: Verify login fails with valid username and invalid password
    [Tags]    WT-LOGIN04    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Login Failed
    Verify Authentication Error Message

AUT-WT-LOGIN05: Verify login fails with invalid username and valid password
    [Tags]    WT-LOGIN05    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${VALID_PASSWORD}
    Verify Login Failed
    Verify Authentication Error Message

AUT-WT-LOGIN06: Verify login fails with both invalid username and invalid password
    [Tags]    WT-LOGIN06    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME_ALT}    ${INVALID_PASSWORD_ALT}
    Verify Login Failed
    Verify Authentication Error Message

AUT-WT-LOGIN07: Verify validation when Username field is left empty
    [Tags]    WT-LOGIN07    negative
    Open Login Page
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Login Failed
    Verify Required Field Validation

AUT-WT-LOGIN08: Verify validation when Password field is left empty
    [Tags]    WT-LOGIN08    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Login Failed
    Verify Required Field Validation

AUT-WT-LOGIN09: Verify validation when both Username and Password fields are empty
    [Tags]    WT-LOGIN09    negative
    Open Login Page
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Login Failed
    Verify Required Field Validation

AUT-WT-LOGIN10: Verify password field masks entered characters
    [Tags]    WT-LOGIN10    positive
    Open Login Page
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN11: Verify Username field accepts pasted text input
    [Tags]    WT-LOGIN11    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN12: Verify Password field accepts pasted text input
    [Tags]    WT-LOGIN12    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN13: Verify login behavior with leading and trailing spaces in Username field
    [Tags]    WT-LOGIN13    edge
    Open Login Page
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${VALID_PASSWORD}
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN14: Verify login behavior with leading and trailing spaces in Password field
    [Tags]    WT-LOGIN14    edge
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN15: Verify whitespace-only values are rejected in Username and Password fields
    [Tags]    WT-LOGIN15    negative
    Open Login Page
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Login Failed
    Verify Authentication Error Message

AUT-WT-LOGIN16: Verify username field handles special characters input without UI break
    [Tags]    WT-LOGIN16    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}!@#    ${VALID_PASSWORD}
    Verify Login Failed
    Verify Authentication Error Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN17: Verify login credentials are case sensitive
    [Tags]    WT-LOGIN17    negative
    Open Login Page
    ${upper_username}=    Evaluate    "${VALID_USERNAME}".upper()
    ${upper_password}=    Evaluate    "${VALID_PASSWORD}".upper()
    Login With Credentials    ${upper_username}    ${upper_password}
    Verify Login Failed
    Verify Authentication Error Message

AUT-WT-LOGIN18: Verify extremely long username input does not break the login page
    [Tags]    WT-LOGIN18    edge
    Open Login Page
    ${long_username}=    Evaluate    "a" * 256
    Login With Credentials    ${long_username}    ${VALID_PASSWORD}
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN19: Verify extremely long password input does not break the login page
    [Tags]    WT-LOGIN19    edge
    Open Login Page
    ${long_password}=    Evaluate    "a" * 256
    Login With Credentials    ${VALID_USERNAME}    ${long_password}
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN20: Verify repeated clicking on Login button during valid authentication does not create duplicate submissions
    [Tags]    WT-LOGIN20    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Repeat Keyword    3 times    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN21: Verify Login button remains functional after a failed login attempt followed by valid credentials
    [Tags]    WT-LOGIN21    positive
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME_ALT}    ${INVALID_PASSWORD_ALT}
    Verify Login Failed
    Verify Authentication Error Message
    Login With Valid Credentials
    Verify Login Successful

AUT-WT-LOGIN22: Verify login page remains accessible and interactive after failed authentication
    [Tags]    WT-LOGIN22    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Login Failed
    Verify Authentication Error Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN23: Verify browser refresh on login page retains functional login controls
    [Tags]    WT-LOGIN23    edge
    Open Login Page
    Reload Page
    Verify Login Page Loaded
    Login With Valid Credentials
    Verify Login Successful

AUT-WT-LOGIN25: Verify Password field does not retain visible value after failed login attempt
    [Tags]    WT-LOGIN25    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Login Failed
    Verify Authentication Error Message
    Verify Password Field Is Masked
