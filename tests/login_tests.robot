*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Resource    ../pom_pages/home_page/home_page.resource
Suite Setup    Open Browser To Url    ${HOME_PAGE_URL}
Test Setup    Go To Url    ${PAGE_URL}
Suite Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Open Login page from Home page guest state using person/profile button
    [Tags]    WT-LOGIN01    positive
    Verify Login Form Loaded

AUT-WT-LOGIN02: Validate Login page controls visibility and interaction state after opening from Home page
    [Tags]    WT-LOGIN02    positive
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${VALID_PASSWORD}
    Verify Login Form Loaded

AUT-WT-LOGIN03: Verify password input is masked during typing
    [Tags]    WT-LOGIN03    positive
    Verify Login Form Loaded
    Enter Password     ${VALID_PASSWORD}
    Verify Password Is Masked

AUT-WT-LOGIN04: Login successfully with approved credentials and return to authenticated Home page
    [Tags]    WT-LOGIN04    positive
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${VALID_PASSWORD}
    Click Login Button

AUT-WT-LOGIN05: Reject login with invalid username and invalid password
    [Tags]    WT-LOGIN05    negative
    Verify Login Form Loaded
    Enter Username     ${INVALID_USERNAME}
    Enter Password     ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN06: Reject login with blank username and blank password
    [Tags]    WT-LOGIN06    negative
    Verify Login Form Loaded
    Enter Username     ${EMPTY}
    Enter Password     ${EMPTY}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN07: Reject login with populated username and blank password
    [Tags]    WT-LOGIN07    negative
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${EMPTY}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN08: Reject login with blank username and populated password
    [Tags]    WT-LOGIN08    negative
    Verify Login Form Loaded
    Enter Username     ${EMPTY}
    Enter Password     ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN09: Verify all failed authentication attempts display the same generic Failed message
    [Tags]    WT-LOGIN09    negative
    Verify Login Form Loaded
    Enter Username     ${INVALID_USERNAME}
    Enter Password     ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Failed Message
    Verify Login Form Loaded
    Enter Username     ${EMPTY}
    Enter Password     ${EMPTY}
    Click Login Button
    Verify Authentication Failed Message
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${EMPTY}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN10: Return to Home page in unauthenticated state using Back button
    [Tags]    WT-LOGIN10    positive
    Verify Login Form Loaded
    Click Back Button

AUT-WT-LOGIN11: Return to Home page in unauthenticated state using Home button
    [Tags]    WT-LOGIN11    positive
    Verify Login Form Loaded
    Click Home Button

AUT-WT-LOGIN12: Validate login behavior with leading whitespace in username
    [Tags]    WT-LOGIN12    edge
    Verify Login Form Loaded
    Enter Username     ${SPACE}${VALID_USERNAME}
    Enter Password     ${VALID_PASSWORD}
    Click Login Button

AUT-WT-LOGIN13: Validate login behavior with trailing whitespace in username
    [Tags]    WT-LOGIN13    edge
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}${SPACE}
    Enter Password     ${VALID_PASSWORD}
    Click Login Button

AUT-WT-LOGIN14: Validate login behavior with leading whitespace in password
    [Tags]    WT-LOGIN14    edge
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${SPACE}${VALID_PASSWORD}
    Click Login Button

AUT-WT-LOGIN15: Validate login behavior with trailing whitespace in password
    [Tags]    WT-LOGIN15    edge
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${VALID_PASSWORD}${SPACE}
    Click Login Button

AUT-WT-LOGIN16: Validate whitespace-only submission in Username and Password fields
    [Tags]    WT-LOGIN16    negative
    Verify Login Form Loaded
    Enter Username     ${SPACE}
    Enter Password     ${SPACE}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN17: Verify invalid password with valid username does not authenticate user
    [Tags]    WT-LOGIN17    negative
    Verify Login Form Loaded
    Enter Username     ${VALID_USERNAME}
    Enter Password     ${INVALID_PASSWORD}
    Click Login Button
    Verify Authentication Failed Message

AUT-WT-LOGIN18: Verify invalid username with valid password does not authenticate user
    [Tags]    WT-LOGIN18    negative
    Verify Login Form Loaded
    Enter Username     ${ALTERNATE_INVALID_USERNAME}
    Enter Password     ${VALID_PASSWORD}
    Click Login Button
    Verify Authentication Failed Message
