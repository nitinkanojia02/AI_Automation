*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Verify Home Page Loaded In Guest State

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page controls are visible and enabled after navigation from home_page
    [Tags]    WT-LOGIN01    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Wait For Element To Be Ready    xpath=//input[@placeholder='User Name']
    Wait For Element To Be Ready    id=password
    Wait For Element To Be Ready    xpath=//ion-button[normalize-space(.)='Login']
    Verify Back Button Visible And Enabled
    Verify Home Button Visible And Enabled

AUT-WT-LOGIN02: Verify password field masks characters during manual entry
    [Tags]    WT-LOGIN02    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    ${password_field_type}=    Get Element Attribute    id=password    type
    Should Be Equal    ${password_field_type}    password

AUT-WT-LOGIN03: Verify successful authentication using approved credentials returns the user to authenticated home_page
    [Tags]    WT-LOGIN03    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN04: Verify invalid username with valid password displays only the generic Failed message
    [Tags]    WT-LOGIN04    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${INVALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN05: Verify valid username with invalid password displays only the generic Failed message
    [Tags]    WT-LOGIN05    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${INVALID_PASSWORD_ALT}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN06: Verify invalid username and invalid password combination does not authenticate the user
    [Tags]    WT-LOGIN06    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${INVALID_USERNAME}
    Input Password When Ready    id=password    ${INVALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN07: Verify blank Username and blank Password submission displays only the generic Failed message
    [Tags]    WT-LOGIN07    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${EMPTY}
    Input Password When Ready    id=password    ${EMPTY}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN08: Verify blank Username with populated Password displays only the generic Failed message
    [Tags]    WT-LOGIN08    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${EMPTY}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN09: Verify populated Username with blank Password displays only the generic Failed message
    [Tags]    WT-LOGIN09    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${EMPTY}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN10: Verify leading whitespace in Username credential submission follows implemented application behavior
    [Tags]    WT-LOGIN10    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN11: Verify trailing whitespace in Password credential submission follows implemented application behavior
    [Tags]    WT-LOGIN11    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}${SPACE}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN12: Verify whitespace-only credential submission does not authenticate the user
    [Tags]    WT-LOGIN12    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}
    Input Password When Ready    id=password    ${SPACE}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN13: Verify Back button returns the user from Login page to unauthenticated home_page
    [Tags]    WT-LOGIN13    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Click Back Button

AUT-WT-LOGIN14: Verify Home button returns the user from Login page to unauthenticated home_page
    [Tags]    WT-LOGIN14    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Click Home Button
