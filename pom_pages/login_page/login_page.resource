*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_HOME_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL_FRAGMENT}    /washtabui/login?data=undefined
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    invalidpassword
${INVALID_PASSWORD_ALT}    WrongPassword#1
${MIXED_CASE_USERNAME}    KrisAdmin
${FAILED_AUTHENTICATION_MESSAGE}    Failed
${USERNAME_FIELD}    xpath=//input[@placeholder='User Name']
${PASSWORD_FIELD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[normalize-space(.)='Login']
${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}    text=Failed
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${NOTIFICATION_BUTTON}    id=auto_notification_btn

*** Keywords ***
Enter Username
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_FIELD}    ${username}

Enter Password
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Perform Login
    [Arguments]    ${username}    ${password}
    Enter Username    ${username}
    Enter Password    ${password}
    Click Login Button

Verify Login Page Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Username Field Visible And Enabled
    Wait For Element To Be Ready    ${USERNAME_FIELD}

Verify Password Field Visible And Enabled
    Wait For Element To Be Ready    ${PASSWORD_FIELD}

Verify Login Button Visible And Enabled
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Verify Failed Authentication Message Displayed
    Wait Until Element Is Visible    ${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}
    Element Text Should Be    ${FAILED_AUTHENTICATION_MESSAGE_ELEMENT}    ${FAILED_AUTHENTICATION_MESSAGE}

Verify User Remains Unauthenticated On Login Failure
    Verify Failed Authentication Message Displayed
    Verify Login Page Loaded

Verify Password Field Is Masked
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    ${password_field_type}=    Get Element Attribute    ${PASSWORD_FIELD}    type
    Should Be Equal    ${password_field_type}    password
