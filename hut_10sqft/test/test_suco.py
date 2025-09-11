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

import argparse
import os
import pytest
import sys

from hut_10sqft.init_setup import ChromeOsSetup, CompInitSetup, ConfigDispach, MacOsSetup, OsUtil, UbuntuOsSetup

ATTR_HOME_DIR = "user_home_dir"
ATTR_PATH_SYMLINKS_DIR = "path_symlinks_dir"

@pytest.fixture
def argparsed():
    _args = argparse.Namespace()
    _os_type, _distro_type = OsUtil.get_os_type()
    _args.os_distro = _distro_type
    _args.os_type = _os_type
    _args.hostname = "suco_test_host"
    _args.user_id = "suco_test_user"
    _args.skip_setup_docker = True
    return _args

@pytest.fixture
def cfgbuilder(argparsed):
    if argparsed.os_type == OsUtil.TYPE_OS_LINUX:
        if argparsed.os_distro == OsUtil.TYPE_LINUX_DISTRO_DEBIAN:
            return ChromeOsSetup(args_in=argparsed)
        elif argparsed.os_distro == OsUtil.TYPE_LINUX_DISTRO_UBUNTU:
            return UbuntuOsSetup(args_in=argparsed)
    elif argparsed.os_type == OsUtil.TYPE_OS_MACOS:
        # You can add more specific checks for macOS versions if needed,
        # e.g., using platform.mac_ver()
        return MacOsSetup(args_in=argparsed)
    else:
        raise RuntimeError(f"Unsupported OS platform: {argparsed.os_distro}.")

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
    
