*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Teardown    Close Browser Session
Test Setup    Run Keywords    Open Home Page    AND    Click Person Profile Button    AND    Verify Login Page Opened

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page opens from Home page guest state using the person-profile button
    [Tags]    WT-LOGIN01    positive
    Verify Home Page Loaded In Guest State
    Verify Login Page Opened
    Verify Login Form Loaded
    Verify Back Button

AUT-WT-LOGIN02: Verify Login page controls are visible enabled and interactive after opening from Home page
    [Tags]    WT-LOGIN02    positive
    Verify Login Page Opened
    Verify Login Form Loaded
    Verify Password Textbox
    Verify Back Button

AUT-WT-LOGIN03: Verify Password field masks entered characters during credential entry
    [Tags]    WT-LOGIN03    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Verify successful authentication using approved credentials returns the user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN05: Verify invalid username and password combination displays the generic Failed message and keeps the user unauthenticated
    [Tags]    WT-LOGIN05    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN06: Verify submitting the Login form with both Username and Password empty displays only the generic Failed message
    [Tags]    WT-LOGIN06    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN07: Verify submitting only Username without Password fails authentication and preserves unauthenticated state
    [Tags]    WT-LOGIN07    negative
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN08: Verify submitting only Password without Username fails authentication and preserves unauthenticated state
    [Tags]    WT-LOGIN08    negative
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN09: Verify leading and trailing whitespace handling for Username and Password values
    [Tags]    WT-LOGIN09    edge
    Enter User Name Textbox    ${SPACE}${SPACE}${VALID_USERNAME}${SPACE}${SPACE}
    Enter Password Textbox    ${SPACE}${SPACE}${VALID_PASSWORD}${SPACE}${SPACE}
    Click Sign In Button
    Wait Until Keyword Succeeds    2x    2s    Verify Generic Failed Message

AUT-WT-LOGIN10: Verify whitespace only Username and Password submission displays the generic Failed message
    [Tags]    WT-LOGIN10    negative
    Enter User Name Textbox    ${SPACE}${SPACE}
    Enter Password Textbox    ${SPACE}${SPACE}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN11: Verify the Back button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN11    positive
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN12: Verify the Home button returns the user to the Home page without authentication
    [Tags]    WT-LOGIN12    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify very long Username and Password values are rejected without authenticating the user
    [Tags]    WT-LOGIN13    edge
    ${long_username}    Evaluate    '${INVALID_USERNAME}' * 25
    ${long_password}    Evaluate    '${INVALID_PASSWORD}' * 25
    Enter User Name Textbox    ${long_username}
    Enter Password Textbox    ${long_password}
    Click Sign In Button
    Verify Login Page Remains Accessible

AUT-WT-LOGIN14: Verify user remains unauthenticated after failed login followed by Home page return navigation
    [Tags]    WT-LOGIN14    negative
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${WRONG_PASSWORD}
    Click Sign In Button
    Verify Login Page Remains Accessible
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN15: Verify navigation sequence preserves Home to Login to Home authenticated transition behavior
    [Tags]    WT-LOGIN15    positive
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    ${HOME_PAGE_PATH}
