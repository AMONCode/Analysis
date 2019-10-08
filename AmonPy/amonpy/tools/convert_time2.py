#convert_time2.py
"""@package convert_time2
A quick test for comparison to convert_time module.
"""
import sys
from amonpy.sim.sidereal import *

def gettimestamp(mjd):
    jd = mjd + 2400000.5
    
    j,f = divmod(jd,1)
    jday = sidereal.JulianDate(j,f)
    dt = jday.datetime()
    
    return dt  
    
    
    
