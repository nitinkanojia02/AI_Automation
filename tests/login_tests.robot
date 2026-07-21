*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Teardown    Close Browser Session
Test Setup    Open Home Page In Guest State

*** Test Cases ***
AUT-WT-LOGIN01: Verify Home page guest state opens and Login page is accessed through the person profile button
    [Tags]    WT-LOGIN01    positive
    Verify Home Page Guest State Loaded
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and interactive after opening from Home page
    [Tags]    WT-LOGIN02    positive
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded
    Click When Ready    ${USERNAME_FIELD}
    Click When Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

AUT-WT-LOGIN03: Verify password entry is masked while typing credentials
    [Tags]    WT-LOGIN03    positive
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${VALID_USERNAME}
    Enter Password Field    ${VALID_PASSWORD}
    Verify Password Field

AUT-WT-LOGIN04: Verify successful authentication returns the user to authenticated Home page state
    [Tags]    WT-LOGIN04    positive
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${VALID_USERNAME}
    Enter Password Field    ${VALID_PASSWORD}
    Click Login Button
    Wait Until Location Contains    ${AUTHENTICATED_HOME_STATE_IDENTIFIER}

AUT-WT-LOGIN06: Verify invalid username and password combination displays generic Failed message and keeps user unauthenticated
    [Tags]    WT-LOGIN06    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${INVALID_USERNAME}
    Enter Password Field    ${INVALID_PASSWORD}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only generic Failed message
    [Tags]    WT-LOGIN07    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${EMPTY}
    Enter Password Field    ${EMPTY}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN08: Verify submission with Username populated and Password blank fails authentication
    [Tags]    WT-LOGIN08    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${VALID_USERNAME}
    Enter Password Field    ${EMPTY}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN09: Verify submission with Password populated and Username blank fails authentication
    [Tags]    WT-LOGIN09    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${EMPTY}
    Enter Password Field    ${VALID_PASSWORD}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN10: Verify leading and trailing whitespace handling for valid credentials
    [Tags]    WT-LOGIN10    edge
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Field    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN11: Verify whitespace only credential submission fails with generic Failed message
    [Tags]    WT-LOGIN11    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${SPACE}
    Enter Password Field    ${SPACE}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN12: Verify Back button returns user to Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Click Person Profile Button
    Verify Login Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify Home button returns user to Home page without authentication
    [Tags]    WT-LOGIN13    positive
    Click Person Profile Button
    Verify Login Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN14: Verify generic Failed message consistency across invalid credential scenarios
    [Tags]    WT-LOGIN14    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${INVALID_USERNAME}
    Enter Password Field    ${INVALID_PASSWORD}
    Click Login Button
    Verify Generic Failed Authentication Message
    Clear Element Text    ${USERNAME_FIELD}
    Clear Element Text    ${PASSWORD_FIELD}
    Enter Username Field    ${EMPTY}
    Enter Password Field    ${EMPTY}
    Click Login Button
    Verify Generic Failed Authentication Message
    Clear Element Text    ${USERNAME_FIELD}
    Clear Element Text    ${PASSWORD_FIELD}
    Enter Username Field    ${VALID_USERNAME}
    Enter Password Field    ${EMPTY}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated

AUT-WT-LOGIN20: Verify user remains unauthenticated after failed login and can still navigate back to Home page
    [Tags]    WT-LOGIN20    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter Username Field    ${INVALID_USERNAME}
    Enter Password Field    ${INVALID_PASSWORD}
    Click Login Button
    Verify Login Failed And User Remains Unauthenticated
    Click Home Button
    Verify Home Page Remains In Guest State
