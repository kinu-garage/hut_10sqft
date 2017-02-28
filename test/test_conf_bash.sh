#!/bin/sh

# Copyright 2017 Isaac I. Y. Saito.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

test_rm_dropbox_conflictfiles() {
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
    echo '[DEBUG] PATH='; echo $PATH
    rm_dropbox_conflictfiles.sh
    ls -l

    # Verify if files are moved.
    files_notremoved=`ls | wc -l | cut -f1 -d' '`
    if [ $files_notremoved != 1 ]; then RESULT=1; fi

    return $RESULT
}

_test_androidpic_mv() {
    RESULT=0  # success by default
    LIST_FILES_A=("aa.jpg" "bb.jpeg" "cc.png" "dd.mp4" "ee.mov")
    LIST_FILES_B=("ff.jpg" "g g.jpeg" "hh.mp4" "ii.mov")

    # Create folders to mimic real environment
    TARGET_FOLDER=`date -d "$D" '+%m'`;
    mkdir -p ~/data/Dropbox/Camera\ Uploads/ ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio ~/link/Current/"${TARGET_FOLDER}";
    # Populate dummy image files
    cd ~/data/Dropbox/Camera\ Uploads
    for file in "${LIST_FILES_A[@]}"; do touch "$file"; done  # $file needs to be surrounded by double-quote in order for a file name with spaces to be properly touched.
    cd ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio
    for file in "${LIST_FILES_B[@]}"; do touch "$file"; done

    androidpic_mv

    echo "*** Verifying if files are moved."
    cd ~/link/Current/"${TARGET_FOLDER}"
    echo "Files in the target folder:"; ls -al
    i=0
    # Combine 2 arrays of file names.
    # "g g.jpeg" needs to be renamed as "g_g.jpeg" due to the algorighm of androidpic_mv
    for elem in "${LIST_FILES_A[@]}"; do LIST_FILES_ALL[i++]=$elem; done
    for elem in "${LIST_FILES_B[@]}"; do
        if [ "$elem" = "g g.jpeg" ]; then elem="g_g.jpeg"; fi
        LIST_FILES_ALL[i++]=$elem
    done
    for f in "${LIST_FILES_ALL[@]}"; do
        if [ ! -e "$f" ]; then
            echo "[ERROR] $f is missing from the target folder."; ls -al $f; RESULT=1;
        else
            echo "[SUCCESS] $f is found at the target folder."; ls -al $f;
        fi
    done

    return $RESULT
}

test_replace_py(){
    RESULT=1  # failure by default
	
	DIR_TEST=/tmp/proovingground_of_mad_overlord/replace_py
	# Unlike test_util.py, this testcase will be run from the top directory
	# of the repo so we still need test folder's path passed. 
	mkdir -p $DIR_TEST && cp -R ./test/testdata1 $DIR_TEST
	cd $DIR_TEST
	
	# Command to be tested. Replace string "Isaac" with "Isao"
	replace_str Isaac Isao . *
	
	# Verify the command.
	# Success if "grep -i isaac" returns empty result. 
	if [[ $(grep -i -r isaac .) ]]; then $RESULT=0; else echo "[test_replace_py] Failed."; fi

    return $RESULT
}

#
# This function works as "main" so all testcases should be defined above here.
#
_test_systems() {

    test_rm_dropbox_conflictfiles
    _test_androidpic_mv
    #test_replace_py
    retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then echo "Error: not all commands are installed yet. Exiting."; exit 1; fi
    
    if [ ! -z $MSG_ENDROLL ]; then printf $MSG_ENDROLL; else echo "No accumulated error messages."; fi
}

# Here's kindf of main function.
_test_systems
