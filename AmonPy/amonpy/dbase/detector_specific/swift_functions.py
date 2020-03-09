"""@package swift_functions
    Module with Swift specific function:
    - 2day
    - random_time_stamp
"""

# Author: Cody Messick <cody.messick@psu.edu>
from __future__ import division
from builtins import str
from numpy.random import randint
import time
from decimal import Decimal

def met2day(met):
    """ 
        Converts from Swift time to time stamp needed by database 
    """
    #TODO Clean up with time module (I wrote this when I was first learning
    #python)
    tjd = met/86400.0 + 11910
    JD = tjd + 2400000.5 + 40000.0
    J_new = JD + 0.5
    j = int(J_new) + 32044
    g = j/146097
    dg = j - j/146097*146097
    c = (dg/36524 + 1)*3/4
    dc = dg - c*36524
    b = dc/1461
    db = dc - dc/1461*1461
    a = (db/365 + 1)*3/4
    da = db - a*365
    y = g*400 + c*100 +b*4 + a
    m = (da*5+308)/153 - 2
    d = da - (m+4)*153/5 + 122
    year = y - 4800 + (m+2)/12
    month = ((m+2) - (m+2)/12*12) + 1
    day = d+1
    if month < 10:
        month_str = str(0) + str(month)
    else:
        month_str = str(month)
    if day < 10:
        day_str = str(0) + str(day)
    else:
        day_str = str(day)
    date=str(year) + '-' + month_str + '-' + day_str
    hourdec = J_new - int(J_new)
    hour = int(hourdec * 24)
    if hour < 10:
        hour_str = str(0) + str(hour)
    else:
        hour_str = str(hour)
    mindec = hourdec * 24 - hour
    min = int(mindec * 60)
    if min < 10:
        min_str = str(0) + str(min)
    else:
        min_str = str(min)
    secdec = mindec * 60 - min
    sec = int(secdec * 60)
    if sec < 10:
        sec_str = str(0) + str(sec)
    else:
        sec_str = str(sec)
    # Decimal has to be written with a capital D
    sec_remain_str = Decimal(10e5 * (60*secdec - sec ))#[:str( 10e5 * (60*secdec - sec )).index('.')]
    sec_remain_str = Decimal(round(sec_remain_str,0))
    sec_remain_str = str(sec_remain_str)
    if len(sec_remain_str) < 6:
        sec_remain_str = str(0)*(6 - len(sec_remain_str)) + sec_remain_str
    if len(sec_remain_str) > 6:
        sec_remain_str = sec_remain_str[:6]
    if len(sec_remain_str) < 6:
        sec_remain_str = sec_remain_str + (6 - len(sec_remain_str)) * '0'
    time=hour_str + ':' + min_str + ':' + sec_str
    datetime=date + ' ' + time
    return datetime, sec_remain_str

def random_time_stamp(num_of_events):
    """
    Generated random time stamps for MySQL database
    """
    time_interval_start = time.mktime(time.strptime("Jan 01 2008", "%b %d %Y"))
    time_interval_end = time.mktime(time.strptime("Jan 01 2010", "%b %d %Y"))
    new_time_stamps = tuple(time.strftime("%Y-%m-%d %H:%M:%d",time.localtime(random_time)) for random_time in randint(time_interval_start,time_interval_end,num_of_events))
    return new_time_stamps
