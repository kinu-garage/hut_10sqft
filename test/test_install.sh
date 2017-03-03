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

_test_commands() {
    RESULT=0  # success by default

    bloom-release --help || RESULT=1
    catkin --help || RESULT=1
    rosdep --help || RESULT=1
    wstool --help || RESULT=1
    return $RESULT
}

# Need to test https://github.com/130s/hut_10sqft/issues/3
test_display_env() {
    #TODO
    return
}

run_test_install() {
	retval_test_commands=0

    _test_commands || retval_test_commands=$?
    test_display_env || retval_test_commands=$?
    if [ $retval_test_commands -ne 0 ]; then echo "Error: not all commands are installed yet. Exiting.o"; fi    
    if [ ! -z "$MSG_ENDROLL" ]; then printf "$MSG_ENDROLL"; else echo "No accumulated error messages."; fi
    return $retval_test_commands
}

# Here's kindf of main function.
# 201703 Because now this "main" function is intended to be called by another script, we don't call this here anymore. 
# run_test_install
