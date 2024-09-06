#!/usr/bin/env python

# Copyright 2024 Kinu Garage Inc.
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

import os
import pytest

from hut_10sqft.init_setup import ChromeOsSetup, ConfigDispach

ATTR_HOME_DIR = "user_home_dir"
ATTR_PATH_SYMLINKS_DIR = "path_symlinks_dir"

@pytest.fixture
def cfgbuilder_chromeos():
    return ChromeOsSetup()

@pytest.fixture
def chromeos_input_params():
    return {
        ATTR_HOME_DIR: "~",
        ATTR_PATH_SYMLINKS_DIR: "/"
    }

def test_generate_symlinks(cfgbuilder_chromeos, chromeos_input_params):
    pairs = cfgbuilder_chromeos.generate_symlinks(
            rootpath_symlinks=os.path.join(chromeos_input_params[ATTR_HOME_DIR], chromeos_input_params[ATTR_PATH_SYMLINKS_DIR]),
            path_user_home=chromeos_input_params[ATTR_HOME_DIR])
#    assert type(pairs) == list[ConfigDispach]
    assert type(pairs) == list
    assert len(pairs) == 5
    