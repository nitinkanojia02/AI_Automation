*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${LOGIN_PAGE_URL}    http://localhost/washtabui/home
${LOGIN_PAGE_IDENTIFIER}    login
${AUTHENTICATED_HOME_STATE_IDENTIFIER}    home
${USERNAME_FIELD}    id=ion-input-0
${PASSWORD_FIELD}    id=ion-input-1
${LOGIN_BUTTON}    xpath=//ion-button[contains(normalize-space(.),'SIGN IN') or contains(normalize-space(.),'Login')]
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass#1
${UPPERCASE_USERNAME}    KRISADMIN
${UPPERCASE_PASSWORD}    CARWASH#1
${FAILED_AUTHENTICATION_MESSAGE}    Failed

*** Keywords ***
Enter Username Field
    [Arguments]    ${text}
    Input Text When Ready    ${USERNAME_FIELD}    ${text}

Enter Password Field
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_FIELD}    ${password}

Click Login Button
    Click When Ready    ${LOGIN_BUTTON}

Verify Login Form Loaded
    Wait For Element To Be Ready    ${USERNAME_FIELD}
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    Wait For Element To Be Ready    ${LOGIN_BUTTON}

Verify Password Field
    Wait For Element To Be Ready    ${PASSWORD_FIELD}
    ${password_field_type}=    Get Element Attribute    ${PASSWORD_FIELD}    type
    Should Be Equal    ${password_field_type}    password

Verify Generic Failed Authentication Message
    Page Should Contain    ${FAILED_AUTHENTICATION_MESSAGE}

Verify Login Failed And User Remains Unauthenticated
    Verify Generic Failed Authentication Message
    Wait For Element To Be Ready    ${LOGIN_BUTTON}
