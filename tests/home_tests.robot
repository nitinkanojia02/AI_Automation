*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page In Guest State
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Guest State Loaded
    Verify Guest State Controls Are Visible And Enabled

AUT-WT-HOME02: Verify guest-state Home controls and shared shell controls are visible and enabled
    [Tags]    WT-HOME02    positive
    Verify Guest State Controls Are Visible And Enabled

AUT-WT-HOME03: Verify Person/Profile button navigates from Home guest state to Login page
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

AUT-WT-HOME09: Verify returning to Home guest state after navigating to Login view
    [Tags]    WT-HOME09    positive
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify returning to Home guest state after navigating to customer-search page
    [Tags]    WT-HOME10    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify returning to Home guest state after navigating to vehicle-survey page
    [Tags]    WT-HOME11    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME12: Verify returning to Home guest state after navigating to survey page
    [Tags]    WT-HOME12    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME13: Verify Home button remains visible and enabled during guest-state execution
    [Tags]    WT-HOME13    positive
    Verify Guest State Controls Are Visible And Enabled
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME14: Verify Back button remains visible and enabled during guest-state execution
    [Tags]    WT-HOME14    positive
    Verify Home Page Guest State Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Click Back Button
    Verify Home Page Guest State Loaded

AUT-WT-HOME15: Verify Notification button remains visible and enabled in guest state
    [Tags]    WT-HOME15    positive
    Verify Home Page Guest State Loaded
    Click Notification Button
    Verify Guest State Controls Are Visible And Enabled
