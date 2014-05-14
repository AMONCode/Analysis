#convert_time2.py
"""@package convert_time2
A quick test for comparison to convert_time module.
"""
import sys
sys.path.append('../sim')
import sidereal

def gettimestamp(mjd):
    jd = mjd + 2400000.5
    
    j,f = divmod(jd,1)
    jday = sidereal.JulianDate(j,f)
    dt = jday.datetime()
    
    return dt  
    
    
    