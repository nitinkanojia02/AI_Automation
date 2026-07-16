*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Run Keywords    Open Browser Session    AND    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state from direct URL navigation
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify guest-state controls and guest-accessible feature buttons are visible and enabled on Home page
    [Tags]    WT-HOME02    positive
    Verify Home Page Guest Controls Visible
    Verify Home Page Guest Controls Enabled

AUT-WT-HOME03: Verify Person Profile button opens the Login page from guest Home state
    [Tags]    WT-HOME03    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify Customer signup button navigates to the customer-search page
    [Tags]    WT-HOME04    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify Clean survey button navigates to the vehicle-survey page
    [Tags]    WT-HOME05    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify Site survey button navigates to the survey page
    [Tags]    WT-HOME06    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME07: Verify Home button returns the user to Home page after navigating to Customer signup
    [Tags]    WT-HOME07    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Home Button
    Verify Home Page Loaded In Guest State

AUT-WT-HOME08: Verify Back button returns the user to Home page after navigating to Clean survey
    [Tags]    WT-HOME08    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Click Back Button
    Verify Home Page Loaded In Guest State

AUT-WT-HOME09: Verify Home button keeps the user on the Home page when already in guest Home state
    [Tags]    WT-HOME09    edge
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify Back button behavior from initial guest Home page load
    [Tags]    WT-HOME10    edge
    Click Back Button
    Verify Home Page Guest Controls Visible

AUT-WT-HOME11: Verify Notification button is visible and interactive in guest Home state
    [Tags]    WT-HOME11    positive
    Click Notification Button
    Verify Home Page Guest Controls Visible
    Verify Home Page Guest Controls Enabled

AUT-WT-HOME12: Verify guest-accessible feature buttons remain enabled after returning to Home page
    [Tags]    WT-HOME12    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Home Button
    Verify Home Page Guest Controls Visible
    Verify Home Page Guest Controls Enabled
