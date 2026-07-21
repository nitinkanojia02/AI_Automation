*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Guest State Loaded

AUT-WT-HOME02: Verify guest-state controls are visible and enabled
    [Tags]    WT-HOME02    positive
    Verify Guest State Controls Visible And Enabled

AUT-WT-HOME03: Verify clicking the Person/Profile button opens the Login page or Login view
    [Tags]    WT-HOME03    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify returning to Home guest state after opening the Login view keeps guest controls available
    [Tags]    WT-HOME04    positive
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME05: Verify clicking the Customer signup button opens the customer-search page
    [Tags]    WT-HOME05    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME06: Verify clicking the Clean survey button opens the vehicle-survey page
    [Tags]    WT-HOME06    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME07: Verify clicking the Site survey button opens the survey page
    [Tags]    WT-HOME07    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME08: Verify Home button remains visible and enabled while already on the Home guest state
    [Tags]    WT-HOME08    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Back button is visible and enabled in Home guest state before any additional navigation
    [Tags]    WT-HOME09    positive
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify Notification button is visible and enabled in Home guest state for unauthenticated users
    [Tags]    WT-HOME10    positive
    Click Notification Button
    Verify Home Page Remains In Guest State
