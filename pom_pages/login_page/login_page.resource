*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${EXPECTED_HOME_URL}    http://localhost/washtabui/home
${EXPECTED_LOGIN_URL_FRAGMENT}    /washtabui/login
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPassword
${INVALID_PASSWORD_ALT}    WrongPassword#1
${MIXED_CASE_USERNAME}    KrisAdmin
${FAILED_AUTH_MESSAGE}    Failed
${PERSON_PROFILE_BUTTON}    id=auto_person_btn
${USERNAME_FIELD}    xpath=//input[@placeholder='User Name']
${PASSWORD_FIELD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[normalize-space(.)='Login']
${BACK_BUTTON}    id=auto_back_btn
${HOME_BUTTON}    id=auto_home_btn
${FAILED_AUTHENTICATION_MESSAGE}    text=Failed

*** Keywords ***
Enter Username
    [Arguments]    ${username}
    Input Text When Ready    ${USERNAME_FIELD}    ${username}

Enter Password
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Click Person Profile Button
    Click When Ready    ${PERSON_PROFILE_BUTTON}

Click Back Button
    Click When Ready    ${BACK_BUTTON}

Click Home Button
    Click When Ready    ${HOME_BUTTON}

Verify Login Page Controls Visible And Enabled
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
    Wait For Element To Be Ready    ${BACK_BUTTON}
    Wait For Element To Be Ready    ${HOME_BUTTON}

Verify Failed Authentication Message Displayed
    Wait Until Element Is Visible    ${FAILED_AUTHENTICATION_MESSAGE}
    Element Text Should Be    ${FAILED_AUTHENTICATION_MESSAGE}    ${FAILED_AUTH_MESSAGE}

Verify User Remains Unauthenticated On Login Failure
    Verify Failed Authentication Message Displayed
    Location Should Contain    ${EXPECTED_LOGIN_URL_FRAGMENT}

Verify Login Redirected To Authenticated Home Page
    Wait Until Location Contains    ${EXPECTED_HOME_URL}

Verify Password Field Is Masked
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Element Attribute Value Should Be    ${PASSWORD_FIELD}    type    password
