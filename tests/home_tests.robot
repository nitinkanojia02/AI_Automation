*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Browser To Url    ${HOME_PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for unauthenticated user
    [Tags]    WT-HOME01    positive
    Verify Home Page Is Loaded
    Verify Guest Accessible Feature Buttons

AUT-WT-HOME02: Verify Person Profile button opens Login page from guest Home state
    [Tags]    WT-HOME02    positive
    Verify Home Page Is Loaded
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME03: Verify Customer signup button navigates to customer-search page
    [Tags]    WT-HOME03    positive
    Verify Home Page Is Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME04: Verify Clean survey button navigates to vehicle-survey page
    [Tags]    WT-HOME04    positive
    Verify Home Page Is Loaded
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME05: Verify Site survey button navigates to survey page
    [Tags]    WT-HOME05    positive
    Verify Home Page Is Loaded
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME06: Verify authenticated-only controls are not visible in guest Home state
    [Tags]    WT-HOME06    negative
    Verify Home Page Is Loaded
    Wait Until Element Is Not Visible    xpath=//*[contains(text(),'Logout')]    5s
    Wait Until Element Is Not Visible    xpath=//*[contains(text(),'Sign Out')]    5s
    Verify Guest Accessible Feature Buttons

AUT-WT-HOME07: Verify Back button returns user to Home page after navigating to Customer signup page
    [Tags]    WT-HOME07    positive
    Verify Home Page Is Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME08: Verify Home button returns user to Home page after navigating to Clean survey page
    [Tags]    WT-HOME08    positive
    Verify Home Page Is Loaded
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME09: Verify Home button returns user to Home page after navigating to Site survey page
    [Tags]    WT-HOME09    positive
    Verify Home Page Is Loaded
    Click Site Survey Button
    Verify Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME10: Verify Back button from Login page returns to Home page guest state
    [Tags]    WT-HOME10    positive
    Verify Home Page Is Loaded
    Click Person Profile Button
    Verify Login Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify Home button from Login page returns to Home page guest state
    [Tags]    WT-HOME11    positive
    Verify Home Page Is Loaded
    Click Person Profile Button
    Verify Login Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME12: Verify Notification button is visible enabled and stable in guest Home state
    [Tags]    WT-HOME12    positive
    Verify Notification Button
    Click Notification Button
    Verify Notification Button
    Verify Home Page Guest Controls Are Visible

AUT-WT-HOME13: Verify direct navigation to Home URL opens guest Home state
    [Tags]    WT-HOME13    positive
    Verify Home Page Is Loaded
    Verify Guest Accessible Feature Buttons

AUT-WT-HOME14: Verify Home button behavior when already on Home page guest state
    [Tags]    WT-HOME14    edge
    Verify Home Page Is Loaded
    Click Home Button
    Verify Browser Url Contains Home Path
    Verify Home Page Remains In Guest State

AUT-WT-HOME15: Verify Back button behavior when guest user is already on initial Home page
    [Tags]    WT-HOME15    edge
    Verify Home Page Is Loaded
    Click Back Button
    Verify Browser Url Contains Home Path
    Verify Home Page Guest Controls Are Visible

AUT-WT-HOME16: Verify guest-accessible feature buttons remain available after returning from secondary page
    [Tags]    WT-HOME16    positive
    Verify Home Page Is Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Back Button
    Verify Guest Accessible Feature Buttons

AUT-WT-HOME17: Verify guest Home state remains unauthenticated after navigating through multiple guest workflows
    [Tags]    WT-HOME17    edge
    Verify Home Page Is Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State
    Click Site Survey Button
    Verify Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State
    Wait Until Element Is Not Visible    xpath=//*[contains(text(),'Logout')]    5s

AUT-WT-HOME18: Verify Person Profile button remains visible after returning from Login page
    [Tags]    WT-HOME18    positive
    Verify Home Page Is Loaded
    Click Person Profile Button
    Verify Login Page Opened
    Click Back Button
    Verify Person Profile Button

AUT-WT-HOME19: Verify guest-accessible feature buttons can be opened sequentially without application instability
    [Tags]    WT-HOME19    edge
    Verify Home Page Is Loaded
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Click Back Button
    Verify Home Page Remains In Guest State
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State
    Click Site Survey Button
    Verify Survey Page Opened
    Click Home Button
    Verify Home Page Remains In Guest State
