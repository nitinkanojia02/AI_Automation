*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Test Setup    Run Keywords    Open Browser Session    AND    Open Home Page
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON01: Verify Home page loads successfully in guest state for an unauthenticated user
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON01    positive
    Verify Home Page Is Loaded
    Verify Home Page URL

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON02: Verify approved guest-state controls are visible enabled and focusable on initial Home page load
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON02    positive
    Verify Guest Home Controls Are Visible
    Verify Guest Home Controls Are Enabled
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON03: Verify Person Profile button opens the Login page from guest Home state
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON03    positive
    Click Person Profile Button
    Verify User Is Navigated To Login Page

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON04: Verify Person Profile button can be activated using keyboard interaction
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON04    edge
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Press Keys    ${PERSON_PROFILE_BUTTON}    ENTER
    Verify User Is Navigated To Login Page

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON05: Verify Customer signup button navigates to the customer-search page
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON05    positive
    Click Customer Signup Button
    Verify Customer Search Page Navigation

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON06: Verify Clean survey button navigates to the vehicle-survey page
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON06    positive
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON07: Verify Site survey button navigates to the survey page
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON07    positive
    Click Site Survey Button
    Verify Survey Page Navigation

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON08: Verify Customer signup button can be activated using keyboard interaction
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON08    edge
    Wait For Element To Be Ready    ${CUSTOMER_SIGNUP_BUTTON}
    Press Keys    ${CUSTOMER_SIGNUP_BUTTON}    ENTER
    Verify Customer Search Page Navigation

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON09: Verify Home button remains visible and enabled in guest state
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON09    positive
    Wait For Element To Be Ready    ${HOME_BUTTON}
    Click Home Button
    Verify Home Page Is Loaded
    Verify Home Page URL

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON10: Verify Back button remains visible and enabled in guest state
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON10    positive
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Element Should Be Visible    ${BACK_BUTTON}
    Element Should Be Enabled    ${BACK_BUTTON}

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON11: Verify Notification button remains visible and enabled in guest state
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON11    positive
    Wait For Element To Be Ready    ${NOTIFICATION_BUTTON}
    Element Should Be Visible    ${NOTIFICATION_BUTTON}
    Element Should Be Enabled    ${NOTIFICATION_BUTTON}

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON12: Verify guest Home page remains accessible through direct URL navigation
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON12    positive
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Verify Home Page URL

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON13: Verify guest Home page controls remain visible after returning from a guest-accessible feature page
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON13    edge
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Verify Guest Home Controls Are Visible
    Verify Guest Home Controls Are Enabled

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON14: Verify Person Profile button remains enabled after returning to Home from another guest-accessible page
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON14    edge
    Click Clean Survey Button
    Verify Vehicle Survey Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Wait For Element To Be Ready    ${PERSON_PROFILE_BUTTON}
    Click Person Profile Button
    Verify User Is Navigated To Login Page

AUT-WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON15: Verify guest-state controls do not become disabled after sequential navigation actions
    [Tags]    WT-HOMEPAGESHOULDSUPPORTGUESTSTATECONTROLSGUESTNAVIGATIONANDLOGINENTRYFROMTHEPERSONBUTTON15    edge
    Click Customer Signup Button
    Verify Customer Search Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Click Site Survey Button
    Verify Survey Page Navigation
    Go To Url    ${HOME_PAGE_URL}
    Verify Home Page Is Loaded
    Verify Guest Home Controls Are Visible
    Verify Guest Home Controls Are Enabled
