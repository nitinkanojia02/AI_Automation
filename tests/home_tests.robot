*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session
Test Setup    Open Home Page

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state when application is launched
    [Tags]    WT-HOME01    positive
    Verify Guest Home Page Loaded

AUT-WT-HOME02: Verify Person Profile button is visible and enabled in guest state
    [Tags]    WT-HOME02    positive
    Verify Person Profile Button

AUT-WT-HOME03: Verify Back button is visible and enabled in guest state
    [Tags]    WT-HOME03    positive
    Verify Back Button

AUT-WT-HOME04: Verify Notification button is visible and enabled in guest state
    [Tags]    WT-HOME04    positive
    Verify Notification Button

AUT-WT-HOME05: Verify Home button is visible and enabled in guest state
    [Tags]    WT-HOME05    positive
    Verify Home Button

AUT-WT-HOME06: Verify Customer signup button is visible and enabled in guest state
    [Tags]    WT-HOME06    positive
    Verify Customer Signup Button

AUT-WT-HOME07: Verify Clean survey button is visible and enabled in guest state
    [Tags]    WT-HOME07    positive
    Verify Clean Survey Button

AUT-WT-HOME08: Verify Site survey button is visible and enabled in guest state
    [Tags]    WT-HOME08    positive
    Verify Site Survey Button

AUT-WT-HOME09: Verify clicking the Person Profile button opens the Login page from guest Home state
    [Tags]    WT-HOME09    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME10: Verify clicking Customer signup navigates to the customer-search page
    [Tags]    WT-HOME10    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME11: Verify clicking Clean survey navigates to the vehicle-survey page
    [Tags]    WT-HOME11    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME12: Verify clicking Site survey navigates to the survey page
    [Tags]    WT-HOME12    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME20: Verify Home button remains visible and enabled after navigating back from a guest-accessible feature page
    [Tags]    WT-HOME20    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Home Button

