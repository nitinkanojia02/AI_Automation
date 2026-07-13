*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify all approved navigation buttons and action buttons are visible on the home page
    [Tags]    WT-LOGIN01    positive
    Open Home Page In Browser
    Verify Home Page Is Loaded
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN02: Verify clicking the person button navigates the user to the login page with expected URL
    [Tags]    WT-LOGIN02    positive
    Open Home Page In Browser
    Click Person Button
    Verify User Is Navigated To Login Page

AUT-WT-LOGIN03: Verify customer signup button opens the customer-search page
    [Tags]    WT-LOGIN03    positive
    Open Home Page In Browser
    Click Customer Signup Button
    Verify Customer Search Page Navigation

AUT-WT-LOGIN04: Verify clean survey button opens the vehicle-survey page
    [Tags]    WT-LOGIN04    positive
    Open Home Page In Browser
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation

AUT-WT-LOGIN05: Verify site survey button opens the survey page
    [Tags]    WT-LOGIN05    positive
    Open Home Page In Browser
    Click Site Survey Button
    Verify Survey Page Navigation

AUT-WT-LOGIN06: Verify home button remains functional when clicked from the home page
    [Tags]    WT-LOGIN06    positive
    Open Home Page In Browser
    Click Home Button
    Verify Home Page Is Loaded
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN07: Verify notification button accepts click interaction without application failure
    [Tags]    WT-LOGIN07    positive
    Open Home Page In Browser
    Click Notification Button
    Verify Notification Button Is Functional
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN08: Verify back button responds to user interaction on the home page
    [Tags]    WT-LOGIN08    positive
    Open Home Page In Browser
    Click Back Button
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN09: Verify home page remains usable after browser back navigation
    [Tags]    WT-LOGIN09    edge
    Open Home Page In Browser
    Click Customer Signup Button
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN10: Verify refreshing the home page preserves approved controls and layout
    [Tags]    WT-LOGIN10    edge
    Open Home Page In Browser
    Reload Page
    Verify Home Page Is Loaded
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN11: Verify user remains on the home page when no action is performed
    [Tags]    WT-LOGIN11    negative
    Open Home Page In Browser
    Sleep    3s
    Verify Home Page Is Loaded
    Verify Home Page Controls Are Visible

AUT-WT-LOGIN12: Verify approved controls remain clickable after page refresh
    [Tags]    WT-LOGIN12    edge
    Open Home Page In Browser
    Reload Page
    Verify Home Page Is Loaded
    Click Person Button
    Verify User Is Navigated To Login Page
