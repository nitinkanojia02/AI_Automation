*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Verify Home Page Loaded In Guest State

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page controls are visible and interactive after navigation from home_page
    [Tags]    WT-LOGIN01    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']
    Wait Until Element Is Enabled    xpath=//input[@placeholder='User Name']
    Wait Until Element Is Visible    id=password
    Wait Until Element Is Enabled    id=password
    Wait Until Element Is Visible    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Enabled    xpath=//ion-button[normalize-space(.)='Login']
    Verify Back Button Visible And Enabled
    Verify Home Button Visible And Enabled

AUT-WT-LOGIN02: Verify password input remains masked while typing credentials
    [Tags]    WT-LOGIN02    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    ${password_type}=    Get Element Attribute    id=password    type
    Should Be Equal    ${password_type}    password

AUT-WT-LOGIN03: Verify successful authentication using approved credentials returns the user to authenticated home_page
    [Tags]    WT-LOGIN03    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN04: Verify invalid username and invalid password display only the generic Failed message
    [Tags]    WT-LOGIN04    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${INVALID_USERNAME}
    Input Password When Ready    id=password    ${INVALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN05: Verify blank Username and blank Password submission displays only the generic Failed message
    [Tags]    WT-LOGIN05    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN06: Verify submission with only Username populated displays only the generic Failed message
    [Tags]    WT-LOGIN06    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN07: Verify submission with only Password populated displays only the generic Failed message
    [Tags]    WT-LOGIN07    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN08: Verify incorrect password for approved username does not authenticate the user
    [Tags]    WT-LOGIN08    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${INVALID_PASSWORD_FOR_VALID_USER}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN09: Verify leading whitespace in Username credential is observationally validated
    [Tags]    WT-LOGIN09    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN10: Verify trailing whitespace in Password credential is observationally validated
    [Tags]    WT-LOGIN10    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}${SPACE}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN11: Verify whitespace-only credential values do not authenticate the user
    [Tags]    WT-LOGIN11    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${SPACE}
    Input Password When Ready    id=password    ${SPACE}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed

AUT-WT-LOGIN12: Verify Back button returns the user to home_page without authentication
    [Tags]    WT-LOGIN12    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Verify Back Button Visible And Enabled
    Click Back Button
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN13: Verify Home button returns the user to home_page without authentication
    [Tags]    WT-LOGIN13    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Verify Home Button Visible And Enabled
    Click Home Button
    Wait Until Location Is    ${EXPECTED_HOME_URL}

AUT-WT-LOGIN14: Verify failed authentication does not expose authenticated user identity or authenticated-only features
    [Tags]    WT-LOGIN14    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${INVALID_USERNAME}
    Input Password When Ready    id=password    ${INVALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Element Is Visible    text=Failed
    Element Text Should Be    text=Failed    Failed
    Wait Until Element Is Visible    xpath=//input[@placeholder='User Name']

AUT-WT-LOGIN15: Verify Login button processes pasted approved credentials successfully
    [Tags]    WT-LOGIN15    generic
    Click Person Profile Button
    Verify Navigation To Login Page
    Input Text When Ready    xpath=//input[@placeholder='User Name']    ${VALID_USERNAME}
    Input Password When Ready    id=password    ${VALID_PASSWORD}
    Click When Ready    xpath=//ion-button[normalize-space(.)='Login']
    Wait Until Location Is    ${EXPECTED_HOME_URL}
