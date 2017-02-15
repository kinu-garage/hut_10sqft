#!/usr/bin/env python

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

import os
import unittest
import urllib

from replace_str_infile import replace_str_in_file


class TestUtil(unittest.TestCase):
    '''
    All tests in this file are intended to be run from project top directory;
    dir X at X/test/test_util.py
    '''

    def setUp(self):

        self._TESTDATA_XML1 = 'package1.xml'
        self._LIST_TESTDATA1 = [self._TESTDATA_XML1, 'prooving2.txt'] 
        self.TESTDATA_DIR = './test/testdata1' 

        self.TEST_DIR = '/tmp/proovingground_of_mad_overlord'

    def _setup_testdata(self):
        # Set test dir. In case the test script gets run at localhost, not on cloud, and affect the files, it could be bad.
        if os.path.exists(self.TEST_DIR):
            # Remove the dir and re-create with the same name.
            shutil.rmtree(self.TEST_DIR)
            os.makedirs(self.TEST_DIR)

        # Copy testdata into /tmp folders.
        src = self.TESTDATA_DIR
        src_files = os.listdir(src)
        dest = self.TEST_DIR
        for file_name in src_files:
            full_file_name = os.path.join(src, file_name)
            print('File to be copied into: {}'.format(full_file_name))
            if (os.path.isfile(full_file_name)):
                shutil.copy(full_file_name, dest)

    def test_find_all_files(self):
        self._setup_testdata()
        os.chdir(self.TEST_DIR)

        # Test without argument passed to find_all_files.
        filenames_matched_1 = Util.find_all_files()
        self.assertItemsEqual(filenames_matched_1, self._LIST_TESTDATA1)

        # Test with arguments passed to find_all_files.
        filenames_matched_2 = Util.find_all_files(path=self.TEST_DIR)
        self.assertItemsEqual(filenames_matched_2, self._LIST_TESTDATA1)

        filenames_matched_3 = Util.find_all_files(filename_pattern='xml')
        # This list should be [self._TESTDATA_XML1]
        common_list = set(filenames_matched_3) & set(self._LIST_TESTDATA1)
        assertEqual(common_list, [self._TESTDATA_XML1])

    def _test_replace_str_infile(self, match_str_regex, new_str, searchpath, filename):
        os.chdir(self.TEST_DIR)
        testfile = urllib.URLopener()
        # Save temporarily. This method is intended for files on the filesystem.
        testfile.retrieve(FILE_STRTEST, FILENAME_STRTEST)

        # Find all package.xml files in sub-folders.
        replace_str_in_file(match_str_regex, new_str, searchpath, filename)

        is_replaced = False
        file_strtest = open(FILENAME_STRTEST).read()
        self.assertIsNotNone(file_strtest) and self.assertIsNot(file_strtest, None) 
        print('Content of the file tested: {}'.format(file_strtest))
        if NEW_STR in file_strtest:
            is_replaced = True        
        # Assert if the new str is contained and old str are not.
        self.assertTrue(is_replaced, 'String is not found in the targeted file.')

    def test_replace_str_infile_specific(self):
        '''Test specifying filepath and filename.'''
        self._test_replace_str_infile(MATCH_STR_REGEX, NEW_STR, self.TEST_DIR, FILENAME_STRTEST)

    def test_replace_str_infile_nospecify(self):
        '''Test w/o specifying filepath and filename.'''
        self._test_replace_str_infile(MATCH_STR_REGEX, NEW_STR)

    def _test_measure_performance(self):
        '''Prefixed since this testcase is NOT functional yet. '''
        from subprocess import Popen, PIPE
        process = Popen(['measure_performance', 'ls', '10'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        self.assertTrue(stderr, '')

if __name__ == '__main__':
    unittest.main()
