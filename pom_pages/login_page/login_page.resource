*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${A_LINK}    xpath=//a
${CONTAINER_ELEMENT}    id=container

*** Keywords ***
Click A
    [Documentation]    Click action for A (link) using page object locator.
    Wait Until Element Is Visible    ${A_LINK}    10s
    Click Element    ${A_LINK}

Click Container
    [Documentation]    Click action for Container (element) using page object locator.
    Wait Until Element Is Visible    ${CONTAINER_ELEMENT}    10s
    Click Element    ${CONTAINER_ELEMENT}
