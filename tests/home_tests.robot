*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page In Guest State
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state from the approved entry URL
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify Person/Profile button is visible and enabled in guest state
    [Tags]    WT-HOME02    positive
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

AUT-WT-HOME03: Verify Back button is visible and enabled in guest state
    [Tags]    WT-HOME03    positive
    Wait For Element To Be Ready    ${BACK_BUTTON}

AUT-WT-HOME04: Verify Notification button is visible and enabled in guest state
    [Tags]    WT-HOME04    positive
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}

AUT-WT-HOME05: Verify Home button is visible and enabled in guest state
    [Tags]    WT-HOME05    positive
    Wait For Element To Be Ready    ${HOME_BUTTON}

AUT-WT-HOME06: Verify Customer signup button is visible and enabled in guest state
    [Tags]    WT-HOME06    positive
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}

AUT-WT-HOME07: Verify Clean survey button is visible and enabled in guest state
    [Tags]    WT-HOME07    positive
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}

AUT-WT-HOME08: Verify Site survey button is visible and enabled in guest state
    [Tags]    WT-HOME08    positive
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}

AUT-WT-HOME09: Verify navigation from Person/Profile button opens Login page or Login view
    [Tags]    WT-HOME09    positive
    Click Person Button
    Verify Login Page Opened

AUT-WT-HOME10: Verify return to Home guest state after opening Login view from Person/Profile button
    [Tags]    WT-HOME10    positive
    Click Person Button
    Verify Login Page Opened
    Go To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Page Remains In Guest State

AUT-WT-HOME11: Verify Customer signup button navigates to customer-search page
    [Tags]    WT-HOME11    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened

AUT-WT-HOME12: Verify Clean survey button navigates to vehicle-survey page
    [Tags]    WT-HOME12    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened

AUT-WT-HOME13: Verify Site survey button navigates to survey page
    [Tags]    WT-HOME13    positive
    Click Site Survey Button
    Verify Survey Page Opened

AUT-WT-HOME14: Verify Home button interaction preserves guest-state session
    [Tags]    WT-HOME14    positive
    Click Home Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME15: Verify Notification button interaction does not expose authenticated functionality to guest users
    [Tags]    WT-HOME15    negative
    Click Notification Button
    Verify Home Page Remains In Guest State
    Verify Guest State Controls Are Visible

AUT-WT-HOME16: Verify Back button interaction does not incorrectly authenticate the guest user
    [Tags]    WT-HOME16    negative
    Click Back Button
    Verify Home Page Remains In Guest State
    Verify Guest State Controls Are Visible

AUT-WT-HOME17: Verify guest-accessible controls remain available after returning from customer-search page
    [Tags]    WT-HOME17    positive
    Click Customer Signup Button
    Verify Customer Search Page Opened
    Go To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME18: Verify guest-accessible controls remain available after returning from vehicle-survey page
    [Tags]    WT-HOME18    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Opened
    Go To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME19: Verify guest-accessible controls remain available after returning from survey page
    [Tags]    WT-HOME19    positive
    Click Site Survey Button
    Verify Survey Page Opened
    Go To Url    ${HOME_GUEST_STATE_URL}
    Verify Home Page Loaded In Guest State
