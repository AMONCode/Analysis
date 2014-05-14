"""@package convert_time
conversion between MJD time to timestamp needed for DB
modified from free code at 
http://www.atnf.csiro.au/people/Enno.Middelberg/python/python.html 
by g.t.
"""
import sys
import time
import datetime
import math
import string

def gettimestamp(jd):
    jd=jd+0.5+2400000.5
    Z=int(jd)
    F=jd-Z
    alpha=int((Z-1867216.25)/36524.25)
    A=Z + 1 + alpha - int(alpha/4)

    B = A + 1524
    C = int( (B-122.1)/365.25)
    D = int( 365.25*C )
    E = int( (B-D)/30.6001 )

    dd = B - D - int(30.6001*E) + F

    if E<13.5:
	mm=E-1

    if E>13.5:
	mm=E-13

    if mm>2.5:
	yyyy=C-4716

    if mm<2.5:
	yyyy=C-4715

    months=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    daylist=[31,28,31,30,31,30,31,31,30,31,30,31]
    daylist2=[31,29,31,30,31,30,31,31,30,31,30,31]

    h=int((dd-int(dd))*24)
    min=int((((dd-int(dd))*24)-h)*60)
    sec=86400*(dd-int(dd))-h*3600-min*60

    # Now calculate the fractional year. Do we have a leap year?
    if (yyyy%4 != 0):
	days=daylist2
    elif (yyyy%400 == 0):
	days=daylist2
    elif (yyyy%100 == 0):
	days=daylist
    else:
	days=daylist2

    if "-f" in sys.argv:
	daysum=0
	for y in range(mm-1):
	    daysum=daysum+days[y]
	daysum=daysum+dd-1

	if days[1]==29:
	    fracyear=yyyy+daysum/366
	else:
	    fracyear=yyyy+daysum/365
	print x+" = "+`fracyear`
    else:
	str1="%i-%i-%i" % (yyyy, months[mm-1],dd)
	str2=string.zfill(h,2)+":"+string.zfill(min,2)+":"+string.zfill(sec,2)
    str3=str1+" "+str2
    dt=datetime.datetime(yyyy, months[mm-1],int(dd),int(h),int(min),int(sec),int(float(sec-int(sec))*1000000))
    return dt, int(float(sec-int(sec))*1000000)
    
if __name__ == "__main__":
    mjd=50448.
    print ('MJD: %f') % (mjd) 
    print  gettimestamp(mjd) 