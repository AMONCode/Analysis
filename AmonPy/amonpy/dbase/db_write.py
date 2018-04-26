"""@package db_write
 Module to write into database event, parameter, eventStreamConfig, alert, alertConfig
 and alertline tables.
"""
import MySQLdb as mdb
import sys
import time
import datetime
import math
import string
import numpy as np

# amonpy imports
from amonpy.tools import convert_time
from amonpy.tools.misctools import perc_done
from amonpy.dbase import db_classes


def write_event_archive(real_archive, stream_num, host_name, user_name, passw_name, db_name, filename):
    """ Write archival data to DB, only ICeCube-40 for now
    """
# connect to database
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

# real_archive==0 archival data, otherwise real-time
# stream_num=0 is IceCube

    if real_archive==0:
        if stream_num==0:
#            a1,a2,a3,a4,a5,a6 =loadtxt('../../../data/icecube/IC40/IceCube-40',
#                                       unpack=True, usecols=[0,1,2,3,4,8])
            a1,a2,a3,a4,a5 =loadtxt(filename, unpack=True, usecols=[0,1,2,4,5])

# write miliseconds in delta T column

            NEVENTS=len(a1)
            print 'Number of events in the file: %d' % NEVENTS
            source_type='observation'
            count=0
            num=0
            for i in range(NEVENTS):
# read in upward going muons only
                if a1[i]>-0.0001:
                    st, milisec=convert_time.gettimestamp(a5[i])
#                    print st
                    num=num+1
#                    print num
                    try:
                        cur.execute("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                   %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num,num,0,st, milisec,
                                   a1[i],a2[i],a4[i],1,0.0,0.000001,0.000065,0.96,source_type,a4[i],a4[i],
                                   -89.99,-63.453056,-2000.,'fisher',0))
                        con.commit()
                        count+=cur.rowcount
                    except mdb.Error, e:
                        print 'Exception %s' %e
                        print 'Something is wrong with this event %d, exception...' % num
                        print 'This event is not written.'
                        con.rollback()
                else:
                    pass
            print "Number of rows written: %d" % count

            con.close()
    elif real_archive==1: # MC event
        pass # create new function for both MC and real time
    else:
        print "This is not archival event"
        sys.exit(0)

# write Event and SimEvent : real-time, MC events

def write_event(real_archive, host_name, user_name, passw_name, db_name, eventlist):
    """ Write event list to DB from MC and real-time data streams"""
# connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

# real_archive==0 archival data, otherwise real-time

    NEVENTS=len(eventlist)
    print 'Number of events to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (eventlist[i].stream >-1):
            try:
                if '.' in str(eventlist[i].datetime):
                    microsec=int(float('.'+str(eventlist[i].datetime).split('.')[1])*1000000)
                #print 'microseconds %d' % microsec
                else:
                    microsec=0
                cur.execute("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(eventlist[i].stream,eventlist[i].id,
                            eventlist[i].rev,eventlist[i].datetime, microsec,
                            eventlist[i].dec,eventlist[i].RA, eventlist[i].sigmaR, eventlist[i].nevents,
                            eventlist[i].deltaT,eventlist[i].sigmaT,eventlist[i].false_pos,
                            eventlist[i].pvalue,eventlist[i].type,eventlist[i].point_RA,
                            eventlist[i].point_dec,eventlist[i].longitude, eventlist[i].latitude,
                            eventlist[i].elevation,eventlist[i].psf_type,0))
                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Something is wrong with this event %d ' % eventlist[i].id
                print 'Exception %s' %e
                con.rollback()
            pd = perc_done(i,NEVENTS,2)
            if pd != -1: print pd
        else:
            print 'Invalide stream number'

    print "Number of rows written: %d" % count

    con.close()
    cur.close()

