#!/usr/bin/env python

# Copyright 2016 Isaac I. Y. Saito.
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

import fileinput
import fnmatch
import os
import re
import sys

class Util():

    @staticmethod
    def find_all_files(path='.', filename_pattern='*', ret_relativepath=False):
        '''
        http://stackoverflow.com/questions/1724693/find-a-file-in-python
        @param path: (str) Top level path to search.
        @param filename_pattern: Full file name or pattern to be found.
        @type filename_pattern: str
        @param ret_relativepath: If True, returned file paths will be in
                                 relative to the "path" arg.
                                 e.g. ['file1', 'currentdir/file2']
        @return: List of absolute path of the files.
        '''
        filenames_matched = []
        for root, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, filename_pattern):
                if ret_relativepath:
                    filenames_matched.append(filename)
                else:
                    filenames_matched.append(os.path.abspath(filename))

        print('[find_all_files]: matched files: {}'.format(filenames_matched))
        return filenames_matched

    @staticmethod
    def replaceAll(file, searchExp, replaceExp):
        '''
        http://stackoverflow.com/questions/39086/search-and-replace-a-line-in-a-file-in-python
    
        Example usage: replaceAll("/fooBar.txt","Hello\sWorld!$","Goodbye\sWorld.")
        '''
        for line in fileinput.input(file, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp, replaceExp)
            sys.stdout.write(line)

    @staticmethod
    def replace(filename, pattern, subst):
        '''
        Replace string in a single file.
        RegEx capable.
        Originally taken from http://stackoverflow.com/a/13641746/577001
        @param pattern: Regular expression of the pattern of strings to be
                        replaced.
        @param subst: Exact string to be replaced with.
        '''
        # Read contents from filename as a single string
        file_handle = open(filename, 'r')
        file_string = file_handle.read()
        file_handle.close()
    
        # Use RE package to allow for replacement (also allowing for (multiline) REGEX)
        file_string = (re.sub(pattern, subst, file_string))
    
        # Write contents to file.
        # Using mode 'w' truncates the file.
        file_handle = open(filename, 'w')
        file_handle.write(file_string)
        file_handle.close()

    @staticmethod
    def replace_str_in_file(match_str_regex, new_str, target_path='.', target_filename='*'):
        '''
        @param target_filename: Name of the file(s) to be manipulated.
        @param target_path: Path under which target file(s) will be searched at. Full or relative path.
        @param match_str_regex: File pattern to match. You can use regular expression.
        @param new_str: String to be used.
        '''    
        # Find all files in sub-folders.
        files_found = Util.find_all_files(target_path, target_filename)
        for f in files_found:
            print('Path of the file  to be replaced: {}'.format(f))
            # replace(f, "<version>.*</version>", "<version>0.8.2</version>")
            Util.replace(f, match_str_regex, new_str)

        # Testing regex
        #     if re.match("<version>.*</version>", "<version>0.7.2</version>"):
        #         print(11)
        #     else:
        #         print(22)

    @staticmethod
    def common_list(list_a, list_b):
        '''
        Originally hinted at http://stackoverflow.com/questions/20050913/python-unittests-assertdictcontainssubset-recommended-alternative
        @type list_a: [str]
        @type list_b: [str]
        Returns a list of common values among the two passed lists.
        '''
        return [k for k in list_a.keys() if k in list_b.keys()]
