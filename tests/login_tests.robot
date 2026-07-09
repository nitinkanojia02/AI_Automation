*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page displays all approved login controls and title
    [Tags]    WT-LOGIN01    positive
    Open Login Page
    Verify Login Page Is Displayed
    Verify Login Button Is Enabled

AUT-WT-LOGIN02: Verify successful login using valid username and valid password
    [Tags]    WT-LOGIN02    positive
    Open Login Page
    Login With Valid Credentials
    Verify Successful Login

AUT-WT-LOGIN03: Verify login submission using Enter key from password field with valid credentials
    [Tags]    WT-LOGIN03    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login Using Enter Key
    Verify Successful Login

AUT-WT-LOGIN04: Verify login fails with invalid username and valid password
    [Tags]    WT-LOGIN04    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN05: Verify login fails with valid username and invalid password
    [Tags]    WT-LOGIN05    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN06: Verify login fails with both username and password invalid
    [Tags]    WT-LOGIN06    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME_ALT}    ${INVALID_PASSWORD_ALT}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN07: Verify required validation when username and password fields are empty
    [Tags]    WT-LOGIN07    negative
    Open Login Page
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN08: Verify required validation when password field is empty
    [Tags]    WT-LOGIN08    negative
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN09: Verify required validation when username field is empty
    [Tags]    WT-LOGIN09    negative
    Open Login Page
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN10: Verify password characters are masked while typing
    [Tags]    WT-LOGIN10    positive
    Open Login Page
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN11: Verify forgot password link is visible and navigates to password recovery page
    [Tags]    WT-LOGIN11    positive
    Open Login Page
    Click Forgot Password Link
    Verify Forgot Password Navigation

AUT-WT-LOGIN12: Verify logout redirects authenticated user back to login page
    [Tags]    WT-LOGIN12    positive
    Open Login Page
    Login With Valid Credentials
    Go To Url    ${LOGIN_PAGE_URL}
    Verify Login Page Is Displayed
    Verify Login Button Is Enabled

AUT-WT-LOGIN13: Verify login behavior with leading and trailing spaces in username field
    [Tags]    WT-LOGIN13    edge
    Open Login Page
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${VALID_PASSWORD}
    Verify User Remains On Login Page

AUT-WT-LOGIN14: Verify password field treats leading and trailing spaces as part of password value
    [Tags]    WT-LOGIN14    edge
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN15: Verify whitespace-only input is rejected in username and password fields
    [Tags]    WT-LOGIN15    negative
    Open Login Page
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN16: Verify login is case-sensitive for username field
    [Tags]    WT-LOGIN16    negative
    Open Login Page
    Login With Credentials    ${LOWERCASE_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN17: Verify login is case-sensitive for password field
    [Tags]    WT-LOGIN17    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${MIXED_CASE_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN18: Verify special characters in username field are rejected
    [Tags]    WT-LOGIN18    negative
    Open Login Page
    Login With Credentials    ${SPECIAL_CHARACTER_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN19: Verify very long username and password inputs do not break login form
    [Tags]    WT-LOGIN19    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Login Button
    Verify User Remains On Login Page

AUT-WT-LOGIN20: Verify repeated clicking of Login button with valid credentials does not create duplicate navigation behavior
    [Tags]    WT-LOGIN20    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Successful Login

AUT-WT-LOGIN21: Verify repeated clicking of Login button with invalid credentials consistently shows rejection
    [Tags]    WT-LOGIN21    edge
    Open Login Page
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN22: Verify copy-paste of valid credentials into login fields authenticates successfully
    [Tags]    WT-LOGIN22    edge
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Successful Login

AUT-WT-LOGIN23: Verify login page remains accessible after failed login attempt
    [Tags]    WT-LOGIN23    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify Login Page Is Displayed
    Verify Login Button Is Enabled

AUT-WT-LOGIN24: Verify browser refresh on login page preserves application usability
    [Tags]    WT-LOGIN24    edge
    Open Login Page
    Reload Page
    Verify Login Page Is Displayed
    Login With Valid Credentials
    Verify Successful Login

AUT-WT-LOGIN25: Verify login button is visible and clickable on initial page load
    [Tags]    WT-LOGIN25    positive
    Open Login Page
    Verify Login Button Is Enabled
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN26: Verify user cannot access dashboard URL directly after logout
    [Tags]    WT-LOGIN26    negative
    Open Login Page
    Login With Valid Credentials
    Go To Url    ${LOGIN_PAGE_URL}
    Verify Login Page Is Displayed
    Verify Login Button Is Enabled
