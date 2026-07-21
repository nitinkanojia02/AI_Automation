*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/washtabui/home
${USER_NAME_TEXTBOX}    id=ion-input-0
${ION_INPUT_1_PASSWORD}    id=ion-input-1
${AUTO_BACK_BTN_BUTTON}    id=auto_back_btn
${AUTO_HOME_BTN_BUTTON}    id=auto_home_btn
${PASSWORD}    id=password
${LOGIN_BUTTON}    xpath=//ion-button[normalize-space(.)='[BTN_LOGIN]']
${BACKGROUND_CONTENT_ELEMENT}    id=background-content

*** Keywords ***
Enter User Name
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${USER_NAME_TEXTBOX}
    Input Text    ${USER_NAME_TEXTBOX}    ${text}

Enter Ion Input 1
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${ION_INPUT_1_PASSWORD}
    Input Password    ${ION_INPUT_1_PASSWORD}    ${password}

Click Auto Back Btn Button
    Wait Until Element Is Visible    ${AUTO_BACK_BTN_BUTTON}
    Click Element    ${AUTO_BACK_BTN_BUTTON}

Click Auto Home Btn Button
    Wait Until Element Is Visible    ${AUTO_HOME_BTN_BUTTON}
    Click Element    ${AUTO_HOME_BTN_BUTTON}

Enter Ion Input
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD}
    Input Password    ${PASSWORD}    ${password}

Click Login Button
    Wait Until Element Is Visible    ${LOGIN_BUTTON}
    Click Element    ${LOGIN_BUTTON}

Background Content
    Wait Until Element Is Visible    ${BACKGROUND_CONTENT_ELEMENT}
    Click Element    ${BACKGROUND_CONTENT_ELEMENT}
