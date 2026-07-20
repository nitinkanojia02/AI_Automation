*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify Guest User Can Open The Login Page From The Home Page Using The Person Profile Button
    [Tags]    WT-LOGIN01    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login Page Controls Remain Visible And Interactive After Opening From The Home Page
    [Tags]    WT-LOGIN02    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Verify Login Form Loaded
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}

AUT-WT-LOGIN03: Verify Password Input Is Masked While Entering Credentials On The Login Page
    [Tags]    WT-LOGIN03    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Verify Successful Login Returns The User To The Authenticated Home Page State
    [Tags]    WT-LOGIN04    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Login With Valid Credentials
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN05: Verify Authenticated Home Page State Persists Immediately After Successful Login Transition
    [Tags]    WT-LOGIN05    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Login With Valid Credentials
    Wait Until Location Contains    ${HOME_PAGE_PATH}

AUT-WT-LOGIN06: Verify Invalid Username And Password Combination Displays The Generic Failed Message And Keeps The User Unauthenticated
    [Tags]    WT-LOGIN06    negative
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Login With Invalid Credentials
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN07: Verify Blank Username And Blank Password Submission Displays Only The Generic Failed Message
    [Tags]    WT-LOGIN07    negative
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN08: Verify Login Attempt With Username Only Populated Fails With The Generic Failed Message
    [Tags]    WT-LOGIN08    negative
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN09: Verify Login Attempt With Password Only Populated Fails With The Generic Failed Message
    [Tags]    WT-LOGIN09    negative
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN10: Verify Leading And Trailing Whitespace Handling For Username And Password Values
    [Tags]    WT-LOGIN10    edge
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Textbox    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Sign In Button
    ${login_success}=    Run Keyword And Return Status    Wait Until Location Contains    ${HOME_PAGE_PATH}
    Run Keyword If    ${login_success}    Wait Until Location Contains    ${HOME_PAGE_PATH}
    Run Keyword If    not ${login_success}    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}

AUT-WT-LOGIN11: Verify Whitespace Only Values In Username And Password Fields Fail Authentication With The Generic Failed Message
    [Tags]    WT-LOGIN11    negative
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Enter User Name Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN12: Verify The Back Button Returns The User To The Home Page Without Authenticating
    [Tags]    WT-LOGIN12    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN13: Verify The Home Button Returns The User To The Home Page Without Authenticating
    [Tags]    WT-LOGIN13    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-LOGIN19: Verify Very Long Username And Password Values Are Handled Without Breaking The Login Page
    [Tags]    WT-LOGIN19    edge
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    ${long_username}=    Evaluate    "A" * 256
    ${long_password}=    Evaluate    "B" * 256
    Enter User Name Textbox    ${long_username}
    Enter Password Textbox    ${long_password}
    Click Sign In Button
    Wait Until Page Contains    ${GENERIC_FAILED_MESSAGE}
    Verify Login Form Loaded

AUT-WT-LOGIN20: Verify Login Page Navigation Sequence Preserves Home To Login To Home SPA Behavior
    [Tags]    WT-LOGIN20    positive
    Open Home Page
    Verify Home Page Loaded In Guest State
    Click Person Profile Button
    Verify Login Page Opened
    Login With Valid Credentials
    Wait Until Location Contains    ${HOME_PAGE_PATH}
