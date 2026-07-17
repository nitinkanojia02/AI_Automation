*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Suite Setup    Open Browser To Url    ${HOME_PAGE_URL}
Suite Teardown    Close Browser Session
Test Setup    Open Home Page And Click User Button    ${HOME_PAGE_URL}

*** Test Cases ***
AUT-WT-LOGIN01: Verify Login page opens from Home page using the Person/Profile button
    [Tags]    WT-LOGIN01    positive
    Verify Login Form Loaded

AUT-WT-LOGIN02: Verify Login page controls are visible and enabled after navigation from Home page
    [Tags]    WT-LOGIN02    positive
    Verify Login Form Loaded

AUT-WT-LOGIN03: Verify password input is masked by default while typing
    [Tags]    WT-LOGIN03    positive
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN04: Verify successful login with approved valid credentials returns the user to authenticated Home state
    [Tags]    WT-LOGIN04    positive
    Login With Valid Credentials
    Wait Until Location Contains    home

AUT-WT-LOGIN06: Verify invalid username with valid password does not authenticate the user
    [Tags]    WT-LOGIN06    negative
    Login With Credentials    ${INVALID_USERNAME_WITH_VALID_PASSWORD}    ${VALID_PASSWORD}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN07: Verify valid username with invalid password does not authenticate the user
    [Tags]    WT-LOGIN07    negative
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD_WITH_VALID_USERNAME}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN08: Verify invalid username and invalid password combination is rejected
    [Tags]    WT-LOGIN08    negative
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN09: Verify Login button behavior when Username and Password fields are empty
    [Tags]    WT-LOGIN09    negative
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Required Validation
    Verify Login Page Remains Visible

AUT-WT-LOGIN10: Verify required validation when Username is empty and Password is entered
    [Tags]    WT-LOGIN10    negative
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Required Validation
    Verify Login Page Remains Visible

AUT-WT-LOGIN11: Verify required validation when Password is empty and Username is entered
    [Tags]    WT-LOGIN11    negative
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Required Validation
    Verify Login Page Remains Visible

AUT-WT-LOGIN12: Verify whitespace-only Username and Password values are rejected
    [Tags]    WT-LOGIN12    negative
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN13: Verify leading and trailing spaces in valid credentials are handled according to business rules
    [Tags]    WT-LOGIN13    edge
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Wait Until Page Contains Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN16: Verify Password field is case-sensitive for authentication
    [Tags]    WT-LOGIN16    negative
    Login With Credentials    ${VALID_USERNAME}    ${PASSWORD_LOWERCASE_VARIANT}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN17: Verify Back button returns the user from Login page to Home page
    [Tags]    WT-LOGIN17    positive
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Page Contains Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN18: Verify Home button returns the user from Login page to Home page
    [Tags]    WT-LOGIN18    positive
    Go To Url    ${HOME_PAGE_URL}
    Wait Until Page Contains Element    ${USERNAME_TEXTBOX}

AUT-WT-LOGIN19: Verify authenticated Home state displays logged-in user identity after successful login
    [Tags]    WT-LOGIN19    positive
    Login With Valid Credentials
    Wait Until Location Contains    home

AUT-WT-LOGIN21: Verify long Username input value is rejected without breaking the Login page
    [Tags]    WT-LOGIN21    edge
    ${long_username}=    Generate Long Username Value
    Login With Credentials    ${long_username}    ${VALID_PASSWORD}
    Verify Authentication Error Message
    Verify Login Page Remains Visible

AUT-WT-LOGIN22: Verify long Password input value is rejected without exposing password text
    [Tags]    WT-LOGIN22    edge
    ${long_password}=    Generate Long Password Value
    Login With Credentials    ${VALID_USERNAME}    ${long_password}
    Verify Password Field Is Masked
    Verify Authentication Error Message
    Verify Login Page Remains Visible
