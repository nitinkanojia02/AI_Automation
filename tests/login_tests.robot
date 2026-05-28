*** Settings ***
Resource         ../pom_pages/login_page/login_page.resource
Suite Setup     Open Browser To Page
Test Setup      Open Page
Suite Teardown    Close Browser

*** Test Cases ***
TC01 Verify login page loads successfully
    Enter User Name    test
    Enter Password    test
    Click Sign In Button

TC02 Verify successful login with valid username and password
    Enter User Name    haklarr
    Enter Password    Icstunnel1
    Click Sign In Button
    Location Should Contain    /home

TC03 Verify login fails with incorrect username and correct password
    Enter User Name    wronguser
    Enter Password    Icstunnel1
    Click Sign In Button

TC04 Verify login fails with correct username and incorrect password
    Enter User Name    haklarr
    Enter Password    WrongPass1
    Click Sign In Button

TC05 Verify login fails when both username and password are incorrect
    Enter User Name    invaliduser
    Enter Password    invalidpass
    Click Sign In Button

TC06 Verify login fails when username and password fields are blank
    Click Sign In Button

TC07 Verify login fails when username is blank and password is filled
    Enter Password    Icstunnel1
    Click Sign In Button

TC08 Verify login fails when password is blank and username is filled
    Enter User Name    haklarr
    Click Sign In Button

TC09 Verify username textbox accepts alphanumeric input
    Enter User Name    user123

TC10 Verify password textbox masks entered characters
    Enter Password    Icstunnel1

TC11 Verify login button is clickable
    Click Sign In Button

TC12 Verify error message appears in error message area on failed login
    Enter User Name    abc
    Enter Password    xyz
    Click Sign In Button

TC13 Verify login with username containing leading and trailing spaces
    Enter User Name      haklarr  
    Enter Password    Icstunnel1
    Click Sign In Button

TC14 Verify login with password containing leading and trailing spaces
    Enter User Name    haklarr
    Enter Password      Icstunnel1  
    Click Sign In Button

TC15 Verify login attempt with very long username input
    ${LONG_USER}=    Evaluate    "a"*200
    Enter User Name    ${LONG_USER}
    Enter Password    Icstunnel1
    Click Sign In Button

TC16 Verify login attempt with very long password input
    ${LONG_PASS}=    Evaluate    "b"*200
    Enter User Name    haklarr
    Enter Password    ${LONG_PASS}
    Click Sign In Button

TC17 Verify login fails when username contains only whitespace
    Enter User Name  ${SPACE}${SPACE}       
    Enter Password    Icstunnel1
    Click Sign In Button

TC18 Verify login fails when password contains only whitespace
    Enter User Name    haklarr
    Enter Password  ${SPACE}${SPACE}          
    Click Sign In Button

TC19 Verify login using copy paste for username and password
    Enter User Name    haklarr
    Enter Password    Icstunnel1
    Click Sign In Button
    Location Should Contain    /home

