*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Browser To Url    ${PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Home page loads successfully in guest state using the approved entry URL
    [Tags]    WT-HOME01    generic
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify Person/Profile button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME02    generic
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME03: Verify Back button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME03    generic
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME04: Verify Notification button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME04    generic
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME05: Verify Home button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME05    generic
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME06: Verify Customer signup button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME06    generic
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME07: Verify Clean survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME07    generic
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME08: Verify Site survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME08    generic
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME09: Verify navigation to login page from the Person/Profile button
    [Tags]    WT-HOME09    generic
    Click Person Profile Button
    Verify Person Profile Navigation Redirect

AUT-WT-HOME10: Verify navigation to customer-search workflow from the Customer signup button
    [Tags]    WT-HOME10    generic
    Click Customer Signup Button
    Verify Customer Signup Navigation Redirect

AUT-WT-HOME11: Verify navigation to vehicle-survey workflow from the Clean survey button
    [Tags]    WT-HOME11    generic
    Click Clean Survey Button
    Verify Clean Survey Navigation Redirect

AUT-WT-HOME12: Verify navigation to survey workflow from the Site survey button
    [Tags]    WT-HOME12    generic
    Click Site Survey Button
    Verify Site Survey Navigation Redirect

AUT-WT-HOME13: Verify Home button interaction does not break guest-state Home page accessibility
    [Tags]    WT-HOME13    generic
    Click Home Button
    Verify Home Page Loaded In Guest State

AUT-WT-HOME14: Verify Back button interaction does not remove access to the Home page in guest state
    [Tags]    WT-HOME14    generic
    Click Back Button
    Go To Url    ${PAGE_URL}
    Verify Home Page Loaded In Guest State

AUT-WT-HOME15: Verify Notification button interaction is accessible from the Home page in guest state
    [Tags]    WT-HOME15    generic
    Click Notification Button
    Verify All Home Navigation Controls Are Enabled
