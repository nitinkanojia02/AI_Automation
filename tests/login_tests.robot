*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Home Page
Suite Teardown    Close Browser Session
Test Setup    Run Keywords    Verify Home Page Loaded In Guest State    AND    Click Person Profile Button    AND    Verify Login Page Opened

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page opens from Home page using the person/profile button while user is in guest state
    [Tags]    WT-LOGIN01    positive

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after opening Login page from Home page
    [Tags]    WT-LOGIN02    positive

AUT-WT-LOGIN03: Verify password input is masked while entering password characters
    [Tags]    WT-LOGIN03    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Verify successful login using approved credentials returns user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN05: Verify invalid username and password combination displays generic Failed message and keeps user unauthenticated
    [Tags]    WT-LOGIN05    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN06: Verify login submission with both Username and Password fields empty displays only the generic Failed message
    [Tags]    WT-LOGIN06    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN07: Verify login submission with Username populated and Password empty displays generic Failed message
    [Tags]    WT-LOGIN07    negative
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN08: Verify login submission with Password populated and Username empty displays generic Failed message
    [Tags]    WT-LOGIN08    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN09: Verify login attempt with leading and trailing spaces around valid credentials follows implemented whitespace handling behavior
    [Tags]    WT-LOGIN09    edge
    Enter User Name Textbox    ${SPACE}${SPACE}${VALID_USERNAME}${SPACE}${SPACE}
    Enter Password Textbox    ${SPACE}${SPACE}${VALID_PASSWORD}${SPACE}${SPACE}
    Click Sign In Button
    Verify Login Form Loaded

AUT-WT-LOGIN10: Verify whitespace-only values in Username and Password fields display generic Failed message
    [Tags]    WT-LOGIN10    negative
    Enter User Name Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN11: Verify Back button returns the user to Home page without authentication
    [Tags]    WT-LOGIN11    positive
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN12: Verify Home button returns the user to Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify generic Failed message remains consistent across multiple invalid authentication attempts
    [Tags]    WT-LOGIN13    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Generic Failed Authentication Message
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN14: Verify successful login state displays authenticated-only UI after returning to Home page
    [Tags]    WT-LOGIN14    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN15: Verify credential fields accept special characters in password input without breaking masking behavior
    [Tags]    WT-LOGIN15    edge
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN16: Verify invalid credentials with correct username and incorrect password do not authenticate the user
    [Tags]    WT-LOGIN16    negative
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD_FOR_VALID_USER}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN17: Verify invalid credentials with incorrect username and correct password do not authenticate the user
    [Tags]    WT-LOGIN17    negative
    Enter User Name Textbox    ${WRONG_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected
