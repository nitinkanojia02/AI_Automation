*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home Page Loads Successfully In Guest State
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-HOME02: Verify Guest State Shared Home Controls Are Visible And Enabled
    [Tags]    WT-HOME02    positive
    Verify Guest Home Controls Are Visible And Enabled
    Verify Home Page Loaded In Guest State

AUT-WT-HOME03: Verify Guest Accessible Feature Buttons Are Visible And Enabled
    [Tags]    WT-HOME03    positive
    Verify Guest Feature Buttons Are Ready
    Verify Home Page Loaded In Guest State

AUT-WT-HOME04: Verify Clicking Person Profile Button Opens Login Page
    [Tags]    WT-HOME04    positive
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME05: Verify Clicking Customer Signup Navigates To Customer Search Page
    [Tags]    WT-HOME05    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME06: Verify Clicking Clean Survey Navigates To Vehicle Survey Page
    [Tags]    WT-HOME06    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME07: Verify Clicking Site Survey Navigates To Survey Page
    [Tags]    WT-HOME07    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME08: Verify Home Button Remains Visible And Enabled In Guest State
    [Tags]    WT-HOME08    positive
    Verify Guest Home Controls Are Visible And Enabled
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Notification Button Is Visible And Clickable In Guest State
    [Tags]    WT-HOME09    positive
    Verify Guest Home Controls Are Visible And Enabled
    Click Notification Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify Back Button Is Visible And Clickable In Guest State
    [Tags]    WT-HOME10    positive
    Verify Guest Home Controls Are Visible And Enabled
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify Guest Accessible Feature Buttons Remain Interactable After Returning Home
    [Tags]    WT-HOME11    edge
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Open Home Page
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Open Home Page
    Verify Home Page Remains In Guest State
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME12: Verify Direct Navigation Loads Guest State For Unauthenticated Session
    [Tags]    WT-HOME12    edge
    Verify Home Page Loaded In Guest State
    Verify Guest Home Controls Are Visible And Enabled
