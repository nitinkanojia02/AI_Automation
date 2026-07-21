*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify guest user can directly access the Home page using the approved entry URL
    [Tags]    WT-HOME01    positive
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled

AUT-WT-HOME02: Verify Person/Profile button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME02    positive
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Element Should Be Enabled    ${PERSON_PROFILE_BUTTON}

AUT-WT-HOME03: Verify Back button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME03    positive
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}

AUT-WT-HOME04: Verify Notification button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME04    positive
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}

AUT-WT-HOME05: Verify Home button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME05    positive
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Element Should Be Enabled    ${HOME_BUTTON}

AUT-WT-HOME06: Verify Customer signup button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME06    positive
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Element Should Be Enabled    ${CUSTOMER_SIGNUP_BUTTON}

AUT-WT-HOME07: Verify Clean survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME07    positive
    Wait For Element To Be Ready    ${CLEAN_SURVEY_BUTTON}
    Element Should Be Enabled    ${CLEAN_SURVEY_BUTTON}

AUT-WT-HOME08: Verify Site survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME08    positive
    Wait For Element To Be Ready    ${SITE_SURVEY_BUTTON}
    Element Should Be Enabled    ${SITE_SURVEY_BUTTON}

AUT-WT-HOME09: Verify clicking the Person/Profile button navigates guest user to the login URL
    [Tags]    WT-HOME09    positive
    Click Auto Person Btn Button
    Verify Navigation To Login Page

AUT-WT-HOME10: Verify clicking the Customer signup button navigates guest user to customer-search page
    [Tags]    WT-HOME10    positive
    Click Auto Btn Customer Signup Button
    Verify Navigation To Customer Search Page

AUT-WT-HOME11: Verify clicking the Clean survey button navigates guest user to vehicle-survey page
    [Tags]    WT-HOME11    positive
    Click Auto Btn Clean Survey Button
    Verify Navigation To Vehicle Survey Page

AUT-WT-HOME12: Verify clicking the Site survey button navigates guest user to survey page
    [Tags]    WT-HOME12    positive
    Click Auto Btn Site Survey Button
    Verify Navigation To Site Survey Page

AUT-WT-HOME13: Verify all approved Home page navigation controls are enabled and interactive before user interaction
    [Tags]    WT-HOME13    positive
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled

AUT-WT-HOME14: Verify Home button remains interactive and does not redirect away from the Home page unexpectedly
    [Tags]    WT-HOME14    positive
    Click Auto Home Btn Button
    Verify Home Page Remains In Guest State

AUT-WT-HOME15: Verify Back button interaction from initial Home page state does not break the guest Home workflow
    [Tags]    WT-HOME15    edge
    Click Auto Back Btn Button
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled

AUT-WT-HOME16: Verify Notification button interaction is accepted while user remains in guest-accessible workflow state
    [Tags]    WT-HOME16    edge
    Click Auto Notification Btn Button
    Verify Home Guest State Loaded
    Verify Guest State Controls Are Enabled
