#test_convert_time.py
"""@package convert_time
This module tests convert_time module.
"""
from __future__ import print_function
from builtins import range
import sys
from sys import argv
from amonpy.tools.convert_time import *
import unittest

class TestConvertTime(unittest.TestCase):
    def setUp(self):
        # no set up actions yet
        # print 'setting up unit tests: ', argv[0]
        self.mjd = 50448.
        
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass


    def test_gettimestamp(self):
        print("Check Time stamp")
        a=gettimestamp(self.mjd)
        t=a[0].strftime("%Y-%m-%d %H:%M:%S")
        print(t)
        self.assertEqual(t,"1996-12-31 00:00:00")

# Run the unittests
if __name__ == '__main__':
    unittest.main()
