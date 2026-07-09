*** Settings ***
Resource    ../resources/common_keywords.resource
Resource    ../pom_pages/login_page/login_page.resource
Test Teardown    Close Browser Session

*** Test Cases ***
AUT-WT-LOGIN01: Verify login page displays all required login controls and labels
    [Tags]    WT-LOGIN01    positive
    Open Login Page
    Verify Login Page Loaded

AUT-WT-LOGIN02: Verify successful login using valid username and valid password
    [Tags]    WT-LOGIN02    positive
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Successful Login

AUT-WT-LOGIN03: Verify successful login when credentials are pasted into the fields
    [Tags]    WT-LOGIN03    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Successful Login

AUT-WT-LOGIN04: Verify login can be submitted using Enter key from password field
    [Tags]    WT-LOGIN04    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Submit Login Form Using Enter Key
    Verify Successful Login

AUT-WT-LOGIN05: Verify login fails with invalid username and valid password
    [Tags]    WT-LOGIN05    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN06: Verify login fails with valid username and invalid password
    [Tags]    WT-LOGIN06    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN07: Verify login fails with both invalid username and invalid password
    [Tags]    WT-LOGIN07    negative
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME_ALT}    ${INVALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN08: Verify required validation when username and password fields are empty
    [Tags]    WT-LOGIN08    negative
    Open Login Page
    Enter Username    ${EMPTY}
    Enter Password    ${EMPTY}
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN09: Verify required validation when username is empty and password is entered
    [Tags]    WT-LOGIN09    negative
    Open Login Page
    Enter Username    ${EMPTY}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN10: Verify required validation when password is empty and username is entered
    [Tags]    WT-LOGIN10    negative
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${EMPTY}
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page

AUT-WT-LOGIN11: Verify login behavior with leading and trailing spaces in username field
    [Tags]    WT-LOGIN11    edge
    Open Login Page
    Login With Credentials    ${SPACE}${VALID_USERNAME}${SPACE}    ${VALID_PASSWORD}
    Verify Login Page Remains Accessible

AUT-WT-LOGIN12: Verify login fails when only whitespace is entered in username and password fields
    [Tags]    WT-LOGIN12    negative
    Open Login Page
    Login With Credentials    ${SPACE}    ${SPACE}
    Verify User Remains On Login Page
    Run Keyword And Ignore Error    Verify Required Field Message
    Run Keyword And Ignore Error    Verify Invalid Credentials Message

AUT-WT-LOGIN13: Verify password characters remain masked while typing
    [Tags]    WT-LOGIN13    positive
    Open Login Page
    Enter Password    ${VALID_PASSWORD}
    Verify Password Field Is Masked

AUT-WT-LOGIN14: Verify forgot password link navigates to password recovery page
    [Tags]    WT-LOGIN14    positive
    Open Login Page
    Click Forgot Password Link
    Verify Forgot Password Navigation

AUT-WT-LOGIN15: Verify keyboard Tab navigation moves focus through login controls in sequence
    [Tags]    WT-LOGIN15    edge
    Open Login Page
    Wait For Element To Be Ready    ${USERNAME_TEXTBOX}
    Press Keys    ${USERNAME_TEXTBOX}    TAB
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Press Keys    ${PASSWORD_TEXTBOX}    TAB
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Press Keys    ${LOGIN_BUTTON}    TAB
    Wait For Element To Be Ready    ${FORGOT_PASSWORD_LINK}

AUT-WT-LOGIN16: Verify login is case-sensitive for username credentials
    [Tags]    WT-LOGIN16    negative
    Open Login Page
    Login With Credentials    ${LOWERCASE_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN17: Verify login is case-sensitive for password credentials
    [Tags]    WT-LOGIN17    negative
    Open Login Page
    Login With Credentials    ${VALID_USERNAME}    ${UPPERCASE_PASSWORD}
    Verify Invalid Credentials Message
    Verify User Remains On Login Page

AUT-WT-LOGIN18: Verify login behavior with very long username and password values
    [Tags]    WT-LOGIN18    edge
    Open Login Page
    Login With Credentials    ${LONG_INPUT_TEXT}    ${LONG_INPUT_TEXT}
    Verify User Remains On Login Page
    Verify Login Page Remains Accessible

AUT-WT-LOGIN19: Verify login fails when special characters are entered in username and password fields
    [Tags]    WT-LOGIN19    negative
    Open Login Page
    Login With Credentials    ${SPECIAL_CHARACTERS_TEXT}    ${SPECIAL_CHARACTERS_TEXT}
    Verify User Remains On Login Page
    Run Keyword And Ignore Error    Verify Invalid Credentials Message

AUT-WT-LOGIN20: Verify repeated clicking on Login button with valid credentials does not create duplicate login actions
    [Tags]    WT-LOGIN20    edge
    Open Login Page
    Enter Username    ${VALID_USERNAME}
    Enter Password    ${VALID_PASSWORD}
    Click Login Button
    Run Keyword And Ignore Error    Click Login Button
    Run Keyword And Ignore Error    Click Login Button
    Verify Successful Login

AUT-WT-LOGIN21: Verify logout returns authenticated user back to login page
    [Tags]    WT-LOGIN21    positive
    Open Login Page
    Login With Valid Credentials
    Verify Successful Login

AUT-WT-LOGIN22: Verify invalid credential message disappears after successful login retry
    [Tags]    WT-LOGIN22    edge
    Open Login Page
    Login With Credentials    ${INVALID_USERNAME}    ${INVALID_PASSWORD}
    Verify Invalid Credentials Message
    Login With Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Verify Invalid Credentials Message Is Cleared
    Verify Successful Login

AUT-WT-LOGIN23: Verify browser refresh on login page retains stable login form state
    [Tags]    WT-LOGIN23    edge
    Open Login Page
    Reload Page
    Verify Login Page Loaded

AUT-WT-LOGIN24: Verify login button is clickable and responsive on page load
    [Tags]    WT-LOGIN24    positive
    Open Login Page
    Click Login Button
    Verify Required Field Message
    Verify User Remains On Login Page
