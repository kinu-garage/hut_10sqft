#!/usr/bin/env python

import os
import unittest
import urllib

from util.util import Util


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

        # TODO Run the process
        # Find all package.xml files in sub-folders.
        files_found = Util.find_all(FILENAME_STRTEST, '/tmp')
        for f in files_found:
            print(f)
    #        replace(f, "<version>.*</version>", "<version>0.8.2</version>")
            util.replace(f, MATCH_STR_REGEX, NEW_STR)

        # Assert if the new str is contained and old str are not.
        is_replaced = False
        file_strtest = open(FILENAME_STRTEST).read()
        print('Content of the file tested: '.format(file_strtest))
        if NEW_STR in file_strtest:
            is_replaced = True        
        self.assertTrue(is_replaced, 'String is not found in the targeted file.')

    def test_measure_performance(self):
        from subprocess import Popen, PIPE
        process = Popen(['measure_performance', 'ls', '10'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        self.assertTrue(stderr, '')
