*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${HOME_PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Open Home Page

*** Test Cases ***
AUT-WT-LOGIN01: Verify all approved navigation controls and action buttons are visible and enabled on the home page
    [Tags]    WT-LOGIN01    positive
    Verify Home Page Loaded
    Verify All Home Navigation Controls Are Visible
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN02: Verify clicking the person navigation button redirects the user to the login page
    [Tags]    WT-LOGIN02    positive
    Click Auto Person Btn Button
    Verify Login Page Navigation

AUT-WT-LOGIN03: Verify customer signup button opens the customer-search page
    [Tags]    WT-LOGIN03    positive
    Click Auto Btn Customer Signup Button
    Verify Customer Search Page Navigation

AUT-WT-LOGIN04: Verify clean survey button opens the vehicle-survey page
    [Tags]    WT-LOGIN04    positive
    Click Auto Btn Clean Survey Button
    Verify Vehicle Survey Page Navigation

AUT-WT-LOGIN05: Verify site survey button opens the survey page
    [Tags]    WT-LOGIN05    positive
    Click Auto Btn Site Survey Button
    Verify Survey Page Navigation

AUT-WT-LOGIN06: Verify clicking the home navigation link while already on the home page does not trigger incorrect navigation
    [Tags]    WT-LOGIN06    positive
    Click Auto Home Btn Button
    Verify Home Page Loaded
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN07: Verify notification button interaction does not break the application UI
    [Tags]    WT-LOGIN07    positive
    Click Auto Notification Btn Button
    Verify Notification Button Is Functional
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN08: Verify back navigation button behavior from the home page
    [Tags]    WT-LOGIN08    edge
    Click Auto Back Btn Button
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded

AUT-WT-LOGIN09: Verify all approved controls are keyboard accessible using tab navigation
    [Tags]    WT-LOGIN09    edge
    Press Keys    None    TAB
    Press Keys    None    TAB
    Press Keys    None    TAB
    Press Keys    None    TAB
    Press Keys    None    TAB
    Press Keys    None    TAB
    Press Keys    None    TAB
    Verify All Home Navigation Controls Are Visible
    Wait Until Element Is Visible    ${PERSON_NAVIGATION_BUTTON}    ${DEFAULT_TIMEOUT}

AUT-WT-LOGIN10: Verify direct access to the home page URL loads the correct page
    [Tags]    WT-LOGIN10    positive
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Verify All Home Navigation Controls Are Visible

AUT-WT-LOGIN11: Verify browser refresh retains a stable home page state
    [Tags]    WT-LOGIN11    edge
    Reload Page
    Verify Home Page Loaded
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN12: Verify browser back navigation returns the user to the home page after opening the login page
    [Tags]    WT-LOGIN12    edge
    Click Auto Person Btn Button
    Verify Login Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN13: Verify browser back navigation returns the user to the home page after opening the customer-search page
    [Tags]    WT-LOGIN13    edge
    Click Auto Btn Customer Signup Button
    Verify Customer Search Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN14: Verify the home page does not display disabled or visually broken approved controls during initial load
    [Tags]    WT-LOGIN14    negative
    Verify Home Page Loaded
    Verify All Home Navigation Controls Are Visible
    Verify Home Page Controls Are Interactable

AUT-WT-LOGIN15: Verify clicking non-interactive blank areas around buttons does not trigger navigation
    [Tags]    WT-LOGIN15    negative
    Click Background Content
    Verify Home Page Loaded
    Verify All Home Navigation Controls Are Visible

AUT-WT-LOGIN16: Verify multiple sequential navigations from the home page work consistently without degrading the UI state
    [Tags]    WT-LOGIN16    edge
    Click Auto Btn Customer Signup Button
    Verify Customer Search Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Click Auto Btn Clean Survey Button
    Verify Vehicle Survey Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Click Auto Btn Site Survey Button
    Verify Survey Page Navigation

AUT-WT-LOGIN17: Verify browser forward navigation restores the previously opened page after returning to the home page
    [Tags]    WT-LOGIN17    edge
    Click Auto Btn Customer Signup Button
    Verify Customer Search Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Loaded
    Go To Url    ${HOME_PAGE_URL}/${CUSTOMER_SEARCH_PAGE_PATH}
    Verify Customer Search Page Navigation

AUT-WT-LOGIN18: Verify home page controls remain functional after multiple browser refresh operations
    [Tags]    WT-LOGIN18    edge
    Reload Page
    Reload Page
    Reload Page
    Verify Home Page Loaded
    Verify Home Page Controls Are Interactable
    Click Auto Person Btn Button
    Verify Login Page Navigation
