*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${LOGIN_PAGE_URL}    http://172.21.166.115/washtabui/login?data=undefined
${USER_NAME_TEXTBOX}    xpath=//input[@placeholder='User Name']
${PASSWORD_TEXTBOX}    xpath=//input[@placeholder='Password']
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']

${VALID_USERNAME}    haklarr
${VALID_PASSWORD}    Icstunnel1
${INVALID_USERNAME}    wronguser
${INVALID_PASSWORD}    wrongpass
${ANOTHER_INVALID_USERNAME}    invaliduser
${ANOTHER_INVALID_PASSWORD}    invalidpass
${ALPHANUMERIC_USERNAME}    user123
${SPECIAL_USERNAME}    @@@###
${SPECIAL_PASSWORD}    !@#$$%^
${UPPERCASE_USERNAME}    HAKLARR
${LOWERCASE_PASSWORD}    icstunnel1
${USERNAME_WITH_SPACES}     haklarr
${PASSWORD_WITH_SPACES}     Icstunnel1
${LONG_USERNAME}    verylongusernamethatexceedsnormallengthlimitsfortestingpurposes1234567890
${LONG_PASSWORD}    verylongpasswordthatexceedsnormallengthlimitsfortestingpurposes1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZ

*** Keywords ***
Enter User Name Textbox
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${USER_NAME_TEXTBOX}    10s
    Input Text    ${USER_NAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Input Text    ${PASSWORD_TEXTBOX}    ${text}

Click Sign In Button
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Click Element    ${SIGN_IN_BUTTON}

Enter Login Credentials
    [Arguments]    ${username}    ${password}
    Enter User Name Textbox    ${username}
    Enter Password Textbox    ${password}

Submit Login
    Click Sign In Button

Login With Credentials
    [Arguments]    ${username}    ${password}
    Enter Login Credentials    ${username}    ${password}
    Submit Login

Login With Valid Credentials
    Enter Login Credentials    ${VALID_USERNAME}    ${VALID_PASSWORD}
    Submit Login

Verify Login Page Loaded
    Wait Until Element Is Visible    ${USER_NAME_TEXTBOX}    10s
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Element Should Be Enabled    ${USER_NAME_TEXTBOX}
    Element Should Be Enabled    ${PASSWORD_TEXTBOX}

Verify Password Field Is Masked
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    ${type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${type}    password

Click Sign In Button Multiple Times
    [Arguments]    ${times}=3
    FOR    ${i}    IN RANGE    ${times}
        Click Sign In Button
    END
