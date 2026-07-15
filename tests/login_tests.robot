*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Open login page from Home page using profile button navigation
    [Tags]    WT-LOGIN01    positive
    Open Browser To Url    ${HOME_PAGE_URL}
    Open Home Page And Click User Button    ${HOME_PAGE_URL}
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify login page UI elements are visible and interactive after navigation from Home page
    [Tags]    WT-LOGIN02    positive
    Open Login Page
    Verify Login Page Loaded
    Verify Password Field Is Masked
    Element Should Be Enabled    ${LOGIN_BUTTON}

AUT-WT-LOGIN03: Login successfully with valid username and valid password
    [Tags]    WT-LOGIN03    positive
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN04: Reject login with invalid username and valid password
    [Tags]    WT-LOGIN04    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN05: Reject login with valid username and invalid password
    [Tags]    WT-LOGIN05    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN06: Reject login when both username and password are invalid
    [Tags]    WT-LOGIN06    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN07: Validate required field behavior when Login is clicked with both fields empty
    [Tags]    WT-LOGIN07    negative
    Open Login Page
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN08: Validate required Username field when Password is entered
    [Tags]    WT-LOGIN08    negative
    Open Login Page
    Enter User Name    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN09: Validate required Password field when Username is entered
    [Tags]    WT-LOGIN09    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN10: Verify password characters are masked while typing
    [Tags]    WT-LOGIN10    positive
    Open Login Page
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN11: Verify login behavior with leading and trailing spaces in Username and Password fields
    [Tags]    WT-LOGIN11    edge
    Open Login Page
    Enter User Name    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN12: Validate behavior when Username field contains only whitespace characters
    [Tags]    WT-LOGIN12    negative
    Open Login Page
    Enter User Name    ${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN13: Validate behavior when Password field contains only whitespace characters
    [Tags]    WT-LOGIN13    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${SPACE}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN14: Verify login submission using keyboard Enter key after entering valid credentials
    [Tags]    WT-LOGIN14    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login Using Enter Key
    Verify Login Successful

AUT-WT-LOGIN15: Verify login failure when credentials are pasted into the fields with invalid values
    [Tags]    WT-LOGIN15    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN16: Verify successful login when valid credentials are pasted into input fields
    [Tags]    WT-LOGIN16    positive
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN17: Verify application stability when Login button is clicked repeatedly with valid credentials
    [Tags]    WT-LOGIN17    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Repeat Keyword    3 times    Click Login Button
    Verify Login Successful

AUT-WT-LOGIN18: Verify application stability when Login button is clicked repeatedly with invalid credentials
    [Tags]    WT-LOGIN18    edge
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Repeat Keyword    3 times    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN19: Verify Username field accepts long input without UI corruption
    [Tags]    WT-LOGIN19    edge
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN20: Verify Password field accepts long input while remaining masked
    [Tags]    WT-LOGIN20    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Verify Password Field Is Masked
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN21: Verify Username field handling of special characters
    [Tags]    WT-LOGIN21    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-LOGIN22: Verify Password field handling of special characters during authentication
    [Tags]    WT-LOGIN22    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${SPACE}
    Verify Password Field Is Masked
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible
