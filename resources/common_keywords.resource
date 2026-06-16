*** Settings ***
Library    SeleniumLibrary

*** Keywords ***
Open Browser To Url
    [Documentation]    Opens browser, maximizes window, and navigates to the provided URL.
    [Arguments]    ${url}    ${browser}=chrome
    Open Browser    about:blank    ${browser}
    Maximize Browser Window
    Go To    ${url}

Go To Url
    [Documentation]    Navigates the current browser session to the provided URL.
    [Arguments]    ${url}
    Go To    ${url}

Wait For Element To Be Ready
    [Documentation]    Waits until the provided locator is visible and enabled.
    [Arguments]    ${locator}    ${timeout}=10s
    Wait Until Element Is Visible    ${locator}    ${timeout}
    Wait Until Element Is Enabled    ${locator}    ${timeout}