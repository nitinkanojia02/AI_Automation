*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-HOME02: Verify all approved guest-state controls and shared Home shell controls are visible and enabled on Home page
    [Tags]    WT-HOME02    positive
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled
    Verify Guest Accessible Feature Buttons Are Visible And Enabled

AUT-WT-HOME03: Verify Person Profile button navigates from Home guest state to Login page or Login view
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

AUT-WT-HOME07: Verify guest-state execution remains unauthenticated after navigating to Login view from Person Profile button
    [Tags]    WT-HOME07    negative
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify Home button remains enabled and accessible in guest state
    [Tags]    WT-HOME08    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Back button is visible and does not expose authenticated functionality in guest state
    [Tags]    WT-HOME09    negative
    Verify Guest Home Controls Are Visible And Enabled
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify repeated clicks on Customer signup button do not create duplicate customer-search transitions
    [Tags]    WT-HOME10    edge
    Repeat Keyword    3 times    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME11: Verify guest-state controls remain visible after returning to Home page from Customer signup flow
    [Tags]    WT-HOME11    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME12: Verify guest-state controls remain visible after returning to Home page from Clean survey flow
    [Tags]    WT-HOME12    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME13: Verify guest-state controls remain visible after returning to Home page from Site survey flow
    [Tags]    WT-HOME13    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
