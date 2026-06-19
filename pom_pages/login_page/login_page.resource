*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${HOME_BUTTON}    xpath=//ion-fab-button[.//ion-icon[@aria-label='home'] or normalize-space(.)='home']
${ARROW_BACK_BUTTON}    xpath=//ion-fab-button[.//ion-icon[@aria-label='arrow back'] or normalize-space(.)='arrow back']
${USER_NAME_TEXTBOX}    xpath=//input[@name='ion-input-0']
${PASSWORD}    id=password
${PASSWORD_TEXTBOX}    xpath=//input[@name='ion-input-1']
${SIGN_IN_BUTTON}    xpath=//ion-button[normalize-space(.)='SIGN IN']
${VALID_USERNAME}    haklarr
${VALID_PASSWORD}    Icstunnel1

*** Keywords ***
Click Home Button
    Click When Ready    ${HOME_BUTTON}

Click Arrow Back Button
    Click When Ready    ${ARROW_BACK_BUTTON}

Enter User Name
    [Arguments]    ${text}
    Input Text When Ready    ${USER_NAME_TEXTBOX}    ${text}

Enter Password
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD}
    Input Password    ${PASSWORD}    ${password}

Enter Password Textbox
    [Arguments]    ${password}
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Input Password    ${PASSWORD_TEXTBOX}    ${password}

Click Sign In Button
    Click When Ready    ${SIGN_IN_BUTTON}

Verify Login Page Loaded
    Wait For Element To Be Ready    ${USER_NAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${SIGN_IN_BUTTON}

Verify Login Rejected
    Wait For Element To Be Ready    ${SIGN_IN_BUTTON}
    Element Should Be Visible    ${USER_NAME_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}

Verify Username Required Validation
    Wait For Element To Be Ready    ${USER_NAME_TEXTBOX}
    Element Should Be Visible    ${USER_NAME_TEXTBOX}

Verify Password Required Validation
    Wait For Element To Be Ready    ${PASSWORD_TEXTBOX}
    Element Should Be Visible    ${PASSWORD_TEXTBOX}
