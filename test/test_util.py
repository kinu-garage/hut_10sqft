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
import subprocess
import tarfile
import unittest
import urllib

from hut_10sqft.util import Util


class TestUtil(unittest.TestCase):
    '''
    All tests in this file are intended to be run from the "test" directory;
    i.e. ProjectTop
         |-test
           |-testdata1
           |-test_util.py
    '''

    _pwd_beginning = os.path.abspath(os.path.curdir)
    _TESTDATA_XML1 = 'package1.xml'
    _LIST_TESTDATA1 = [_TESTDATA_XML1, 'prooving2.txt'] 
    _LIST_TESTDATA2 = ["black.jpg", "grey_1.jpg", "grey_2.jpg", "red.png"] 
    _TESTDATA_DIR = './testdata1'
    _TESTDATA2_DIR = "./testdata2"
    _TEST_DIR = '/tmp/proovingground_of_mad_overlord'
    _LIST_TESTDATA1_ABS = [os.path.join(_TEST_DIR, elem)                                         
                           for elem in _LIST_TESTDATA1]
    _LIST_TESTDATA2_ABS = [os.path.join(_TEST_DIR, elem)                                         
                           for elem in _LIST_TESTDATA2]
    
    @classmethod
    def setUpClass(cls):
        super(TestUtil, cls).setUpClass()
        
    def setUp(self):        
        self._setup_testdata()
        self._util = Util()

    def tearDown(self):
        print('tearDown: chdir-ed to {}'.format(TestUtil._pwd_beginning))
        #os.chdir(self.pwd_beginning)
        os.chdir(TestUtil._pwd_beginning)
        
    def _setup_testdata(self):
        # this is where testdata files are. So do this every time.
        os.chdir(TestUtil._pwd_beginning)

        # Set test dir. In case the test script gets run at localhost, not on cloud, and affect the files, it could be bad.
        if os.path.exists(TestUtil._TEST_DIR):
            # Remove and re-create the dir with the same name.
            print('Before removing dir {}: {}'.format(TestUtil._TEST_DIR, os.listdir(TestUtil._TEST_DIR)))
            shutil.rmtree(TestUtil._TEST_DIR)
        os.makedirs(TestUtil._TEST_DIR)
        print('Current dir: {}'.format(os.getcwd()))

        if not os.path.exists(TestUtil._TEST_DIR):
            raise OSError('Directory {} is not available.'.format(TestUtil._TEST_DIR))
        
        # Copy testdata into /tmp folders.
        tgz_filename = TestUtil._TEST_DIR + "/testdata.tar.gz"
        with tarfile.open(tgz_filename, "w:gz") as tgz_file:
            try:
                tgz_file.add(TestUtil._TESTDATA_DIR, arcname=os.path.basename(''))
                tgz_file.add(TestUtil._TESTDATA2_DIR, arcname=os.path.basename(''))
            except OSError as e: # [Errno 2] No such file or directory: './testdata1'
                print("OSError; Make sure to run nosetests from 'test' dir.")
                raise e
            tgz_file.close()
        os.chdir(TestUtil._TEST_DIR)
        with tarfile.open(tgz_filename, "r:gz") as tgz_file_dest:
            tgz_file_dest.extractall(path=TestUtil._TEST_DIR)
            tgz_file_dest.close()
        # Remove the temporary tarball
        os.remove(tgz_filename)
        
