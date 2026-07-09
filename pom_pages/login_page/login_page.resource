*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${USERNAME_TEXTBOX}    xpath=//input[@name='username']
${PASSWORD}    xpath=//input[@name='password']
${LOGIN_BUTTON}    xpath=//button[normalize-space(.)='Login']
${ORANGE_HRM_INC_LINK}    xpath=//a[normalize-space(.)='OrangeHRM, Inc']

*** Keywords ***
Enter Username
    [Documentation]    Enter text action for Username (textbox) using page object locator.
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${USERNAME_TEXTBOX}    10s
    Input Text    ${USERNAME_TEXTBOX}    ${text}

Enter Input
    [Documentation]    Enter password action for Input (password) using page object locator.
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD}    10s
    Input Password    ${PASSWORD}    ${password}

Click Login Button
    [Documentation]    Click action for Login Button (button) using page object locator.
    Wait Until Element Is Visible    ${LOGIN_BUTTON}    10s
    Click Element    ${LOGIN_BUTTON}

Click Orange Hrm Inc
    [Documentation]    Click action for Orange Hrm Inc (link) using page object locator.
    Wait Until Element Is Visible    ${ORANGE_HRM_INC_LINK}    10s
    Click Element    ${ORANGE_HRM_INC_LINK}
