*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for unauthenticated user
    [Tags]    WT-HOME01    positive
    Open Home Page In Guest State
    Verify Home Page Is Loaded

AUT-WT-HOME02: Verify Person/Profile button opens Login page from guest Home state
    [Tags]    WT-HOME02    positive
    Open Home Page In Guest State
    Click Person Profile Button
    Verify User Is Navigated To Login Page

AUT-WT-HOME03: Verify Customer signup button navigates to customer-search page
    [Tags]    WT-HOME03    positive
    Open Home Page In Guest State
    Click Customer Signup Button
    Verify Customer Search Page Navigation

AUT-WT-HOME04: Verify Clean survey button navigates to vehicle-survey page
    [Tags]    WT-HOME04    positive
    Open Home Page In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation

AUT-WT-HOME05: Verify Site survey button navigates to survey page
    [Tags]    WT-HOME05    positive
    Open Home Page In Guest State
    Click Site Survey Button
    Verify Survey Page Navigation

AUT-WT-HOME06: Verify Back button returns user to Home page from customer-search page
    [Tags]    WT-HOME06    positive
    Open Home Page In Guest State
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Click Back Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME07: Verify Back button returns user to Home page from vehicle-survey page
    [Tags]    WT-HOME07    positive
    Open Home Page In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation
    Click Back Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME08: Verify Back button returns user to Home page from survey page
    [Tags]    WT-HOME08    positive
    Open Home Page In Guest State
    Click Site Survey Button
    Verify Survey Page Navigation
    Click Back Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME09: Verify Home button returns user to Home page from customer-search page
    [Tags]    WT-HOME09    positive
    Open Home Page In Guest State
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Click Home Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME10: Verify Home button returns user to Home page from vehicle-survey page
    [Tags]    WT-HOME10    positive
    Open Home Page In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation
    Click Home Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME11: Verify Home button returns user to Home page from survey page
    [Tags]    WT-HOME11    positive
    Open Home Page In Guest State
    Click Site Survey Button
    Verify Survey Page Navigation
    Click Home Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME12: Verify Home button behavior when already on Home page in guest state
    [Tags]    WT-HOME12    edge
    Open Home Page In Guest State
    Click Home Button
    Verify Home Page Remains In Guest State
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME13: Verify Back button behavior when user is already on initial Home page guest state
    [Tags]    WT-HOME13    edge
    Open Home Page In Guest State
    Click Back Button
    Verify Home Page URL
    Verify Guest State Controls Are Visible
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME14: Verify Notification button is visible and enabled in guest Home state
    [Tags]    WT-HOME14    positive
    Open Home Page In Guest State
    Verify Guest State Controls Are Visible
    Click Notification Button
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME15: Verify guest-accessible feature buttons remain available after returning to Home page
    [Tags]    WT-HOME15    positive
    Open Home Page In Guest State
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Click Home Button
    Verify Home Page Remains In Guest State
    Verify Guest State Controls Are Visible
    Verify Guest Home Controls Are Enabled
