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

if [ -z $CI_SOURCE_PATH ]; then
	echo 'Env var CI_SOURCE_PATH needs set at the top dir of this repo/package. Exiting.'
	exit 1	
fi

#######################################
#
# Globals:
#   (None)
# Arguments:
#   (None)
# Returns:
#   int 0 when success.
#######################################
run_tests(){
  # Test some commands to check installation
  retval_test_commands=0
  source $CI_SOURCE_PATH/test/test_install.sh
  source $CI_SOURCE_PATH/test/test_conf_bash.sh
  run_test_install || retval_test_commands=$?
  run_test_conf_bash || retval_test_commands=$?

  if [ $retval_test_commands -ne 0 ]; then echo 'sh test(s) did not pass. Exiting.'; return $retval_test_commands; fi

  # 20170224 test/test_util.py is path dependent as of today. We have to move there to run the tests there.
  cd $CI_SOURCE_PATH/test
  nosetests -vv --collect-only  # Show which files are actually handled by nose.
  nosetests -d --exe -s -v -x || retval_test_commands=$?

  return $retval_test_commands
}