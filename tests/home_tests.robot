*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page In Guest State
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Guest State Loaded

AUT-WT-HOME02: Verify guest-state controls and shared Home shell controls are visible and enabled on Home page
    [Tags]    WT-HOME02    positive
    Verify Home Guest StateControls Visible
    Verify Home Guest State Controls Enabled

AUT-WT-HOME03: Verify Person/Profile button navigates from Home guest state to Login page or Login view
    [Tags]    WT-HOME03    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify Customer signup button navigates to customer-search page from Home guest state
    [Tags]    WT-HOME04    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify Clean survey button navigates to vehicle-survey page from Home guest state
    [Tags]    WT-HOME05    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify Site survey button navigates to survey page from Home guest state
    [Tags]    WT-HOME06    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME07: Verify navigation back to Home guest state after opening Login view from Person/Profile button
    [Tags]    WT-HOME07    positive
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify navigation back to Home guest state after opening customer-search page
    [Tags]    WT-HOME08    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify navigation back to Home guest state after opening vehicle-survey page
    [Tags]    WT-HOME09    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify navigation back to Home guest state after opening survey page
    [Tags]    WT-HOME10    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify repeated clicking of Person/Profile button does not create inconsistent navigation state
    [Tags]    WT-HOME11    edge
    Repeat Keyword    3 times    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME12: Verify Home button remains visible and enabled during guest-state execution
    [Tags]    WT-HOME12    positive
    Click Home Button
    Verify Home Guest State Loaded

AUT-WT-HOME13: Verify Notification button remains visible and enabled during guest-state execution
    [Tags]    WT-HOME13    positive
    Click Notification Button
    Verify Home Guest State Loaded

AUT-WT-HOME14: Verify Back button remains visible and enabled during guest-state execution
    [Tags]    WT-HOME14    positive
    Click Back Button
    Verify Home Guest State Loaded
