*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOME01    positive
    Open Home Page
    Verify Guest Home Page Loaded

AUT-WT-HOME02: Verify guest-state shared Home controls are visible and enabled on initial page load
    [Tags]    WT-HOME02    positive
    Open Home Page
    Verify Guest Home Controls Are Visible And Enabled
    Verify Guest Feature Buttons Are Ready

AUT-WT-HOME03: Verify clicking the Person/Profile button from guest Home state opens the Login page
    [Tags]    WT-HOME03    positive
    Open Home Page
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME04: Verify clicking the Customer signup button from guest Home state opens the customer-search page
    [Tags]    WT-HOME04    positive
    Open Home Page
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME05: Verify clicking the Clean survey button from guest Home state opens the vehicle-survey page
    [Tags]    WT-HOME05    positive
    Open Home Page
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME06: Verify clicking the Site survey button from guest Home state opens the survey page
    [Tags]    WT-HOME06    positive
    Open Home Page
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME07: Verify Person/Profile button remains enabled and responsive after returning to Home page
    [Tags]    WT-HOME07    edge
    Open Home Page
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Person Profile Button
    Click Person Profile Button
    Verify Login Page Opened

AUT-WT-HOME08: Verify shared Home shell controls remain visible in guest state after navigation back to Home
    [Tags]    WT-HOME08    positive
    Open Home Page
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-HOME09: Verify Home button is visible and enabled in guest state
    [Tags]    WT-HOME09    positive
    Open Home Page
    Wait For Element To Be Ready    ${HOME_BUTTON}

AUT-WT-HOME10: Verify Notification button is visible and enabled in guest state
    [Tags]    WT-HOME10    positive
    Open Home Page
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

AUT-WT-HOME11: Verify Back button is visible and enabled in guest state
    [Tags]    WT-HOME11    positive
    Open Home Page
    Wait For Element To Be Ready    ${BACK_BUTTON}

AUT-WT-HOME12: Verify guest Home page can be refreshed without losing guest-state controls
    [Tags]    WT-HOME12    edge
    Open Home Page
    Reload Page
    Verify Guest Home Page Loaded
    Verify Guest Feature Buttons Are Ready

AUT-WT-HOME13: Verify direct URL access to Home page always opens guest state when no authenticated session exists
    [Tags]    WT-HOME13    positive
    Open Home Page
    Verify Guest Home Page Loaded
    Verify Guest Home Controls Are Visible And Enabled

AUT-WT-HOME14: Verify guest-accessible feature buttons remain actionable after opening and leaving Login view
    [Tags]    WT-HOME14    edge
    Open Home Page
    Click Person Profile Button
    Verify Login Page Opened
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Remains In Guest State
    Verify Guest Feature Buttons Are Ready
    Click Site Survey Button
    Verify Survey Page Opened
