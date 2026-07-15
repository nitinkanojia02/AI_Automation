*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${HOME_PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Open Home Page In Guest State

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Is Loaded

AUT-WT-HOME02: Verify all approved guest-state controls are visible and enabled
    [Tags]    WT-HOME02    positive
    Verify Guest State Controls Are Visible
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME03: Verify clicking the Person Profile button opens the Login page
    [Tags]    WT-HOME03    positive
    Verify Person Button
    Verify Login Page URL

AUT-WT-HOME04: Verify Customer signup button navigates to the customer-search page
    [Tags]    WT-HOME04    positive
    Click Customer Signup Button
    Verify Customer Search Page Navigation

AUT-WT-HOME05: Verify Clean survey button navigates to the vehicle-survey page
    [Tags]    WT-HOME05    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation

AUT-WT-HOME06: Verify Site survey button navigates to the survey page
    [Tags]    WT-HOME06    positive
    Click Site Survey Button
    Verify Survey Page Navigation

AUT-WT-HOME07: Verify Home button is visible and enabled in guest state
    [Tags]    WT-HOME07    positive
    Wait For Element To Be Ready    ${HOME_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME08: Verify Back button is visible and enabled in guest state
    [Tags]    WT-HOME08    positive
    Wait For Element To Be Ready    ${BACK_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME09: Verify Notification button is visible and enabled in guest state
    [Tags]    WT-HOME09    positive
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}    ${HOME_PAGE_LOAD_TIMEOUT}
    Verify Guest Home Controls Are Enabled

AUT-WT-HOME10: Verify Person Profile button remains accessible after returning from Login view
    [Tags]    WT-HOME10    edge
    Click Person Button
    Verify User Is Navigated To Login Page
    Open Home Page In Guest State
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify Home button interaction preserves guest-state controls
    [Tags]    WT-HOME11    edge
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME12: Verify sequential navigation across guest-accessible feature buttons
    [Tags]    WT-HOME12    positive
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Open Home Page In Guest State
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation
    Open Home Page In Guest State
    Verify Home Page Remains In Guest State
    Click Site Survey Button
    Verify Survey Page Navigation

AUT-WT-HOME13: Verify direct navigation to the Home URL opens the guest Home state
    [Tags]    WT-HOME13    edge
    Open Home Page In Guest State
    Verify Home Page Is Loaded

AUT-WT-HOME14: Verify guest-state controls remain actionable after navigating away and returning to Home
    [Tags]    WT-HOME14    edge
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Open Home Page In Guest State
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation
