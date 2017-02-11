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

    def test_replace_str_infile(self):
        os.chdir('/tmp')
        # Prepare files to be manipulated.
        FILE_STRTEST = 'https://raw.githubusercontent.com/ros-planning/moveit/kinetic-devel/moveit/package.xml'
        FILENAME_STRTEST = 'file_strtest.txt'
        MATCH_STR_REGEX = '<version>.*</version>'
        NEW_STR = '<version>100000000000</version>'  # Something unrealistically used by anyone in any software.
        testfile = urllib.URLopener()
        # Save temporarily. This method is intended for files on the filesystem.
        testfile.retrieve(FILE_STRTEST, FILENAME_STRTEST)         

        # Find all package.xml files in sub-folders.
        replace_str_in_file(FILENAME_STRTEST, '/tmp', MATCH_STR_REGEX, NEW_STR)

        is_replaced = False
        file_strtest = open(FILENAME_STRTEST).read()
        self.assertIsNotNone(file_strtest) and self.assertIsNot(file_strtest, None) 
        print('Content of the file tested: {}'.format(file_strtest))
        if NEW_STR in file_strtest:
            is_replaced = True        
        # Assert if the new str is contained and old str are not.
        self.assertTrue(is_replaced, 'String is not found in the targeted file.')

    def _test_measure_performance(self):
        '''Prefixed since this testcase is NOT functional yet. '''
        from subprocess import Popen, PIPE
        process = Popen(['measure_performance', 'ls', '10'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        self.assertTrue(stderr, '')

if __name__ == '__main__':
    unittest.main()
