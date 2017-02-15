#!/usr/bin/env python

import argparse
from util import Util


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
#        replace(f, "<version>.*</version>", "<version>0.8.2</version>")
        Util.replace(f, match_str_regex, new_str)

    # Testing regex
    #     if re.match("<version>.*</version>", "<version>0.7.2</version>"):
    #         print(11)
    #     else:
    #         print(22)