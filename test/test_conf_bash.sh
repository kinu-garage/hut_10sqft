#!/bin/bash

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

_test_rm_dropbox_conflictfiles() {
    RESULT=1  # failure by default
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
    if [ $files_notremoved -eq 1 ]; then RESULT=0; fi

    return $RESULT
}

_test_androidpic_mv() {
    CHECKED_FUNC='androidpic_mv'
    type -t "$CHECKED_FUNC"
    if [ $? -ne 0 ]; then
        echo "[ERROR] Checked function '$CHECKED_FUNC' not found."; return 1;
    fi

    RESULT=1  # failure by default
    LIST_FILES_A=("aa.jpg" "bb.jpeg" "cc.mp4" "dd.mov")
    LIST_FILES_B=("ee.jpg" "f f.jpeg" "gg.mp4" "hh.mov")
    LIST_FILES_C=( "jj.png" "k k.png")

    # Create folders to mimic real environment
    TARGET_FOLDER=`date -d "$D" '+%m'`;
    # DEBUG purpose.
    ls -al ~/link/Current
    # To avoid the error https://github.com/130s/hut_10sqft/issues/169#issuecomment-322097088, 
    # remove an existing symlink (only in the testcase), and re-create a folder
    # with the same name.
    rm ~/link/Current
    mkdir -p ~/link/Current
    mkdir -p ~/data/Dropbox/Camera\ Uploads/ ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio ~/link/Current/"${TARGET_FOLDER}";
    # Populate dummy image files
    cd ~/data/Dropbox/SharedFromOthers/Camera\ Uploads\ from\ Mio
    for file in "${LIST_FILES_A[@]}"; do touch "$file"; done
    for file in "${LIST_FILES_B[@]}"; do touch "$file"; done  # $file needs to be surrounded by double-quote in order for a file name with spaces to be properly touched.
    mv ${TRAVIS_BUILD_DIR}/test/testdata2/*.png .

    $CHECKED_FUNC

    echo "*** Verifying if files are moved."
    cd ~/link/Current/"${TARGET_FOLDER}"
    echo "Files in the target folder:"; ls -al
    i=0
    # Combine 2 arrays of file names.
    # "f f.jpeg" needs to be renamed as "f_f.jpeg" due to the algorighm of androidpic_mv
    for elem in "${LIST_FILES_A[@]}"; do
        LIST_FILES_ALL[i++]=$elem
    done
    for elem in "${LIST_FILES_B[@]}"; do
        if [ "$elem" = "f f.jpeg" ]; then elem="f_f.jpeg"; fi
        LIST_FILES_ALL[i++]=$elem
    done
    for elem in "${LIST_FILES_C[@]}"; do
        if [[ $elem == *.png ]]; then elem="${elem%.png*}.jpg"; fi  # .png should be renamed to .jpg
        LIST_FILES_ALL[i++]=$elem
    done
    for f in "${LIST_FILES_ALL[@]}"; do
        if [ ! -e "$f" ]; then
            echo "[ERROR] $f is missing from the target folder."; ls -al $f;
        else
            echo "[SUCCESS] $f is found at the target folder."; ls -al $f; RESULT=0;
        fi
    done

    return $RESULT
}

_test_replace_py(){
    RESULT=1  # failure by default
	
	DIR_TEST=/tmp/proovingground_of_mad_overlord/replace_py
	# Unlike test_util.py, this testcase will be run from the top directory
	# of the repo so we still need test folder's path passed. 
	mkdir -p $DIR_TEST && cp -R ./test/testdata1 $DIR_TEST
	cd $DIR_TEST
	
	# Command to be tested. Replace string "Isaac" with "Isao"
	replace_str Isaac Isao -p . -f *
	
	# Verify the command.
	# Success if "grep -i isaac" returns empty result.
	if [[ $(grep -i -r isaac .) ]]; then
		echo "[test_replace_py] Failed. Supposedly replaced string is still found."
	else
		RESULT=0
	fi

    return $RESULT
}

#
# This function works as "main" so all testcases should be defined above here.
#
run_test_conf_bash() {
	retval_test_commands=0
    _test_rm_dropbox_conflictfiles || retval_test_commands=$?
    _test_androidpic_mv || retval_test_commands=$?
    _test_replace_py || retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then
    	echo "Error: not all commands are installed yet. Exiting."
    else
        if [ ! -z $MSG_ENDROLL ]; then printf $MSG_ENDROLL; else echo "No accumulated error messages."; fi
    fi
   return $retval_test_commands
}

# Here's kindf of main function.
# run_test_conf_bash
