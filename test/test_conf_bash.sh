#!/bin/bash

function _test_commands() {
    RESULT=0  # success by default

    bloom-release --help || RESULT=1
    catkin --help || RESULT=1
    rosdep --help || RESULT=1
    wstool --help || RESULT=1
    return $RESULT
}

function test_rm_dropbox_conflictfiles() {
    RESULT=0  # success by default
    LIST_FILES_A=("aa.jpg"
"bb (Case Conflict).png"
"cc (conflicted copy).png")

    # Create a dummy folder to mimic real environment
    FOLDER_TEST=~/data/Dropbox/tmp;
    mkdir -p $FOLDER_TEST && cd $FOLDER_TEST
    # Populate dummy image files
    for f in "${LIST_FILES_A[@]}";  # http://stackoverflow.com/questions/9084257/bash-array-with-spaces-in-elements
    do
        touch "$f"
    done

    # Run the target script.
    rm_dropbox_conflictfiles.bash
    ls -l

    # Verify if files are moved.
    files_notremoved=`ls | wc -l | cut -f1 -d' '`
    if [ $files_notremoved != 1 ]; then RESULT=1; fi

    return $RESULT
}

function _test_systems() {

    _test_commands
    retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then echo "Error: not all commands are installed yet. Exiting.o"; exit 1; fi
    
    if [ ! -z $MSG_ENDROLL ]; then printf $MSG_ENDROLL; else echo "Script ends."; fi

    test_rm_dropbox_conflictfiles
}

# Here's kindf of main function.
_test_systems
