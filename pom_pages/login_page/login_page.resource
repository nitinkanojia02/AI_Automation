*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${USER_NAME_TEXTBOX}    xpath=//input[@name='ion-input-0']
${PASSWORD_TEXTBOX}    xpath=//input[@name='ion-input-1']
${SIGN_IN_BUTTON}    xpath=//ion-button[@text='Login']

*** Keywords ***
Open Page
    [Documentation]    Navigates current browser session to page URL.
    Go To    http://172.21.166.115/washtabui/login?data=undefined

Open Browser To Page
    [Documentation]    Opens browser, maximizes window, and navigates to page URL.
    [Arguments]    ${browser}=chrome
    Open Browser    about:blank    ${browser}
    Maximize Browser Window
    Open Page

Enter User Name
    [Documentation]    Enter text action for User Name (textbox) using page object locator.
    [Arguments]    ${text}
    Wait Until Element Is Visible    ${USER_NAME_TEXTBOX}    10s
    Input Text    ${USER_NAME_TEXTBOX}    ${text}

Click Sign In Button
    [Documentation]    Click Sign In Button
    Wait Until Element Is Visible    ${SIGN_IN_BUTTON}    10s
    Click Button    ${SIGN_IN_BUTTON}

Enter Password
    [Documentation]    Enter password action for Password (password) using page object locator.
    [Arguments]    ${password}
    Wait Until Element Is Visible    ${PASSWORD_TEXTBOX}    10s
    Input Password    ${PASSWORD_TEXTBOX}    ${password}
