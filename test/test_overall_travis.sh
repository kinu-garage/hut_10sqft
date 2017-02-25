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

# Test some commands to check installation
source $CI_SOURCE_PATH/test/test_install.sh
source $CI_SOURCE_PATH/test/test_conf_bash.sh

# 20170224 test/test_util.py is path dependent as of today. We have to move there to run the tests there.
cd $CI_SOURCE_PATH/test
nosetests -vv --collect-only  # Show which files are actually handled by nose.
nosetests -d --exe -s -v -x
