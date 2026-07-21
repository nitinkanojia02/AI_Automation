*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify guest user can directly access the Home page URL and Home page loads successfully
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State
    Verify All Home Navigation Buttons Are Visible And Enabled

AUT-WT-HOME02: Verify Person/Profile button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME02    positive
    Verify Person Profile Button Is Visible And Enabled

AUT-WT-HOME03: Verify Back button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME03    positive
    Verify Back Button Is Visible And Enabled

AUT-WT-HOME04: Verify Notification button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME04    positive
    Verify Notification Button Is Visible And Enabled

AUT-WT-HOME05: Verify Home button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME05    positive
    Verify Home Button Is Visible And Enabled

AUT-WT-HOME06: Verify Customer signup button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME06    positive
    Verify Customer Signup Button Is Visible And Enabled

AUT-WT-HOME07: Verify Clean survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME07    positive
    Verify Clean Survey Button Is Visible And Enabled

AUT-WT-HOME08: Verify Site survey button is visible and enabled on the Home page in guest state
    [Tags]    WT-HOME08    positive
    Verify Site Survey Button Is Visible And Enabled

AUT-WT-HOME09: Verify clicking the Person/Profile button navigates the guest user to the login page URL
    [Tags]    WT-HOME09    positive
    Click Auto Person Btn Button
    Verify Navigation To Login Page

AUT-WT-HOME10: Verify clicking the Customer signup button navigates the guest user to the customer-search workflow entry page
    [Tags]    WT-HOME10    positive
    Click Auto Btn Customer Signup Button
    Verify Navigation To Customer Search Page

AUT-WT-HOME11: Verify clicking the Clean survey button navigates the guest user to the vehicle-survey workflow entry page
    [Tags]    WT-HOME11    positive
    Click Auto Btn Clean Survey Button
    Verify Navigation To Vehicle Survey Page

AUT-WT-HOME12: Verify clicking the Site survey button navigates the guest user to the survey workflow entry page
    [Tags]    WT-HOME12    positive
    Click Auto Btn Site Survey Button
    Verify Navigation To Site Survey Page
