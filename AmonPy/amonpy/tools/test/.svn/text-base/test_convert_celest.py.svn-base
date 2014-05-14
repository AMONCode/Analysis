#test_convert_celest.py
"""@package convert_celest
This module tests convert_celest module.
"""
import sys
from sys import argv
sys.path.append("../")
from convert_celest import *
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
        for ii in xrange(len(ra_list)):
            ra = ra_list[ii]
            dec= dec_list[ii]
            v = radec2vec(ra,dec)
            radec = vec2radec(v)
            ra1 = radec['ra']
            dec1= radec['dec']
            print
            print 'Test of (ra,dec): ', ra, dec
            print 'Unit vector: ', v
            print 'Convert back (ra,dec): ', ra1, dec1
            print 


    def test_quadrants(self):
        #ra_list=[45.,135.,225.,315.,45.,135.,225.,315.]
        ra_list0=[jj*30. for jj in xrange(12)]
        #dec_list=[45.,45.,45.,45.,-45.,-45.,-45.,-45.]
        dec_list0=[45. for jj in xrange(12)]
        dec_list1=[-45. for jj in xrange(12)]
        ra_list =ra_list0+ ra_list0
        dec_list = dec_list0 + dec_list1
        for ii in xrange(len(ra_list)):
            ra = ra_list[ii]
            dec= dec_list[ii]
            v = radec2vec(ra,dec)
            radec = vec2radec(v)
            ra1 = radec['ra']
            dec1= radec['dec']
            print
            print 'Test of (ra,dec): ', ra, dec
            print 'Unit vector: ', v
            print 'Convert back (ra,dec): ', ra1, dec1
            print

            

# Run the unittests
if __name__ == '__main__':
    unittest.main()

    
