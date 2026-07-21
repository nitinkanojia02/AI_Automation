*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page In Guest State
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify guest-state Home controls are visible and enabled on initial page load
    [Tags]    WT-HOME02    positive
    Verify Guest State Controls Are Visible
    Verify Guest State Controls Are Enabled

AUT-WT-HOME03: Verify navigation from Person/Profile button opens the Login page or Login view from Home guest state
    [Tags]    WT-HOME03    positive
    Click Person Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify navigation from Customer signup button opens the customer-search page
    [Tags]    WT-HOME04    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify navigation from Clean survey button opens the vehicle-survey page
    [Tags]    WT-HOME05    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify navigation from Site survey button opens the survey page
    [Tags]    WT-HOME06    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME07: Verify navigation back to Home guest state after opening Login view from Person/Profile button
    [Tags]    WT-HOME07    positive
    Click Person Button
    Verify Login Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify navigation back to Home guest state after opening customer-search page
    [Tags]    WT-HOME08    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify navigation back to Home guest state after opening vehicle-survey page
    [Tags]    WT-HOME09    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify navigation back to Home guest state after opening survey page
    [Tags]    WT-HOME10    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify Home button remains visible and enabled throughout guest-state navigation
    [Tags]    WT-HOME11    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State
    Click Home Button
    Verify Home Page Loaded In Guest State

AUT-WT-HOME12: Verify Back button is visible and enabled in Home guest state
    [Tags]    WT-HOME12    positive
    Verify Guest State Controls Are Visible
    Verify Guest State Controls Are Enabled
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME13: Verify Notification button is visible and enabled in Home guest state
    [Tags]    WT-HOME13    positive
    Verify Guest State Controls Are Visible
    Verify Guest State Controls Are Enabled
    Click Notification Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME14: Verify Home page remains in guest state after repeated navigation between guest-accessible pages
    [Tags]    WT-HOME14    edge
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State
