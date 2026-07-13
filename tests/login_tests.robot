*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE01: Open login page from Home page using profile button navigation
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE01    positive
    Open Browser To Url    ${HOME_PAGE_URL}
    Open Home Page And Click User Button    ${HOME_PAGE_URL}
    Verify Login Page Loaded

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE02: Verify login page UI elements are visible and interactive after navigation from Home page
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE02    positive
    Open Login Page
    Verify Login Page Loaded
    Verify Password Field Is Masked
    Element Should Be Enabled    ${LOGIN_BUTTON}

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE03: Login successfully with valid username and valid password
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE03    positive
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE04: Reject login with invalid username and valid password
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE04    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE05: Reject login with valid username and invalid password
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE05    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE06: Reject login when both username and password are invalid
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE06    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE07: Validate required field behavior when Login is clicked with both fields empty
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE07    negative
    Open Login Page
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE08: Validate required Username field when Password is entered
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE08    negative
    Open Login Page
    Enter User Name    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE09: Validate required Password field when Username is entered
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE09    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE10: Verify password characters are masked while typing
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE10    positive
    Open Login Page
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE11: Verify login behavior with leading and trailing spaces in Username and Password fields
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE11    edge
    Open Login Page
    Enter User Name    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE12: Validate behavior when Username field contains only whitespace characters
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE12    negative
    Open Login Page
    Enter User Name    ${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE13: Validate behavior when Password field contains only whitespace characters
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE13    negative
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${SPACE}
    Click Login Button
    Verify Required Field Validation
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE14: Verify login submission using keyboard Enter key after entering valid credentials
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE14    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login Using Enter Key
    Verify Login Successful

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE15: Verify login failure when credentials are pasted into the fields with invalid values
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE15    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE16: Verify successful login when valid credentials are pasted into input fields
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE16    positive
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Successful

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE17: Verify application stability when Login button is clicked repeatedly with valid credentials
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE17    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Repeat Keyword    3 times    Click Login Button
    Verify Login Successful

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE18: Verify application stability when Login button is clicked repeatedly with invalid credentials
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE18    edge
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Repeat Keyword    3 times    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE19: Verify Username field accepts long input without UI corruption
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE19    edge
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE20: Verify Password field accepts long input while remaining masked
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE20    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Verify Password Field Is Masked
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE21: Verify Username field handling of special characters
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE21    negative
    Open Login Page
    Enter User Name    ${INVALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Error Message
    Verify Login Failed
    Verify Login Page Remains Accessible

AUT-WT-CUSTOMERLOGSINFROMHOMEPAGE22: Verify Password field handling of special characters during authentication
    [Tags]    WT-CUSTOMERLOGSINFROMHOMEPAGE22    edge
    Open Login Page
    Enter User Name    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}${SPACE}
    Verify Password Field Is Masked
    Click Login Button
    Verify Login Failed
    Verify Login Page Remains Accessible
