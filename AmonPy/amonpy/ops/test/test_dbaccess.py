#test_dbaccess.py
"""@package test_db_access
Module to test dbaccess files with
user privileges.
"""
from __future__ import print_function
import sys
# sys.path.append("./")
import unittest
import ast

class TestDBaccess(unittest.TestCase):
    def setUp(self):
        # no set up actions yet
        # print 'setting up unit tests: ', argv[0]
        pass

    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]
        pass

    def test1_readfile(self):
        file=open("../dbaccess.txt")
        # get the first line of the file
        line = file.readline()
        # convert to a dictionary
        db = ast.literal_eval(line)
        print(db)
        file.close()

# Run the unittests
if __name__ == '__main__':
    unittest.main()
