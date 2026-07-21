*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Browser To Url    ${PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify guest user can directly access the Home page using the approved entry URL
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify all approved Home page navigation controls are enabled and interactive in guest state
    [Tags]    WT-HOME02    positive
    Verify Home Page Loaded In Guest State
    Verify All Home Navigation Controls Are Enabled

AUT-WT-HOME03: Verify Person/Profile button navigates guest user to the login page URL
    [Tags]    WT-HOME03    positive
    Verify Home Page Loaded In Guest State
    Click Person Button
    Verify Person Profile Navigation

AUT-WT-HOME04: Verify Customer signup button navigates guest user to the customer-search workflow entry URL
    [Tags]    WT-HOME04    positive
    Verify Home Page Loaded In Guest State
    Click Customer Signup Button
    Verify Customer Signup Navigation

AUT-WT-HOME05: Verify Clean survey button navigates guest user to the vehicle-survey workflow entry URL
    [Tags]    WT-HOME05    positive
    Verify Home Page Loaded In Guest State
    Click Clean Survey Button
    Verify Clean Survey Navigation

AUT-WT-HOME06: Verify Site survey button navigates guest user to the survey workflow entry URL
    [Tags]    WT-HOME06    positive
    Verify Home Page Loaded In Guest State
    Click Site Survey Button
    Verify Site Survey Navigation