#        for file_name in os.listdir(TestUtil._TESTDATA_DIR):
#            file_name_longerpath = TestUtil._TESTDATA_DIR + '/' + file_name
#            print('File in test dir: {}'.format(file_name_longerpath))
#            if not os.path.isdir(file_name_longerpath):
#                print('File to copy: {}'.format(file_name_longerpath))
#                shutil.copy(file_name_longerpath, TestUtil._TEST_DIR)  #TODO this has to handle copying folders in addtion to files. 

        print('After copying files into {}: {}\nCurrent dir: {}'.format(TestUtil._TEST_DIR, os.listdir(TestUtil._TEST_DIR), os.path.abspath(os.path.curdir)))

    def test_find_all_files_noarg_absolutepath(self):
        # Test without argument passed to find_all_files.
        # Test absolute paths.
        filenames_matched_1 = Util.find_all_files()
        ##filenames_matched_1 = Util.find_all_files(depth_max=1)
        
        self.assertItemsEqual(filenames_matched_1, self._LIST_TESTDATA1_ABS + self._LIST_TESTDATA2_ABS)

    def test_find_all_files_noarg_relativepath(self):
        # Test without argument passed to find_all_files.
        # Test absolute paths.
        filenames_matched_1 = Util.find_all_files(ret_relativepath=True)
        self.assertItemsEqual(filenames_matched_1, self._LIST_TESTDATA1)

    def test_find_all_files_path(self):
        '''Util.find_all_files with path specified.'''
        filenames_matched_2 = Util.find_all_files(path=TestUtil._TEST_DIR)
        self.assertItemsEqual(filenames_matched_2, self._LIST_TESTDATA1_ABS)

    def _test_find_all_files_filepattern(self, filename_ptn='*xml',
                                         shouldfail=False, depthmax=3,
                                         expected_files_relat=[_TESTDATA_XML1]):
        filenames_matched_3 = Util.find_all_files(filename_pattern=filename_ptn,
                                                  depth_max=depthmax)
        # This list should be [self._TESTDATA_XML1]
        list_expected = [TestUtil._TEST_DIR + '/' + f for f in expected_files_relat]
        print('list_expected: {}\nfilenames_matched_3:'
              ' {}'.format(list_expected, filenames_matched_3))
        common_list = list(set(filenames_matched_3).intersection(list_expected))
        
        if shouldfail:
            self.assertNotEqual(common_list, list_expected)
        else:
            self.assertEqual(common_list, list_expected)

    def test_find_all_files_filepattern_noasterisk(self):
        self._test_find_all_files_filepattern('xml', True)

    def test_find_all_files_filepattern_asterisk(self):
        self._test_find_all_files_filepattern()

    def test_find_all_files_unlimiteddepth(self):
        '''Util.find_all_files with unlimited depth specified.'''
        expected_files = [TestUtil._TESTDATA_XML1, 'depth1/depth2/depth3/depth4/depth5/depth6/depth7/prooving3.xml']
        self._test_find_all_files_filepattern(depthmax=0, expected_files_relat=expected_files)

    def _test_replace_str_infile(self, match_str_regex='<version>.*</version>',
                                 new_str='<version>100000000000</version>',
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
        self._test_replace_str_infile(searchpath=TestUtil._TEST_DIR,
                                      filename='file_strtest.txt')

    def test_replace_str_infile_nospecify(self):
        '''Test w/o specifying filepath and filename.'''
        self._test_replace_str_infile()

    def _test_measure_performance(self):
        '''Prefixed since this testcase is NOT functional yet. '''
        from subprocess import Popen, PIPE
        process = Popen(['measure_performance', 'ls', '10'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        self.assertTrue(stderr, '')

    def test_mv_ext(self):
        _src = '/tmp/test_mv_ext1'
        _dest = '/tmp/test_mv_ext2'
        subprocess.call(['touch', _src])

        dest_name = Util.mv_ext(_src, _dest)

        # CNCL; Compare the timestamp and if both are close enough (e.g. less than a minute), let the test pass.
        #
        # Extract the timestamp portion and measure the length of the string = 14
        self.assertEqual(len(dest_name.split("_")[-1]), 14)

    def test_imgs_to_pdf(self):
        _PATHS_ABS_INPUT_FILES = os.listdir(os.path.join(TestUtil._TEST_DIR, TestUtil._TESTDATA2_DIR))
        outfile = self._util.imgs_to_pdf(_PATHS_ABS_INPUT_FILES)
        statinfo = os.stat(outfile)
        self.assertGreater(statinfo.st_size, 0)

if __name__ == '__main__':
    unittest.main()
