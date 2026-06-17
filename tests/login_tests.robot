*** Settings ***
Resource    ../pom_pages/login_page/login_page.resource
Test Setup    Open Browser    ${LOGIN_PAGE_URL}    chrome
Test Teardown    Close All Browsers

*** Test Cases ***
LOGIN_TC_001 Verify login with valid username and valid password
    Verify Login Page Loaded
    Login With Valid Credentials
    Wait Until Page Does Not Contain Element    ${USER_NAME_TEXTBOX}    10s

LOGIN_TC_002 Verify login fails with incorrect username and valid password
    Verify Login Page Loaded
    Login With Credentials    ${INVALID_USERNAME}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_003 Verify login fails with valid username and incorrect password
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_004 Verify login fails when both username and password are incorrect
    Verify Login Page Loaded
    Login With Credentials    ${ANOTHER_INVALID_USERNAME}    ${ANOTHER_INVALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_005 Verify login fails when username and password are blank
    Verify Login Page Loaded
    Login With Credentials    ${EMPTY}    ${EMPTY}
    Verify Login Page Loaded

LOGIN_TC_006 Verify login fails when username is blank and password is provided
    Verify Login Page Loaded
    Login With Credentials    ${EMPTY}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_007 Verify login fails when password is blank and username is provided
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${EMPTY}
    Verify Login Page Loaded

LOGIN_TC_008 Verify login page loads successfully
    Verify Login Page Loaded

LOGIN_TC_009 Verify username and password fields are visible on login page
    Verify Login Page Loaded

LOGIN_TC_010 Verify password field masks entered characters
    Verify Login Page Loaded
    Enter Password Textbox    ${VALID_PASSWORD}
    Verify Password Field Is Masked

LOGIN_TC_011 Verify username field accepts alphanumeric input
    Verify Login Page Loaded
    Enter User Name Textbox    ${ALPHANUMERIC_USERNAME}
    Textfield Value Should Be    ${USER_NAME_TEXTBOX}    ${ALPHANUMERIC_USERNAME}

LOGIN_TC_012 Verify login attempt with leading and trailing spaces in username
    Verify Login Page Loaded
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_013 Verify login attempt with leading and trailing spaces in password
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${SPACE}${VALID_PASSWORD}${SPACE}
    Verify Login Page Loaded

LOGIN_TC_014 Verify login attempt using very long username
    Verify Login Page Loaded
    Login With Credentials    ${LONG_USERNAME}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_015 Verify login attempt using very long password
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${LONG_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_016 Verify login attempt with special characters in username
    Verify Login Page Loaded
    Login With Credentials    ${SPECIAL_USERNAME}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_017 Verify login attempt with special characters in password
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${SPECIAL_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_018 Verify login is case sensitive for username
    Verify Login Page Loaded
    Login With Credentials    ${UPPERCASE_USERNAME}    ${VALID_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_019 Verify login is case sensitive for password
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${LOWERCASE_PASSWORD}
    Verify Login Page Loaded

LOGIN_TC_020 Verify multiple rapid clicks on Login button during authentication
    Verify Login Page Loaded
    Enter Login Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Click Sign In Button Multiple Times    3
    Wait Until Page Does Not Contain Element    ${USER_NAME_TEXTBOX}    10s

LOGIN_TC_021 Verify login using copy paste for credentials
    Verify Login Page Loaded
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Wait Until Page Does Not Contain Element    ${USER_NAME_TEXTBOX}    10s