def write_parameter_list(host_name, user_name, passw_name, db_name, paramlist):
    """ Write parameter list to DB from MC and real-time data streams"""

    # connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    NEVENTS=len(paramlist)
    print 'Number of events to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (paramlist[i].event_eventStreamConfig_stream >-1):
            try:
                cur.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",
                           (paramlist[i].name,paramlist[i].value,
                            paramlist[i].units,paramlist[i].event_eventStreamConfig_stream,
                            paramlist[i].event_id,paramlist[i].event_rev))
                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Something is wrong with this parameter %d ' % paramlist[i].event_id
                print 'Exception %s' %e
                con.rollback()
            pd = perc_done(i,NEVENTS,2)
            if pd != -1: print pd
        else:
            print 'Invalide stream number'

    print "Number of rows written: %d" % count

    con.close()
    cur.close()

def write_parameter(real_archive, stream_num, host_name, user_name, passw_name, db_name, filename):
    """
    Write into parameter table in DB. Archival IceCube-40 data only supported for now.
    """
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

# real_archive==0 archival data, otherwise real-time

    if real_archive==0:
        if stream_num==0:
#           a1,a2,a3,a4,a5,a6 =loadtxt('../../data/icecube/IC-40/IC40_finalPS_Public_NoPoles.txt',
#                                       unpack=True, usecols=[0,1,2,3,4,8])

            a1,a2,a3,a4,a5 =loadtxt(filename, unpack=True, usecols=[0,1,2,4,5])

            NEVENTS=len(a1)
            print 'Number of events in the file: %d' % NEVENTS
            source_type='observation'
            count=0
            num=0
            for i in range(NEVENTS):
# read in upward going muons only
                if a1[i]>-0.0001:
                    num=num+1
                    st, milisec=convert_time.gettimestamp(a5[i])
#                    print st
                    try:
#                   cur.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",('ene_loss',
#                              stream_name,num,0, a3[i],'GeVm^{-1}'))
                        cur.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",('ene',
                                    a3[i],'GeV',stream_num,num,0))

                        con.commit()
                        count+=cur.rowcount
                    except mdb.Error, e:
                        print 'Exception %s' %e
                        print "Something is wrong with this event %d, exception..." % num
                        con.rollback()
                else:
                    pass
            print "Number of rows written: %d" % count
            con.close()

    else:
        print "Real time or MC, not ready yet"
        sys.exit(0)

def write_event_config_archive(stream_num, host_name, user_name, passw_name, db_name):
    """
    Write into eventStreamConfig table for the archival data.
    Stream 0 = singlets (subthreshol), 10 = HESE, 11 EHE, 12 MASTER OFU, 13 ASAS-SN OFU, 14 LCGOT OFU, 15 PTF OFU, 16 MAGIC GFU, 17 GFU, 18 GFU, 19 GFU, 20 GFU
    Stream 4 = Swift,
    Stream 5 = FACT
    """
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()
    if stream_num==0:
        obs_name='IceCube'
        try:
            cur.execute("""INSERT INTO eventStreamConfig VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num,0, '2008-01-01 00:00:00',
            '2009-06-01 00:00:00',obs_name, 'UTC-GEOD-TOPO','UTC-ICRS-TOPO','ground-based','point.dat','0','0','0'
            ,'fisher','psf.dat','0','0','0','','sens.dat','circle','75','0',
            'tabulated','bckgr.dat','0'))
            con.commit()
        except mdb.Error, e:
            print 'Exception %s' %e
            print 'Something went wrong, no data are written.'
            con.rollback()

        con.close()
    
    #elif ((stream_num>=10) and (stream_num<=20)):
    elif ((stream_num==10) or (stream_num==11) or (stream_num==12) or (stream_num==13) or (stream_num==14) or (stream_num==15) or (stream_num==16) or (stream_num==17) or (stream_num==18) or (stream_num==19) or (stream_num==20)):
        obs_name='IceCube'
        try:
            cur.execute("""INSERT INTO eventStreamConfig VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num,0, '2016-02-01 00:00:00',
            '2026-01-01 00:00:00',obs_name, 'UTC-GEOD-TOPO','UTC-ICRS-TOPO','ground-based','point.dat','0','0','0'
            ,'fisher','psf.dat','0','0','0','','sens.dat','circle','75','0',
            'tabulated','bckgr.dat','0'))
            con.commit()
        except mdb.Error, e:
            print 'Exception %s' %e
            print 'Something went wrong, no data are written.'
            con.rollback()

        con.close()

    elif stream_num==4:
        obs_name='Swift'
        try:
            cur.execute("""INSERT INTO eventStreamConfig VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num,0, '2008-01-01 00:00:00',
            '2009-12-31 00:00:00',obs_name, 'UTC-GEOD-TOPO','UTC-ICRS-TOPO','ground-based','point.dat','0','0','0'
            ,'fisher','psf.dat','0','0','0','','sens.dat','circle','75','0',
            'tabulated','bckgr.dat','0'))
            con.commit()
        except mdb.Error, e:
            print 'Exception %s' %e
            print 'Something went wrong, no data are written.'
            con.rollback()

        con.close()

    elif stream_num==5:
        obs_name='FACT'
        try:
            cur.execute("""INSERT INTO eventStreamConfig VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num,0, '2008-01-01 00:00:00',
            '2009-12-31 00:00:00',obs_name, 'UTC-GEOD-TOPO','UTC-ICRS-TOPO','ground-based','point.dat','0','0','0'
            ,'fisher','psf.dat','0','0','0','','sens.dat','circle','75','0',
            'tabulated','bckgr.dat','0'))
            con.commit()
        except mdb.Error, e:
            print 'Exception %s' %e
            print 'Something went wrong, no data are written.'
            con.rollback()

        con.close()

    else:
        print "Not ready for other streams. Only IceCube, Swift, and FACT for now."
        con.close()
        cur.close()

