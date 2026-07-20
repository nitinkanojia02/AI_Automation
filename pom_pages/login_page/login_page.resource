*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USER_NAME_TEXTBOX}    id=ion-input-0
${PASSWORD_TEXTBOX}    id=ion-input-1
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${VALID_USERNAME}    krisadmin
${VALID_PASSWORD}    Carwash#1
${INVALID_USERNAME}    invaliduser
${INVALID_PASSWORD}    InvalidPass#1
${UPPERCASE_USERNAME}    KRISADMIN
${SPECIAL_CHARACTER_USERNAME}    user!@#
${SPECIAL_CHARACTER_PASSWORD}    pass!@#
${GENERIC_FAILED_MESSAGE}    Failed

*** Keywords ***
Enter User Name Textbox
    [Arguments]    ${text}
    Input Text When Ready    ${USER_NAME_TEXTBOX}    ${text}

Enter Password Textbox
    [Arguments]    ${password}
    Input Password When Ready    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Login Form Loaded
    Wait For Element To Be Ready    ${USER_NAME_TEXTBOX}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}

Verify Password Textbox
    ${password_type}=    Get Element Attribute    ${PASSWORD_TEXTBOX}    type
    Should Be Equal    ${password_type}    password

Login With Valid Credentials
    Enter User Name Textbox    ${VALID_USERNAME}
    Enter Password Textbox    ${VALID_PASSWORD}
    Click Sign In Button

Login With Invalid Credentials
    Enter User Name Textbox    ${INVALID_USERNAME}
    Enter Password Textbox    ${INVALID_PASSWORD}
    Click Sign In Button
