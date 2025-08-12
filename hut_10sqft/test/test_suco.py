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
import sys

from hut_10sqft.init_setup import ChromeOsSetup, ConfigDispach, MacOsSetup, OsUtil, UbuntuOsSetup

ATTR_HOME_DIR = "user_home_dir"
ATTR_PATH_SYMLINKS_DIR = "path_symlinks_dir"

@pytest.fixture
def cfgbuilder():
    _os_type, _distro_type = OsUtil.get_os_type()
    if _os_type == OsUtil.TYPE_OS_LINUX:
        # Assuming Ubuntu is a common Linux distribution
        return ChromeOsSetup()
    elif _os_type == OsUtil.TYPE_OS_MACOS:
        # You can add more specific checks for macOS versions if needed,
        # e.g., using platform.mac_ver()
        return MacOsSetup()
    else:
        raise RuntimeError(f"Unsupported OS platform: {_os_type}.")

@pytest.fixture
def chromeos_input_params():
    return {
        ATTR_HOME_DIR: "~",
        ATTR_PATH_SYMLINKS_DIR: "/"
    }

def test_generate_symlinks(cfgbuilder, chromeos_input_params):
    pairs = cfgbuilder.generate_symlinks(
            rootpath_symlinks=os.path.join(chromeos_input_params[ATTR_HOME_DIR], chromeos_input_params[ATTR_PATH_SYMLINKS_DIR]),
            path_user_home=chromeos_input_params[ATTR_HOME_DIR])
#    assert type(pairs) == list[ConfigDispach]
    assert type(pairs) == list
    assert len(pairs) == 6
    
