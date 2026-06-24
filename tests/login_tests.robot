*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Setup    Open Home Page And Click User Button    ${HOME_PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify successful login using valid username and valid password through SIGN IN button
    [Tags]    WT-LOGIN01    positive
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN02: Verify login fails when valid username is entered with incorrect password
    [Tags]    WT-LOGIN02    negative
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${INCORRECT_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN03: Verify login fails when invalid username is entered with valid password
    [Tags]    WT-LOGIN03    negative
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN04: Verify login fails when both username and password are invalid
    [Tags]    WT-LOGIN04    negative
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN05: Verify login attempt when both username and password fields are empty
    [Tags]    WT-LOGIN05    negative
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Username Required Validation
    Verify Password Required Validation

AUT-WT-LOGIN06: Verify login attempt when username is empty and password is entered
    [Tags]    WT-LOGIN06    negative
    Verify Login Page Loaded
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Username Required Validation

AUT-WT-LOGIN07: Verify login attempt when password is empty and username is entered
    [Tags]    WT-LOGIN07    negative
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Sign In Button
    Verify Password Required Validation

AUT-WT-LOGIN08: Verify password textbox masks characters during typing
    [Tags]    WT-LOGIN08    positive
    Verify Login Page Loaded
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN09: Verify login succeeds when valid credentials are pasted into fields
    [Tags]    WT-LOGIN09    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN10: Verify login behavior when username contains leading and trailing whitespace
    [Tags]    WT-LOGIN10    edge
    Verify Login Page Loaded
    Enter Username    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN11: Verify login fails when username and password contain only whitespace characters
    [Tags]    WT-LOGIN11    negative
    Verify Login Page Loaded
    Enter Username    ${SPACE}${SPACE}
    Enter Password    ${SPACE}${SPACE}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN12: Verify repeated rapid clicks on SIGN IN button with valid credentials do not trigger duplicate submissions
    [Tags]    WT-LOGIN12    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Click Sign In Button
    Click Sign In Button
    Verify Successful Login Redirect

AUT-WT-LOGIN13: Verify clicking back navigation button on login page navigates to home page
    [Tags]    WT-LOGIN13    positive
    Verify Login Page Loaded
    Click Back Navigation Button
    Verify Back Navigation Redirects To Home Page

AUT-WT-LOGIN14: Verify clicking home navigation button on login page navigates to home page
    [Tags]    WT-LOGIN14    positive
    Verify Login Page Loaded
    Click Home Navigation Button
    Verify Home Navigation Redirects To Home Page

AUT-WT-LOGIN15: Verify login page displays all required UI elements and they are interactable
    [Tags]    WT-LOGIN15    positive
    Verify Login Page Loaded

AUT-WT-LOGIN16: Verify login submission using keyboard Enter key from password field
    [Tags]    WT-LOGIN16    edge
    Verify Login Page Loaded
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login With Enter Key
    Verify Successful Login Redirect

AUT-WT-LOGIN17: Verify login fails when username case differs from valid username
    [Tags]    WT-LOGIN17    edge
    Verify Login Page Loaded
    Enter Username    ${UPPERCASE_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page

AUT-WT-LOGIN18: Verify login fails when extremely long values are entered in username and password fields
    [Tags]    WT-LOGIN18    edge
    Verify Login Page Loaded
    Enter Username    ${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}${INVALID_USERNAME}
    Enter Password    ${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And Still On Login Page
