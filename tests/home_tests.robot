*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Guest State Loaded

AUT-WT-HOME02: Verify guest-state Home controls are visible and enabled on initial page load
    [Tags]    WT-HOME02    positive
    Verify Guest State Controls Visible And Enabled

AUT-WT-HOME03: Verify navigation from Person/Profile button opens the Login page or Login view
    [Tags]    WT-HOME03    positive
    Click Person Profile Button
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

AUT-WT-HOME07: Verify returning to the Home page preserves guest-state behavior after opening the Login view
    [Tags]    WT-HOME07    positive
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify Home button remains visible and enabled in guest state
    [Tags]    WT-HOME08    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Notification button remains visible and enabled in guest state
    [Tags]    WT-HOME09    positive
    Click Notification Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify Back button remains visible and enabled in guest state
    [Tags]    WT-HOME10    positive
    Click Back Button
    Verify Home Guest State Loaded
