*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state from the SPA landing URL
    [Tags]    WT-HOME01    positive
    Open Home Page
    Verify Guest Home Page Loaded
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-HOME02: Verify all approved guest-state controls are visible and enabled on Home page
    [Tags]    WT-HOME02    positive
    Open Home Page
    Verify Guest Home Controls Are Visible And Enabled
    Verify Person Profile Button
    Verify Back Button
    Verify Notification Button
    Verify Home Button
    Verify Guest Feature Buttons Are Ready

AUT-WT-HOME03: Verify Person/Profile button opens the Login page from guest Home state
    [Tags]    WT-HOME03    positive
    Open Home Page
    Verify Person Profile Button
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify Customer signup button navigates to the customer-search page
    [Tags]    WT-HOME04    positive
    Open Home Page
    Verify Customer Signup Button
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify Clean survey button navigates to the vehicle-survey page
    [Tags]    WT-HOME05    positive
    Open Home Page
    Verify Clean Survey Button
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify Site survey button navigates to the survey page
    [Tags]    WT-HOME06    positive
    Open Home Page
    Verify Site Survey Button
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME07: Verify Home page remains the same SPA Home resource in guest state
    [Tags]    WT-HOME07    positive
    Open Home Page
    Verify Home Button
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify Home button is visible and enabled in guest state
    [Tags]    WT-HOME08    positive
    Open Home Page
    Verify Home Button
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Notification button is visible and enabled in guest state
    [Tags]    WT-HOME09    positive
    Open Home Page
    Verify Notification Button
    Click Notification Button
    Verify Guest Home Page Loaded
    Verify Notification Button

AUT-WT-HOME10: Verify Back button is visible and enabled in guest state
    [Tags]    WT-HOME10    positive
    Open Home Page
    Verify Back Button
    Click Back Button
    Verify Guest Home Page Loaded
    Verify Back Button

AUT-WT-HOME11: Verify guest-accessible feature buttons remain actionable before authentication
    [Tags]    WT-HOME11    positive
    Open Home Page
    Verify Guest Feature Buttons Are Ready
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Open Home Page
    Verify Guest Feature Buttons Are Ready
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Open Home Page
    Verify Guest Feature Buttons Are Ready
    Click Site Survey Button
    Verify Survey Page Opened
