*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Verify Home Page Loaded In Guest State

*** Test Cases ***
AUT-WT-LOGIN01: Verify guest user can open the Login page from home_page using the person/profile button
    [Tags]    WT-LOGIN01    generic
    Verify Person Profile Button Visible And Enabled
    Click Person Profile Button
    Verify Navigation To Login Page
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']
    Wait Until Element Is Visible    id=password
    Wait Until Element Is Visible    id=auto_back_btn
    Wait Until Element Is Visible    id=auto_home_btn

AUT-WT-LOGIN02: Verify Login page controls are visible and interactable after navigation from home_page
    [Tags]    WT-LOGIN02    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']
    Wait Until Element Is Enabled    xpath=//input[@placeholder='User Name']
    Wait Until Element Is Visible    id=password
    Wait Until Element Is Enabled    id=password
    Wait Until Element Is Visible    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Enabled    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Verify Back Button Visible And Enabled
    Verify Home Button Visible And Enabled

AUT-WT-LOGIN03: Verify password input remains masked during credential entry
    [Tags]    WT-LOGIN03    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Password When Ready    id=password    Carwash#1
    ${password_type}=    Get Element Attribute    id=password    type
    Should Be Equal    ${password_type}    password

AUT-WT-LOGIN04: Verify successful authentication with approved credentials returns the user to authenticated home_page
    [Tags]    WT-LOGIN04    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    krisadmin
    Input Password When Ready    id=password    Carwash#1
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN05: Verify invalid username and invalid password display only the generic Failed authentication message
    [Tags]    WT-LOGIN05    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    invaliduser
    Input Password When Ready    id=password    InvalidPass123
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN06: Verify blank username and blank password submission displays only the generic Failed message
    [Tags]    WT-LOGIN06    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${EMPTY}
    Input Password When Ready    id=password    ${EMPTY}
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN07: Verify login attempt with populated username and blank password displays only the generic Failed message
    [Tags]    WT-LOGIN07    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    krisadmin
    Input Password When Ready    id=password    ${EMPTY}
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN08: Verify login attempt with blank username and populated password displays only the generic Failed message
    [Tags]    WT-LOGIN08    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${EMPTY}
    Input Password When Ready    id=password    Carwash#1
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN09: Verify login with valid username and incorrect password does not authenticate the user
    [Tags]    WT-LOGIN09    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    krisadmin
    Input Password When Ready    id=password    WrongPassword1
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN10: Verify login with incorrect username and valid password does not authenticate the user
    [Tags]    WT-LOGIN10    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    wronguser
    Input Password When Ready    id=password    Carwash#1
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN11: Verify leading whitespace in username credential is handled according to implemented application behavior
    [Tags]    WT-LOGIN11    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}krisadmin
    Input Password When Ready    id=password    Carwash#1
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Page Contains Element    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN12: Verify trailing whitespace in password credential is handled according to implemented application behavior
    [Tags]    WT-LOGIN12    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    krisadmin
    Input Password When Ready    id=password    Carwash#1${SPACE}
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Page Contains Element    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN13: Verify whitespace-only credentials do not authenticate the user
    [Tags]    WT-LOGIN13    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}
    Input Password When Ready    id=password    ${SPACE}
    Click When Ready    xpath=//ion-button[@text='Login' or normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN14: Verify Back button returns the user from Login page to home_page in guest state
    [Tags]    WT-LOGIN14    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Verify Back Button Visible And Enabled
    Click Back Button
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN15: Verify Home button returns the user from Login page to home_page in guest state
    [Tags]    WT-LOGIN15    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Verify Home Button Visible And Enabled
    Click Home Button
    Wait Until Location Is    ${EXPECTED_HOME_URL}
