*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Home Page
Suite Teardown    Close Browser Session
Test Setup    Run Keywords    Verify Home Page Loaded In Guest State    AND    Click Person Profile Button    AND    Verify Login Page Opened    AND    Verify Login Form Loaded

*** Test Cases ***
AUT-WT-LOGIN01: Verify Home guest state opens Login page through the person profile button navigation flow
    [Tags]    WT-LOGIN01    positive
    Verify Back Button

AUT-WT-LOGIN02: Verify Login page controls are visible enabled and interactive after opening from Home page
    [Tags]    WT-LOGIN02    positive
    Verify User Name Textbox
    Verify Password Textbox
    Verify Back Button

AUT-WT-LOGIN03: Verify password input remains masked during credential entry
    [Tags]    WT-LOGIN03    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Verify successful login with approved credentials returns the user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN05: Verify authenticated Home page state persists immediately after successful login transition
    [Tags]    WT-LOGIN05    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN06: Verify invalid username and password combination displays the generic Failed message and blocks authentication
    [Tags]    WT-LOGIN06    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only the generic Failed message
    [Tags]    WT-LOGIN07    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN08: Verify submission with only Username populated fails authentication with the generic Failed message
    [Tags]    WT-LOGIN08    negative
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN09: Verify submission with only Password populated fails authentication with the generic Failed message
    [Tags]    WT-LOGIN09    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN10: Verify leading and trailing whitespace handling for Username and Password values
    [Tags]    WT-LOGIN10    edge
    Enter User Name Textbox    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Textbox    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Sign In Button

AUT-WT-LOGIN11: Verify whitespace only Username and Password values fail authentication using the generic Failed message
    [Tags]    WT-LOGIN11    negative
    Enter User Name Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN12: Verify Back button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify Home button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN13    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN14: Verify failed authentication keeps the application on Login flow without authenticated transition
    [Tags]    WT-LOGIN14    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN15: Verify special character input in Username and Password fields does not bypass authentication validation
    [Tags]    WT-LOGIN15    negative
    Enter User Name Textbox    ${SPECIAL_CHARACTER_USERNAME}
    Enter Password Textbox    ${SPECIAL_CHARACTER_PASSWORD}
    Click Sign In Button
    Verify Login Rejected

AUT-WT-LOGIN16: Verify very long Username and Password values do not authenticate the user and do not break Login page behavior
    [Tags]    WT-LOGIN16    edge
    Enter User Name Textbox    ${LONG_USERNAME}
    Enter Password Textbox    ${LONG_PASSWORD}
    Click Sign In Button
    Verify Login Rejected
