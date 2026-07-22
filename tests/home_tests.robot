*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Browser To Url    ${PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state using the approved entry URL
    [Tags]    WT-HOME01    generic
    Verify Home Page Loaded In Guest State
    Location Should Be    ${EXPECTED_HOME_URL}

AUT-WT-HOME02: Verify Person/Profile button is visible and enabled on the guest Home page
    [Tags]    WT-HOME02    generic
    Verify Person Profile Button Visible And Enabled

AUT-WT-HOME03: Verify Back button is visible and enabled on the guest Home page
    [Tags]    WT-HOME03    generic
    Verify Back Button Visible And Enabled

AUT-WT-HOME04: Verify Notification button is visible and enabled on the guest Home page
    [Tags]    WT-HOME04    generic
    Verify Notification Button Visible And Enabled

AUT-WT-HOME05: Verify Home button is visible and enabled on the guest Home page
    [Tags]    WT-HOME05    generic
    Verify Home Button Visible And Enabled
    Click Home Button
    Location Should Be    ${EXPECTED_HOME_URL}

AUT-WT-HOME06: Verify Customer signup button is visible and enabled on the guest Home page
    [Tags]    WT-HOME06    generic
    Verify Customer Signup Button Visible And Enabled

AUT-WT-HOME07: Verify Clean survey button is visible and enabled on the guest Home page
    [Tags]    WT-HOME07    generic
    Verify Clean Survey Button Visible And Enabled

AUT-WT-HOME08: Verify Site survey button is visible and enabled on the guest Home page
    [Tags]    WT-HOME08    generic
    Verify Site Survey Button Visible And Enabled

AUT-WT-HOME09: Verify Person/Profile button navigates guest user to the login page URL
    [Tags]    WT-HOME09    generic
    Click Person Profile Button
    Verify Navigation To Login Page

AUT-WT-HOME10: Verify guest user can return to the Home page after navigating to the login page
    [Tags]    WT-HOME10    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Go To Url    ${EXPECTED_HOME_URL}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME11: Verify Customer signup button navigates guest user to the customer-search workflow
    [Tags]    WT-HOME11    generic
    Click Customer Signup Button
    Verify Navigation To Customer Search Page

AUT-WT-HOME12: Verify Clean survey button navigates guest user to the vehicle-survey workflow
    [Tags]    WT-HOME12    generic
    Click Clean Survey Button
    Verify Navigation To Vehicle Survey Page

AUT-WT-HOME13: Verify Site survey button navigates guest user to the survey workflow
    [Tags]    WT-HOME13    generic
    Click Site Survey Button
    Verify Navigation To Site Survey Page

AUT-WT-HOME14: Verify all primary guest navigation controls are simultaneously visible before interaction
    [Tags]    WT-HOME14    generic
    Verify Home Page Loaded In Guest State

AUT-WT-HOME15: Verify guest user remains on the Home page if login navigation does not complete successfully
    [Tags]    WT-HOME15    generic
    Click Person Profile Button
    Run Keyword If    '${EXPECTED_LOGIN_URL}' not in '${PAGE_URL}'    Verify Home Page Loaded In Guest State

AUT-WT-HOME16: Verify guest user remains on the Home page if customer-search navigation does not complete successfully
    [Tags]    WT-HOME16    generic
    Click Customer Signup Button
    Run Keyword If    '${EXPECTED_CUSTOMER_SEARCH_URL_FRAGMENT}' not in '${PAGE_URL}'    Verify Home Page Loaded In Guest State

AUT-WT-HOME17: Verify guest user remains on the Home page if vehicle-survey navigation does not complete successfully
    [Tags]    WT-HOME17    generic
    Click Clean Survey Button
    Run Keyword If    '${EXPECTED_VEHICLE_SURVEY_URL_FRAGMENT}' not in '${PAGE_URL}'    Verify Home Page Loaded In Guest State

AUT-WT-HOME18: Verify guest user remains on the Home page if survey navigation does not complete successfully
    [Tags]    WT-HOME18    generic
    Click Site Survey Button
    Run Keyword If    '${EXPECTED_SITE_SURVEY_URL_FRAGMENT}' not in '${PAGE_URL}'    Verify Home Page Loaded In Guest State
