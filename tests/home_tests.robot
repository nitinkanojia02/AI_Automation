*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Open Browser To Url    ${HOME_PAGE_URL}
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify home page loads with all approved navigation and action controls visible
    [Tags]    WT-LOGIN01    positive
    Wait Until Home Page Loads
    Verify Home Page Is Displayed
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN02: Verify clicking person navigation button redirects user to login page with expected URL
    [Tags]    WT-LOGIN02    positive
    Wait Until Home Page Loads
    Click Auto Person Btn Button
    Verify User Is On Login Page

AUT-WT-LOGIN03: Verify customer signup button navigates to customer-search page
    [Tags]    WT-LOGIN03    positive
    Wait Until Home Page Loads
    Click Auto Btn Customer Signup Button
    Wait Until Location Contains    customer-search    ${DEFAULT_TIMEOUT}

AUT-WT-LOGIN04: Verify clean survey button navigates to vehicle-survey page
    [Tags]    WT-LOGIN04    positive
    Wait Until Home Page Loads
    Click Auto Btn Clean Survey Button
    Wait Until Location Contains    vehicle-survey    ${DEFAULT_TIMEOUT}

AUT-WT-LOGIN05: Verify site survey button navigates to survey page
    [Tags]    WT-LOGIN05    positive
    Wait Until Home Page Loads
    Click Auto Btn Site Survey Button
    Wait Until Location Contains    survey    ${DEFAULT_TIMEOUT}

AUT-WT-LOGIN06: Verify home navigation link keeps user on the home page
    [Tags]    WT-LOGIN06    positive
    Wait Until Home Page Loads
    Click Auto Home Btn Button
    Verify Home Page Still Visible
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN07: Verify notification button responds to user interaction without UI failure
    [Tags]    WT-LOGIN07    positive
    Wait Until Home Page Loads
    Click Auto Notification Btn Button
    Verify Notification Button Is Functional
    Verify Home Page Controls Visible

AUT-WT-LOGIN08: Verify back navigation button behavior when no previous page exists
    [Tags]    WT-LOGIN08    edge
    Wait Until Home Page Loads
    Click Auto Back Btn Button
    Verify Home Page Controls Visible

AUT-WT-LOGIN09: Verify all approved controls are enabled and interactable
    [Tags]    WT-LOGIN09    positive
    Wait Until Home Page Loads
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN10: Verify browser refresh preserves visibility and functionality of home page controls
    [Tags]    WT-LOGIN10    positive
    Wait Until Home Page Loads
    Reload Page
    Wait Until Home Page Loads
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN11: Verify direct access to home page URL opens the expected landing page
    [Tags]    WT-LOGIN11    positive
    Open Home Page
    Wait Until Home Page Loads
    Verify Home Page Is Displayed

AUT-WT-LOGIN12: Verify home page layout remains usable after browser window resize
    [Tags]    WT-LOGIN12    edge
    Set Window Size    800    600
    Wait Until Home Page Loads
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN13: Verify browser back action returns user to home page after opening login page
    [Tags]    WT-LOGIN13    positive
    Wait Until Home Page Loads
    Click Auto Person Btn Button
    Verify User Is On Login Page
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Home Page Loads
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN14: Verify sequential navigation across multiple home page actions remains stable
    [Tags]    WT-LOGIN14    edge
    Wait Until Home Page Loads
    Click Auto Btn Customer Signup Button
    Wait Until Location Contains    customer-search    ${DEFAULT_TIMEOUT}
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Controls Visible
    Click Auto Btn Clean Survey Button
    Wait Until Location Contains    vehicle-survey    ${DEFAULT_TIMEOUT}
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Controls Visible
    Click Auto Btn Site Survey Button
    Wait Until Location Contains    survey    ${DEFAULT_TIMEOUT}
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Controls Visible
    Click Auto Person Btn Button
    Verify User Is On Login Page

AUT-WT-LOGIN15: Verify approved controls remain visible after navigating away and returning to the home page
    [Tags]    WT-LOGIN15    positive
    Wait Until Home Page Loads
    Click Auto Btn Customer Signup Button
    Wait Until Location Contains    customer-search    ${DEFAULT_TIMEOUT}
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Home Page Loads
    Verify Home Page Controls Are Interactable
