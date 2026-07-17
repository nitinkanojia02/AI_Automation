*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser Session
Suite Teardown    Close Browser Session
Test Setup    Go To Url    http://localhost/washtabui/home

*** Test Cases ***
AUT-WT-LOGIN01: Verify unauthenticated guest user can open the Login page from the Home page person profile button
    [Tags]    WT-LOGIN01    positive
    Click When Ready    id=auto_person_btn
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after opening Login page from Home page
    [Tags]    WT-LOGIN02    positive
    Click When Ready    id=auto_person_btn
    Verify Login Form Loaded

AUT-WT-LOGIN03: Verify password input is masked while entering credentials on the Login page
    [Tags]    WT-LOGIN03    positive
    Click When Ready    id=auto_person_btn
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN04: Verify successful login using approved credentials returns the user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Click When Ready    id=auto_person_btn
    Login With Valid Credentials
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN05: Verify authenticated Home state is visible after successful login
    [Tags]    WT-LOGIN05    positive
    Click When Ready    id=auto_person_btn
    Login With Valid Credentials
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN06: Verify invalid username and password combination does not authenticate the user
    [Tags]    WT-LOGIN06    negative
    Click When Ready    id=auto_person_btn
    Login With Invalid Credentials
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN07: Verify login submission with both Username and Password fields empty displays generic Failed message only
    [Tags]    WT-LOGIN07    negative
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN08: Verify login submission with Username populated and Password empty fails authentication
    [Tags]    WT-LOGIN08    negative
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN09: Verify login submission with Password populated and Username empty fails authentication
    [Tags]    WT-LOGIN09    negative
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN10: Verify leading and trailing whitespace handling for Username and Password values
    [Tags]    WT-LOGIN10    edge
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Login PageRemains Visible

AUT-WT-LOGIN11: Verify whitespace only credential values are rejected with generic Failed message
    [Tags]    WT-LOGIN11    negative
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN12: Verify Back button returns the user from Login page to unauthenticated Home page
    [Tags]    WT-LOGIN12    positive
    Click When Ready    id=auto_person_btn
    Click Back Button
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN13: Verify Home button returns the user from Login page to unauthenticated Home page
    [Tags]    WT-LOGIN13    positive
    Click When Ready    id=auto_person_btn
    Click Home Button
    Wait Until Page Does Not Contain Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN14: Verify all authentication failures display the same generic Failed message
    [Tags]    WT-LOGIN14    negative
    Click When Ready    id=auto_person_btn
    Login With Invalid Credentials
    Verify Authentication Failed Message
    Verify Login Page Remains Visible
    Go To Url    http://localhost/washtabui/home
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible
    Go To Url    http://localhost/washtabui/home
    Click When Ready    id=auto_person_btn
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN20: Verify extremely long credential values are rejected without breaking Login page behavior
    [Tags]    WT-LOGIN20    edge
    Click When Ready    id=auto_person_btn
    ${long_username}=    Generate Long Username Value
    ${long_password}=    Generate Long Password Value
    Login With Credentials    ${long_username}    ${long_password}
    Verify Authentication Failed Message
    Verify Login Page Remains Visible
