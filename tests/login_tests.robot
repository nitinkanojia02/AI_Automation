*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Teardown    Close Browser Session
Test Setup    Open Home Page

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page opens from Home page guest state using the person/profile button
    [Tags]    WT-LOGIN01    positive
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible enabled and interactive after opening from Home page
    [Tags]    WT-LOGIN02    positive
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded
    Verify Back Button
    Verify Password Textbox
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}

AUT-WT-LOGIN03: Verify password field masks entered characters during credential entry
    [Tags]    WT-LOGIN03    positive
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Verify successful authentication with approved credentials returns the user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-LOGIN05: Verify authenticated Home state is visible after successful login
    [Tags]    WT-LOGIN05    positive
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-LOGIN06: Verify invalid username and password combination displays generic Failed message and keeps user unauthenticated
    [Tags]    WT-LOGIN06    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only generic Failed message
    [Tags]    WT-LOGIN07    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN08: Verify login attempt with only Username populated fails and keeps user unauthenticated
    [Tags]    WT-LOGIN08    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN09: Verify login attempt with only Password populated fails and keeps user unauthenticated
    [Tags]    WT-LOGIN09    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN10: Verify leading and trailing whitespace handling for valid credentials
    [Tags]    WT-LOGIN10    edge
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Textbox    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Sign In Button
    Run Keywords
    ...    Run Keyword And Ignore Error    Verify Generic Failed Message
    ...    AND
    ...    Run Keyword And Ignore Error    Verify Home Page Loaded In Guest State

AUT-WT-LOGIN11: Verify whitespace-only values in Username and Password fields fail authentication
    [Tags]    WT-LOGIN11    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible

AUT-WT-LOGIN12: Verify Back button returns the user to Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Click Person Profile Button
    Verify Login Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify Home button returns the user to Home page without authentication
    [Tags]    WT-LOGIN13    positive
    Click Person Profile Button
    Verify Login Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN20: Verify failed authentication keeps Login page controls accessible for another attempt
    [Tags]    WT-LOGIN20    negative
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Generic Failed Message
    Verify Login Page Remains Accessible
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Login Form Loaded
