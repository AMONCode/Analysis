#test_sidereal.py
"""@package test_sidereal
Testing module for sidereal_m module.
"""
import sys
sys.path.append("../")
import sidereal_m as sidereal
from numpy import math
import unittest
from datetime import datetime, timedelta

class TestSidereal(unittest.TestCase):
    def setUp(self):
        # no set up actions yet
        # print 'setting up unit tests: ', argv[0]
        pass
        
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass

    def test1_coords(self):
        Ntest = 360 
        az = [ii/float(Ntest)*360. for ii in xrange(Ntest+1)]
        alt = [45. for ii in xrange(Ntest+1)]
        dt = datetime(2012,01,01,0,0,0,0)
        times = [dt for ii in xrange(Ntest+1)]
        lon = 0.
        lat = -90.
        latlon = sidereal.LatLon(math.radians(lat),math.radians(lon))
    

        for ii in xrange(Ntest+1):
            GST = sidereal.SiderealTime.fromDatetime(times[ii])
            LST = GST.lst(math.radians(lon))
            altaz = sidereal.AltAz(math.radians(alt[ii]),math.radians(az[ii]))
            radec = altaz.raDec(LST,latlon)
            ra = math.degrees(radec.ra)
            dec = math.degrees(radec.dec)
            print ii, times[ii], LST, az[ii], alt[ii], ra, dec 


# Run the unittests
if __name__ == '__main__':
    unittest.main()
