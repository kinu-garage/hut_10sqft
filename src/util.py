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
import os
import re
import sys

class Util():

    @staticmethod
    def find_all(filename, path):
        '''
        http://stackoverflow.com/questions/1724693/find-a-file-in-python
        @param filename: (str) Full file name to be found.
        @param path: (str) Top level path to search.
        @return: List of absolute path of the files.
        '''
        result = []
        for root, dirs, files in os.walk(path):
            if filename in files:
                result.append(os.path.join(root, filename))
        return result

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
        http://stackoverflow.com/a/13641746/577001
        RegEx capable.
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
    def replace_str_in_file(target_filename, target_path, match_str_regex, new_str):
        '''
        parser = argparse.ArgumentParser(description='Replace a line of string in all the files found at the folder tree in the given path.')
        parser.add_argument('target_filename', default='package.xml', help='Name of the file(s) to be manipulated.')
        parser.add_argument('target_path', default='.', help='Path under which target file(s) will be searched at. Full or relative path (relative path is not tested).')
        parser.add_argument('match_str_regex', default='<version>.*</version>', help='File pattern to match. You can use regular expression.')
        parser.add_argument('new_str', default='', help='String to be used.')
        '''
    
        # Find all package.xml files in sub-folders.
        files_found = Util.find_all(target_filename, target_path)
        for f in files_found:
            print(f)
        # replace(f, "<version>.*</version>", "<version>0.8.2</version>")
            Util.replace(f, match_str_regex, new_str)
    
        # Testing regex
        #     if re.match("<version>.*</version>", "<version>0.7.2</version>"):
        #         print(11)
        #     else:
        #         print(22)
    
