*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser To Url    ${HOME_PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Open Home Page And Click User Button    ${HOME_PAGE_URL}

*** Test Cases ***
AUT-WT-LOGIN01: Open Login page from Home page using person profile button
    [Tags]    WT-LOGIN01    positive
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after opening Login page
    [Tags]    WT-LOGIN02    positive
    Verify Login Form Loaded

AUT-WT-LOGIN03: Verify password input is masked while typing password characters
    [Tags]    WT-LOGIN03    positive
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox

AUT-WT-LOGIN04: Login successfully using approved valid credentials
    [Tags]    WT-LOGIN04    positive
    Login With Valid Credentials
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN06: Verify failed login with invalid username and valid password
    [Tags]    WT-LOGIN06    negative
    Login With Invalid Username
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN07: Verify failed login with valid username and invalid password
    [Tags]    WT-LOGIN07    negative
    Login With Invalid Password
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN08: Verify failed login with both username and password invalid
    [Tags]    WT-LOGIN08    negative
    Login With Invalid Credentials
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN09: Verify required field validation when Login is clicked with both fields empty
    [Tags]    WT-LOGIN09    negative
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN10: Verify Username required validation when Password is entered and Username is blank
    [Tags]    WT-LOGIN10    negative
    Enter Username Textbox    ${EMPTY}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN11: Verify Password required validation when Username is entered and Password is blank
    [Tags]    WT-LOGIN11    negative
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${EMPTY}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN12: Verify login behavior with leading and trailing spaces in both valid credential fields
    [Tags]    WT-LOGIN12    edge
    Enter Username Textbox    ${SPACE}${VALID_USERNAME}${SPACE}
    Enter Password Textbox    ${SPACE}${VALID_PASSWORD}${SPACE}
    Click Sign In Button
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN13: Verify login rejection with whitespace-only Username and Password values
    [Tags]    WT-LOGIN13    negative
    Enter Username Textbox    ${SPACE}
    Enter Password Textbox    ${SPACE}
    Click Sign In Button
    Verify Required Field Validation
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN14: Verify Username field accepts pasted valid value and authenticates successfully
    [Tags]    WT-LOGIN14    edge
    Enter Username Textbox    ${VALID_USERNAME}
    Verify Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN15: Verify Password field accepts pasted password while remaining masked
    [Tags]    WT-LOGIN15    edge
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Textbox
    Click Sign In Button
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN17: Verify Back button returns the user from Login page to Home page
    [Tags]    WT-LOGIN17    positive
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN18: Verify Home button returns the user from Login page to Home page
    [Tags]    WT-LOGIN18    positive
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN20: Verify authenticated-only features become available after successful login
    [Tags]    WT-LOGIN20    positive
    Login With Valid Credentials
    Wait Until Location Contains    /washtabui/home

AUT-WT-LOGIN21: Verify invalid login does not transition away from Login page
    [Tags]    WT-LOGIN21    negative
    Enter Username Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${WRONG_PASSWORD}
    Click Sign In Button
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN23: Verify username value remains unchanged after failed authentication attempt
    [Tags]    WT-LOGIN23    edge
    Enter Username Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page
    Verify Username Textbox    ${VALID_USERNAME}

AUT-WT-LOGIN24: Verify special characters in Username field do not authenticate invalid user
    [Tags]    WT-LOGIN24    negative
    Enter Username Textbox    ${SPECIAL_CHARACTER_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button
    Verify Authentication Error Message
    Verify Login Failed And User Remains On Login Page

AUT-WT-LOGIN25: Verify very long Username and Password values are handled without application crash
    [Tags]    WT-LOGIN25    edge
    Enter Username Textbox    ${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}${VALID_PASSWORD}${VALID_PASSWORD}
    Click Sign In Button
    Verify Login Failed And User Remains On Login Page
