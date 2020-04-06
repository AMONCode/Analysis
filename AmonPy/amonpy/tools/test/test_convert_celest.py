#test_convert_celest.py
"""@package convert_celest
This module tests convert_celest module.
"""
from __future__ import print_function
from builtins import range
import sys
from sys import argv
from amonpy.tools.convert_celest import *
import unittest

class TestConvertCelest(unittest.TestCase):
    def setUp(self):
        # no set up actions yet
        # print 'setting up unit tests: ', argv[0]
        pass
        
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass


    def test_poles(self):
        ra_list=[0.,90.,180.,270.,0.,90.,180.,270.,0.,90.,180.,270.]
        dec_list=[90.,90.,90.,90.,0.,0.,0.,0.,-90.,-90.,-90.,-90.]
        for i in range(len(ra_list)):
            ra = ra_list[i]
            dec= dec_list[i]
            v = radec2vec(ra,dec)
            radec = vec2radec(v)
            ra1 = radec['ra']
            dec1= radec['dec']
            #self.assertEqual(ra,ra1)
            self.assertEqual(dec,dec1)


    def test_quadrants(self):
        ra_list0=[jj*30. for jj in range(12)]
        dec_list0=[45. for jj in range(12)]
        dec_list1=[-45. for jj in range(12)]
        ra_list =ra_list0+ ra_list0
        dec_list = dec_list0 + dec_list1
        for ii in range(len(ra_list)):
            ra = ra_list[ii]
            dec= dec_list[ii]
            v = radec2vec(ra,dec)
            radec = vec2radec(v)
            ra1 = radec['ra']
            dec1= radec['dec']
            self.assertEqual(ra,ra1)
            self.assertEqual(dec,dec1)

            

# Run the unittests
if __name__ == '__main__':
    unittest.main()

    
