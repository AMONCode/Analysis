"""@package Met2Utc_Fermi
    Module with Fermi specific function:
        -converts Fermi Mission Elapsed Time (MET) to UTC
"""

#Edited for Fermi by: Michael Toomey <mwt5345@psu.edu> 2/9/2015
#WARNING:Only use for Fermi data, not compatable with Swift MET data. Use swift_funtions.py instead.
#Original Author of Swift Met2Utc: Cody Messick <cody.messick@psu.edu>
#Original script for Swift: /Analysis/AmonPy/amonpy/dbase/detector_specific/swift_functions.py

from decimal import Decimal

def Met2Utc_Fermi(met):
        """ 
            Converts from Fermi MET time to time stamp needed by AMON database 
        """
        #Accounts for leap seconds from Fermi MET so it can be converted to correct UTC.
        #Note: Accurate up to leap second of June 30, 2015. Last edited 2/9/2015. Any subsequent leap second must be added. 
        t = met
        if t >= 457401604:
            q = t - 4
        elif t>= 362793603:
            q = t - 3
        elif t>= 252460802:
            q = t - 2
        elif t>= 157766401:
            q = t - 1
        else:
            q = t
        #Converts MET to UTC    
        tjd = q/86400.0 + 11910
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
        timel=hour_str + ':' + min_str + ':' + sec_str
        datetime=date + ' ' + timel
        return datetime, sec_remain_str