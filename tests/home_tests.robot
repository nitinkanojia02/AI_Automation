*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page In Guest State
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify all approved guest-state buttons and shared Home shell controls are visible and enabled on Home page
    [Tags]    WT-HOME02    positive
    Verify Home Guest State Controls Are Visible
    Verify Home Guest State Controls Are Enabled

AUT-WT-HOME03: Verify Person/Profile button navigates from Home guest state to Login page or Login view
    [Tags]    WT-HOME03    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify Customer signup button navigates from Home guest state to customer-search page
    [Tags]    WT-HOME04    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify Clean survey button navigates from Home guest state to vehicle-survey page
    [Tags]    WT-HOME05    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify Site survey button navigates from Home guest state to survey page
    [Tags]    WT-HOME06    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME09: Verify navigation back to Home guest state after opening Login view from Person/Profile button
    [Tags]    WT-HOME09    positive
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify navigation back to Home guest state after opening customer-search page
    [Tags]    WT-HOME10    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify navigation back to Home guest state after opening vehicle-survey page
    [Tags]    WT-HOME11    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME12: Verify navigation back to Home guest state after opening survey page
    [Tags]    WT-HOME12    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME13: Verify repeated clicking of Person/Profile button does not create broken navigation state
    [Tags]    WT-HOME13    edge
    Repeat Keyword    3 times    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME17: Verify Home button remains visible and enabled throughout guest-state workflow navigation
    [Tags]    WT-HOME17    positive
    Verify Home Guest State Controls Are Enabled
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Home Guest State Controls Are Enabled

AUT-WT-HOME18: Verify Notification button remains visible and enabled throughout guest-state workflow
    [Tags]    WT-HOME18    positive
    Verify Home Guest State Controls Are Enabled
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Home Guest State Controls Are Enabled

AUT-WT-HOME19: Verify Back button remains visible and enabled throughout guest-state workflow
    [Tags]    WT-HOME19    positive
    Verify Home Guest State Controls Are Enabled
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Home Guest State Controls Are Enabled
