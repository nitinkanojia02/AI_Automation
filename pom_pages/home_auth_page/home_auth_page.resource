*** Settings ***
Resource    ../../resources/common_keywords.resource

*** Variables ***
${PAGE_URL}    http://localhost/
${A_LINK}    xpath=//a
${CONTAINER_ELEMENT}    id=container

*** Keywords ***
Click A
    Wait Until Element Is Visible    ${A_LINK}
    Click Element    ${A_LINK}

Container
    Wait Until Element Is Visible    ${CONTAINER_ELEMENT}
    Click Element    ${CONTAINER_ELEMENT}
