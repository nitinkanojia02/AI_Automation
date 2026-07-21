*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOME01: Verify Guest User Can Directly Access The Home Page Using The Approved Entry URL
    [Tags]    WT-HOME01    positive
    Verify Home Page Loaded In Guest State

AUT-WT-HOME02: Verify Person Profile Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME02    positive
    Verify Person Profile Button Is Visible And Enabled

AUT-WT-HOME03: Verify Back Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME03    positive
    Verify Back Button Is Visible And Enabled

AUT-WT-HOME04: Verify Notification Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME04    positive
    Verify Notification Button Is Visible And Enabled

AUT-WT-HOME05: Verify Home Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME05    positive
    Verify Home Button Is Visible And Enabled

AUT-WT-HOME06: Verify Customer Signup Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME06    positive
    Verify Customer Signup Button Is Visible And Enabled

AUT-WT-HOME07: Verify Clean Survey Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME07    positive
    Verify Clean Survey Button Is Visible And Enabled

AUT-WT-HOME08: Verify Site Survey Button Is Visible And Enabled On The Home Page In Guest State
    [Tags]    WT-HOME08    positive
    Verify Site Survey Button Is Visible And Enabled

AUT-WT-HOME09: Verify Selecting The Person Profile Button Navigates The Guest User To The Login Page URL
    [Tags]    WT-HOME09    positive
    Click Auto Person Btn Button
    Verify Navigation To Login Page

AUT-WT-HOME10: Verify Selecting The Customer Signup Button Navigates The Guest User To The Customer Search Workflow Entry URL
    [Tags]    WT-HOME10    positive
    Click Auto Btn Customer Signup Button
    Verify Navigation To Customer Search Page

AUT-WT-HOME11: Verify Selecting The Clean Survey Button Navigates The Guest User To The Vehicle Survey Workflow Entry URL
    [Tags]    WT-HOME11    positive
    Click Auto Btn Clean Survey Button
    Verify Navigation To Vehicle Survey Page

AUT-WT-HOME12: Verify Selecting The Site Survey Button Navigates The Guest User To The Survey Workflow Entry URL
    [Tags]    WT-HOME12    positive
    Click Auto Btn Site Survey Button
    Verify Navigation To Site Survey Page