def write_event_config(stream_num, host_name, user_name, passw_name, db_name, eventlist):
    """ Write event config list to DB table eventStreamConfig """
# connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

# real_archive==0 archival data, otherwise real-time

    NEVENTS=len(eventlist)
    print 'Number of event configurations to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (stream_num[i]>-1):
            print stream_num[i]
            try:
                # microsec_start=int(float('.'+str(eventlist[i].config.validStart).split('.')[1])*1000000)
                #microsec_end=int(float('.'+str(eventlist[i].config.validStop).split('.')[1])*1000000)
                #print 'microseconds %d' % microsec
                #print eventlist[i].validStart
                #eventlist[i].forprint()
                print (stream_num[i],eventlist[i].rev,
                            eventlist[i].validStart,eventlist[i].validStop, eventlist[i].observ_name,
                            eventlist[i].observ_coord_sys,eventlist[i].astro_coord_sys,
                            eventlist[i].point_type,eventlist[i].point,
                            eventlist[i].param1Desc,eventlist[i].param2Desc,
                            eventlist[i].param3Desc,eventlist[i].psf_type,
                            eventlist[i].psf,eventlist[i].skymap_val1Desc,
                            eventlist[i].skymap_val2Desc,eventlist[i].skymap_val3Desc,
                            eventlist[i].sensitivity_type, eventlist[i].sensitivity,
                            eventlist[i].fov_type, eventlist[i].fov,eventlist[i].ephemeris,
                            eventlist[i].bckgr_type,eventlist[i].bckgr,
                            eventlist[i].mag_rigidity)
                cur.execute("""INSERT INTO eventStreamConfig VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num[i],eventlist[i].rev,
                            eventlist[i].validStart,eventlist[i].validStop, eventlist[i].observ_name,
                            eventlist[i].observ_coord_sys,eventlist[i].astro_coord_sys,
                            eventlist[i].point_type,eventlist[i].point,
                            eventlist[i].param1Desc,eventlist[i].param2Desc,
                            eventlist[i].param3Desc,eventlist[i].psf_type,
                            eventlist[i].psf,eventlist[i].skymap_val1Desc,
                            eventlist[i].skymap_val2Desc,eventlist[i].skymap_val3Desc,
                            eventlist[i].sensitivity_type, eventlist[i].sensitivity,
                            eventlist[i].fov_type, eventlist[i].fov,eventlist[i].ephemeris,
                            eventlist[i].bckgr_type,eventlist[i].bckgr,
                            eventlist[i].mag_rigidity))
                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Exception %s' %e
                print 'Something is wrong with this event config %d, exception...' % eventlist[i].rev
                print 'This eventconfig  is not written.'
                con.rollback()
        else:
            print 'Not ready for these event config yet'

    print "Number of rows written: %d" % count

    con.close()
    cur.close()

def write_alert(stream_name,host_name, user_name, passw_name, db_name, eventlist):
    """ Write alert list to DB from MC and real-time data streams"""
# connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    NEVENTS=len(eventlist)
    print '   Number of alerts to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (eventlist[i].stream == stream_name):
            try:
                if ('.' in str(eventlist[i].datetime)):
                    microsec=int(float('.'+str(eventlist[i].datetime).split('.')[1])*1000000)
                else:
                    microsec=0
                cur.execute("""INSERT INTO alert VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s)""",(eventlist[i].stream,eventlist[i].id,
                            eventlist[i].rev,eventlist[i].datetime, microsec,
                            eventlist[i].dec,eventlist[i].RA,eventlist[i].sigmaR, eventlist[i].nevents,
                            eventlist[i].deltaT,eventlist[i].sigmaT,eventlist[i].false_pos,
                            eventlist[i].observing,eventlist[i].trigger,eventlist[i].type,
                            eventlist[i].pvalue,eventlist[i].skymap, eventlist[i].anarev))
                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Something is wrong with this alert %d ' % eventlist[i].id
                print 'Exception %s' %e
                print '   This alert is not written.'
                con.rollback()
        else:
            print '   Invalid stream ID'

    print "   Number of rows written: %d" % count

    con.close()
    cur.close()

def write_alert_config(stream_num, host_name, user_name, passw_name, db_name, eventlist):
    """ Write alert config list to DB """
# connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

# real_archive==0 archival data, otherwise real-time

    NEVENTS=len(eventlist)
    print 'Number of event configurations to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (stream_num[i]>-1):
            print stream_num[i]
            try:

                cur.execute("""INSERT INTO alertConfig VALUES (%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(stream_num[i],eventlist[i].rev,
                            eventlist[i].validStart, eventlist[i].validStop,
                            eventlist[i].participating,eventlist[i].p_thresh,
                            eventlist[i].N_thresh, eventlist[i].deltaT, eventlist[i].cluster_method,
                            eventlist[i].sens_thresh,
                            eventlist[i].skymap_val1Desc, eventlist[i].skymap_val2Desc,
                            eventlist[i].skymap_val3Desc, eventlist[i].bufferT,
                            eventlist[i].R_thresh, eventlist[i].cluster_thresh))

                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Exception %s' %e
                print 'Something is wrong with this event config %d, exception...' % eventlist[i].rev
                print 'This eventconfig  is not written.'
                con.rollback()
        else:
            print 'Not ready for these event config yet'

    print "Number of rows written: %d" % count

    con.close()
    cur.close()

def write_alertline(host_name, user_name, passw_name, db_name, eventlist):
    """ Write alertline list to DB from MC and real-time data streams"""
# connect to database

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    NEVENTS=len(eventlist)
    print '   Number of alert lines to be written: %d' % NEVENTS
    count=0

    for i in range(NEVENTS):
        if (eventlist[i].stream_alert >-1):
            try:
                #microsec=int(float('.'+str(eventlist[i].datetime).split('.')[1])*1000000)
 #               print 'microseconds %d' % microsec
                cur.execute("""INSERT INTO alertLine VALUES (%s,%s,%s,%s,%s,%s)""",
                           (eventlist[i].stream_alert,eventlist[i].id_alert,
                            eventlist[i].rev_alert,eventlist[i].stream_event,
                            eventlist[i].id_event,eventlist[i].rev_event))
                con.commit()
                count+=cur.rowcount
            except mdb.Error, e:
                print 'Exception %s' %e
                print '   Something is wrong with this alert line %d, exception...' % eventlist[i].id_event
                print '   This alert line is not written.'
                con.rollback()
        else:
            print '   Invalid stream ID'

    print "   Number of rows written: %d" % count

    con.close()
    cur.close()
