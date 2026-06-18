*** Settings ***
Library    SeleniumLibrary

*** Variables ***

*** Keywords ***
Open Page
    [Documentation]    Navigates current browser session to page URL.
    Go To    http://172.21.166.115/washtabui/home

Open Browser To Page
    [Documentation]    Opens browser, maximizes window, and navigates to page URL.
    [Arguments]    ${browser}=chrome
    Open Browser    about:blank    ${browser}
    Maximize Browser Window
    Open Page
