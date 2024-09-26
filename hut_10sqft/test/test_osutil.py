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

from datetime import datetime
import os
from pathlib import Path
import pytest

from hut_10sqft.init_setup import OsUtil


TEST_FILE_CONTENT_TEXT = "Test content-a"

@pytest.fixture
def timestamp(scope="session"):
    return datetime.today().strftime("%Y%m%d-%H%M%S")

def _file_creation(timestamp, filename: str, testdir_parent: str="/tmp/test"):
    _filename_full = f"test-{timestamp}"
    _test_dir_abs = os.path.join(testdir_parent, _filename_full)
    if not os.path.exists(_test_dir_abs):
        os.makedirs(_test_dir_abs)
    file_path_src = os.path.join(_test_dir_abs, filename)
    return file_path_src

@pytest.fixture
def filepath_src(timestamp):
    _filename_src = "file-a-before-copied.txt"
    file_path = _file_creation(timestamp, _filename_src)
    if not os.path.exists(file_path):
        with open(file_path, "w") as file:
            file.write(TEST_FILE_CONTENT_TEXT)
    return file_path

@pytest.fixture
def filepath_dst(timestamp):
    _filename_dest = "file-a-after-copied.txt"
    file_path = _file_creation(timestamp, _filename_dest)
    return file_path

def test_copy_a_file_basic(filepath_src, filepath_dst):
    """
    @description: Success if we can confirm:
        input: /tmp/test/test-yyyymmddhhmmss/file-a-before-copied.txt
        then
        output: /tmp/test/test-yyyymmddhhmmss/file-a-after-copied.txt
    """
    OsUtil.copy_a_file(filepath_src, filepath_dst)
    assert os.path.exists(filepath_dst)
    # Read the dest file and verify content is the same as source.
    with open(filepath_dst, "r") as file_dst:
        assert file_dst.read() == TEST_FILE_CONTENT_TEXT

def _test_copy_a_file_symlink(timestamp, filepath_src, overwrite=False):
    """
    @description: Success if we can confirm:
        input: /tmp/test/test-yyyymmddhhmmss/file-a-before-copied.txt
        then
        output w/symlink: /tmp/test/test-yyyymmddhhmmss/symlinked-file-a-after-copied.txt
    """
    _filename_dest_symlinked = "symlinked-file-a-after-copied.txt"
    filepath_dst = _file_creation(timestamp, _filename_dest_symlinked)

    OsUtil.copy_a_file(filepath_src, filepath_dst, is_symlink=True, overwrite=overwrite)
    assert os.path.exists(filepath_dst)
    assert Path(filepath_dst).is_symlink()
    # Read the dest file and verify content is the same as source.
    with open(filepath_dst, "r") as file_dst:
        assert file_dst.read() == TEST_FILE_CONTENT_TEXT

def test_copy_a_file_symlink(timestamp, filepath_src):
    _test_copy_a_file_symlink(timestamp, filepath_src)

def test_copy_a_file_backup(filepath_src, filepath_dst):
    """
    @description: Success if we can confirm:
        input: /tmp/test/test-yyyymmddhhmmss/file-a-before-copied.txt
        then
        output: /tmp/test/test-yyyymmddhhmmss/symlinked-file-a-after-copied.txt
                and
                /tmp/test/test-yyyymmddhhmmss/file-a-before-copied.txt.org
    """
    _SUFFIX_FILE_ORG = ".origi"
    OsUtil.copy_a_file(filepath_src, filepath_dst, overwrite=True, backup_suffix=_SUFFIX_FILE_ORG)
    assert os.path.exists(filepath_dst + _SUFFIX_FILE_ORG)

def test_copy_a_file_symlink_overwrite(timestamp, filepath_src):
    _test_copy_a_file_symlink(timestamp, filepath_src, overwrite=True)
