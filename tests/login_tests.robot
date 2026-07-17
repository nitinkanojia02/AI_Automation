*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify guest user can open the Login page from the Home page using the person/profile button
    [Tags]    WT-LOGIN01    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Verify Navigation Buttons Are Visible

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after navigation from Home page
    [Tags]    WT-LOGIN02    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Verify Navigation Buttons Are Visible

AUT-WT-LOGIN03: Verify password input is masked while entering credentials on the Login page
    [Tags]    WT-LOGIN03    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN04: Verify successful authentication using approved credentials returns user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Login Form Loaded

AUT-WT-LOGIN05: Verify authenticated Home page state persists immediately after successful login transition
    [Tags]    WT-LOGIN05    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Login Form Loaded

AUT-WT-LOGIN06: Verify invalid credentials display generic Failed message and keep user unauthenticated
    [Tags]    WT-LOGIN06    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only generic Failed message
    [Tags]    WT-LOGIN07    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN08: Verify submission with Username populated and Password blank fails authentication
    [Tags]    WT-LOGIN08    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN09: Verify submission with Password populated and Username blank fails authentication
    [Tags]    WT-LOGIN09    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN10: Verify Login page Back button returns user to Home page without authentication
    [Tags]    WT-LOGIN10    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Click Back Button
    Verify Login Form Loaded

AUT-WT-LOGIN11: Verify Login page Home button returns user to Home page without authentication
    [Tags]    WT-LOGIN11    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Click Home Button
    Verify Login Form Loaded

AUT-WT-LOGIN12: Verify leading and trailing whitespace handling for valid credentials
    [Tags]    WT-LOGIN12    edge
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Login Page Remains Visible

AUT-WT-LOGIN13: Verify whitespace-only values in Username and Password fields fail authentication with generic Failed message
    [Tags]    WT-LOGIN13    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN18: Verify very long credential values do not authenticate and application remains stable
    [Tags]    WT-LOGIN18    edge
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Verify Login PageRemains Visible

AUT-WT-LOGIN19: Verify special characters in Username and Password fields do not bypass authentication
    [Tags]    WT-LOGIN19    negative
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${SPECIAL_CHARACTER_USERNAME}    ${SPECIAL_CHARACTER_PASSWORD}
    Verify Authentication Failed Message Displayed
    Verify Login Page Remains Visible

AUT-WT-LOGIN20: Verify successful login flow begins only from Home page navigation path
    [Tags]    WT-LOGIN20    positive
    Go To Url    about:blank
    Verify Login Form Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Login Form Loaded
