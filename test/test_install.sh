#!/bin/bash

function _test_commands() {
    RESULT=0  # success by default

    bloom-release --help || RESULT=1
    catkin --help || RESULT=1
    rosdep --help || RESULT=1
    wstool --help || RESULT=1
    return $RESULT
}

# Need to test https://github.com/130s/compenv_ubuntu/issues/3
function test_display_env() {
    #TODO
    return
}

function _test_systems() {

    _test_commands
    retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then echo "Error: not all commands are installed yet. Exiting.o"; exit 1; fi
    
    if [ ! -z $MSG_ENDROLL ]; then printf $MSG_ENDROLL; else echo "No accumulated error messages."; fi

    test_display_env
}

# Here's kindf of main function.
_test_systems
