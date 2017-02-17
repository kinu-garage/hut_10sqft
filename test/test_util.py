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
import shutil
import unittest
import urllib

from util import Util


class TestUtil(unittest.TestCase):
    '''
    All tests in this file are intended to be run from project top directory;
    dir X at X/test/test_util.py
    '''

    _pwd_beginning = os.path.abspath(os.path.curdir)

    @classmethod
    def setUpClass(cls):
        super(TestUtil, cls).setUpClass()
        
    def setUp(self):
        self._TESTDATA_XML1 = 'package1.xml'
        self._LIST_TESTDATA1 = [self._TESTDATA_XML1, 'prooving2.txt'] 
        self.TESTDATA_DIR = './test/testdata1'
        self.TEST_DIR = '/tmp/proovingground_of_mad_overlord'
        self._LIST_TESTDATA1_ABS = [self.TEST_DIR + '/' + elem
                                    for elem in self._LIST_TESTDATA1] 
        
        self._setup_testdata()        

    def tearDown(self):
        print('tearDown: chdir-ed to {}'.format(TestUtil._pwd_beginning))
        #os.chdir(self.pwd_beginning)
        os.chdir(TestUtil._pwd_beginning)
        
    def _setup_testdata(self):
        # this is where testdata files are. So do this every time.
        os.chdir(TestUtil._pwd_beginning)

        # Set test dir. In case the test script gets run at localhost, not on cloud, and affect the files, it could be bad.
        if os.path.exists(self.TEST_DIR):
            # Remove and re-create the dir with the same name.
            print('Before removing dir {}: {}'.format(self.TEST_DIR, os.listdir(self.TEST_DIR)))
            shutil.rmtree(self.TEST_DIR)
        os.makedirs(self.TEST_DIR)
        print('Current dir: {}\nAfter recreating dir {}'.format(TestUtil._pwd_beginning, self.TEST_DIR))

        if not os.path.exists(self.TEST_DIR):
            raise OSError('Directory {} is not available.'.format(self.TEST_DIR))
        
        # Copy testdata into /tmp folders.
        for file_name in os.listdir(self.TESTDATA_DIR):
            shutil.copy(self.TESTDATA_DIR + '/' + file_name, self.TEST_DIR)

        os.chdir(self.TEST_DIR)
        print('After copying files into {}: {}\nCurrent dir: {}'.format(self.TEST_DIR, os.listdir(self.TEST_DIR), os.path.abspath(os.path.curdir)))

    def test_find_all_files_noarg_absolutepath(self):
        # Test without argument passed to find_all_files.
        # Test absolute paths.
        filenames_matched_1 = Util.find_all_files()
        self.assertItemsEqual(filenames_matched_1, self._LIST_TESTDATA1_ABS)

    def test_find_all_files_noarg_relativepath(self):
        # Test without argument passed to find_all_files.
        # Test absolute paths.
        filenames_matched_1 = Util.find_all_files(ret_relativepath=True)
        self.assertItemsEqual(filenames_matched_1, self._LIST_TESTDATA1)

    def test_find_all_files_path(self):
        '''Util.find_all_files with path specified.'''
        filenames_matched_2 = Util.find_all_files(path=self.TEST_DIR)
        self.assertItemsEqual(filenames_matched_2, self._LIST_TESTDATA1_ABS)

    def _test_find_all_files_filepattern(self, filename_ptn, shouldfail=False):
        filenames_matched_3 = Util.find_all_files(path='.',
                                                  filename_pattern=filename_ptn)
        # This list should be [self._TESTDATA_XML1]
        list_expected = [self.TEST_DIR + '/' + self._TESTDATA_XML1]
        common_list = list(set(filenames_matched_3).intersection(list_expected))
        
        if shouldfail:
            self.assertNotEqual(common_list, list_expected)
        else:
            self.assertEqual(common_list, list_expected)

    def test_find_all_files_filepattern_noasterisk(self):
        self._test_find_all_files_filepattern('xml', True)

    def test_find_all_files_filepattern_asterisk(self):
        self._test_find_all_files_filepattern('*xml*')

    def _test_replace_str_infile(self, match_str_regex, new_str,
                                 searchpath='.', filename='*'):
        FILE_STRTEST = 'https://raw.githubusercontent.com/ros-planning/moveit/kinetic-devel/moveit/package.xml'
        testfile = urllib.URLopener()
        # Save temporarily. This method is intended for files on the filesystem.
        testfile.retrieve(FILE_STRTEST, filename)

        # Find all package.xml files in sub-folders.
        Util.replace_str_in_file(match_str_regex, new_str, searchpath, filename)

        is_replaced = False
        file_strtest = open(filename).read()
        self.assertIsNotNone(file_strtest) and self.assertIsNot(file_strtest, None) 
        print('Content of the file tested: {}'.format(file_strtest))
        if new_str in file_strtest:
            is_replaced = True        
        # Assert if the new str is contained and old str are not.
        self.assertTrue(is_replaced, 'String is not found in the targeted file.')

    def test_replace_str_infile_specific(self):
        '''Test specifying filepath and filename.'''
        self._test_replace_str_infile('<version>.*</version>',
                                      '<version>100000000000</version>',
                                      self.TEST_DIR, 'file_strtest.txt')

    def test_replace_str_infile_nospecify(self):
        '''Test w/o specifying filepath and filename.'''
        self._test_replace_str_infile('<version>.*</version>',
                                      '<version>100000000000</version>')

    def _test_measure_performance(self):
        '''Prefixed since this testcase is NOT functional yet. '''
        from subprocess import Popen, PIPE
        process = Popen(['measure_performance', 'ls', '10'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        self.assertTrue(stderr, '')

if __name__ == '__main__':
    unittest.main()
