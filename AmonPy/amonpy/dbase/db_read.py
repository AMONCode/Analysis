"""@package db_read
   Module to read:
  - single event from DB
  - arrays of events from a given time slice
  - single alert
  - alert timeslice
  - alertConfig
  - count the number of alerts
  - everything else form DB: pending ...
"""
from __future__ import print_function

from builtins import str
from builtins import range
import MySQLdb as mdb
import sys
import time
import datetime
import math
import string
#import numpy as np
from numpy import *
import pandas as pd

# amonpy imports
from amonpy.dbase import db_metadata
from amonpy.tools import convert_time
from amonpy.dbase import db_classes
from amonpy.dbase.db_classes import event_def

# build the simplest version of the Event class
#Event = event_def()


def read_event_single(event_stream, event_num, event_rev, host_name, user_name, passw_name, db_name):
    """ Read a given event from the DB. Input event stream name (char), event ID (int)
        event_Rev (int), host name, user name, password and DB name. """

    eventSingle=db_classes.Event(event_stream, event_num, event_rev)

    # use this later to make sure that column names are the same as the class name
    # attributes
    # exattr = ['forprint']
    #atlist = [attr for attr in dir(eventSingle) \
    #              if not (attr.startswith('_') or attr in exattr)]
    #for attr in atlist:
    #    print attr.ljust(20,' ')


    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    #if (eventSingle._Event__lock == False):

    try:
        print("Try to connect to DB: %s %s %s" % (event_stream, event_num, event_rev))
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('event', cur)
        num_columns=len(r[1])
        print("Connected")
        print('Number of columns in the table %d' %  num_columns)
        print()
        #print 'Column names:'
        #print

        #for ii in xrange(num_columns):
        #    print r[1][ii][0]
        #print

        cur.execute("""SELECT * FROM event WHERE eventStreamConfig_stream = %s AND
                    id = %s AND rev = %s""", (event_stream, event_num, event_rev))


        row = cur.fetchone()
        if row is not None:
            eventSingle.stream     =  event_stream   # defined by input
            eventSingle.id         =  event_num       # defined by input
            eventSingle.rev        =  event_rev      # defined by input
            eventSingle.datetime      =  row[3]
            eventSingle.datetime +=datetime.timedelta(microseconds=row[4]) # add microseconds
            eventSingle.dec        =  row[5]
            eventSingle.RA         = row[6]
            eventSingle.sigmaR   = row[7]
            eventSingle.nevents   = row[8]
            eventSingle.deltaT   =  row[9]
            eventSingle.sigmaT   =  row[10]
            eventSingle.false_pos  =  row[11]
            eventSingle.pvalue  =  row[12]
            eventSingle.type       = row[13]
            eventSingle.point_RA   = row[14]
            eventSingle.point_dec  =  row[15]
            eventSingle.longitude       =  row[16]
            eventSingle.latitude       =  row[17]
            eventSingle.elevation       =  row[18]
            eventSingle.psf_type          =row[19]
            eventSingle.configstream     = row[20]
            #eventSingle._Event__lock=True
        else:
            eventSingle=None
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        #print "Event %s %s %s failed to be read." % event_stream, event_num, event_rev
        cur.close()
        con.close()
        eventSingle=None
    return eventSingle



def read_event_timeslice(time_start,time_interval,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of events from the DB.
        Input start time (datetime), time window
       (in seconds), host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values
    eventList=[db_classes.Event(0, 0, 0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S.%f")
    timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    print('   Requested time slice: %s - %s' %(timeStart,timeStop))

    # **** Code to read the database column names is bellow****
    # **** Just print them out for now ****

    #if (eventSingle._Event__lock == False):

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('event', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")
        #print '    Number of columns in the table %d' %  num_columns
        #print
        #print '    Column names:'
        #print
        #for ii in xrange(num_columns):
        #    print '    ', r[1][ii][0]
        #print
        cur.execute("""SELECT * FROM event WHERE time>= %s AND
                    time <= %s""", (timeStart, timeStop))

        #print "  ...CONNECTED"
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].stream     = row[0]
            eventList[i].id         = row[1]
            eventList[i].rev        = row[2]
            eventList[i].datetime   = row[3]
            # add microseconds
            eventList[i].datetime  += datetime.timedelta(microseconds=row[4])
            eventList[i].dec        = row[5]
            eventList[i].RA         = row[6]
            eventList[i].sigmaR     = row[7]
            eventList[i].nevents    = row[8]
            eventList[i].deltaT     = row[9]
            eventList[i].sigmaT     = row[10]
            eventList[i].false_pos  = row[11]
            eventList[i].pvalue     = row[12]
            eventList[i].type       = row[13]
            eventList[i].point_RA   = row[14]
            eventList[i].point_dec  = row[15]
            eventList[i].longitude  = row[16]
            eventList[i].latitude   = row[17]
            eventList[i].elevation  = row[18]
            eventList[i].psf_type     = row[19]
            eventList[i].configstream     = row[20]
            #add a space for the next event
            eventList+=[db_classes.Event(0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def read_events_angle_separation(streams,angle,RA,Dec,host_name,user_name,passw_name,db_name):
    """ Get a list of events from the DB from a point in the sky with a distance of <angle.
        Input, streams, angle separation, RA and Dec of the point in the sky,
        host_name, user_name, password and DB name.
        Angles should be given in degrees; method will convert to radians.
    """
    eventList = [db_classes.Event(0,0,0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    num_streams=len(streams)

    selecStream = ""
    for s in streams:
        if s == streams[-1]:
            selecStream += "eventStreamConfig_stream = %d"%(s)
        else:
            selecStream += "eventStreamConfig_stream = %d OR "%(s)

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('event', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")

        cmd= "SELECT * FROM event WHERE ACOS(COS(RADIANS(`Dec`))*COS(RADIANS(%s))*COS(RADIANS(RA-%s))+SIN(RADIANS(`Dec`))*SIN(RADIANS(%s)))<RADIANS(%s) AND (%s)"%((str(Dec),str(RA), str(Dec), str(angle), selecStream))

        #cur.execute("""SELECT * FROM event WHERE
                    #ACOS(COS(RADIANS(`Dec`))*COS(RADIANS(%s))*COS(RADIANS(RA-%s))+SIN(RADIANS(`Dec`))*SIN(RADIANS(%s)))<RADIANS(%s)
                    #AND (%s)""", (str(Dec),str(RA), str(Dec), str(angle), selecStream))
        cur.execute(cmd)
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].stream     = row[0]
            eventList[i].id         = row[1]
            eventList[i].rev        = row[2]
            eventList[i].datetime   = row[3]
            # add microseconds
            eventList[i].datetime  += datetime.timedelta(microseconds=row[4])
            eventList[i].dec        = row[5]
            eventList[i].RA         = row[6]
            eventList[i].sigmaR     = row[7]
            eventList[i].nevents    = row[8]
            eventList[i].deltaT     = row[9]
            eventList[i].sigmaT     = row[10]
            eventList[i].false_pos  = row[11]
            eventList[i].pvalue     = row[12]
            eventList[i].type       = row[13]
            eventList[i].point_RA   = row[14]
            eventList[i].point_dec  = row[15]
            eventList[i].longitude  = row[16]
            eventList[i].latitude   = row[17]
            eventList[i].elevation  = row[18]
            eventList[i].psf_type     = row[19]
            eventList[i].configstream     = row[20]
            #add a space for the next event
            eventList+=[db_classes.Event(0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def read_event_timeslice_streams(streams,time_start,time_interval,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of events from specific streams the DB.
        Input start time (datetime), time window
       (in seconds), host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values
    eventList=[db_classes.Event(0, 0, 0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()
    try:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S.%f")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    except:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    print('   Requested time slice: %s - %s' %(timeStart,timeStop))

    # **** Code to read the database column names is bellow****
    # **** Just print them out for now ****

    #if (eventSingle._Event__lock == False):
    num_streams=len(streams)

    selecStream = ""
    for s in streams:
        if s == streams[-1]:
            selecStream += "eventStreamConfig_stream = %d"%(s)
        else:
            selecStream += "eventStreamConfig_stream = %d OR "%(s)

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('event', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")

        if num_streams == 1:
            stmt = ("""SELECT * FROM event WHERE time>= '{}' AND time <= '{}' AND eventStreamConfig_stream = {}""".format(timeStart, timeStop, streams[0]))
        else:
            stmt = ("""SELECT * FROM event WHERE (time>= '{}' AND time <= '{}') AND ({})""".format(timeStart, timeStop, selecStream))

        cur.execute(stmt)
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].stream     = row[0]
            eventList[i].id         = row[1]
            eventList[i].rev        = row[2]
            eventList[i].datetime   = row[3]
            # add microseconds
            eventList[i].datetime  += datetime.timedelta(microseconds=row[4])
            eventList[i].dec        = row[5]
            eventList[i].RA         = row[6]
            eventList[i].sigmaR     = row[7]
            eventList[i].nevents    = row[8]
            eventList[i].deltaT     = row[9]
            eventList[i].sigmaT     = row[10]
            eventList[i].false_pos  = row[11]
            eventList[i].pvalue     = row[12]
            eventList[i].type       = row[13]
            eventList[i].point_RA   = row[14]
            eventList[i].point_dec  = row[15]
            eventList[i].longitude  = row[16]
            eventList[i].latitude   = row[17]
            eventList[i].elevation  = row[18]
            eventList[i].psf_type     = row[19]
            eventList[i].configstream     = row[20]
            #add a space for the next event
            eventList+=[db_classes.Event(0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

# Difference between and previous function is that it looks for newer revisions only
def read_event_timeslice_streams_latest(streams,time_start,time_interval,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of events from specific streams from the DB. Only latest revisions will be read.
        Input start time (datetime), time window
       (in seconds), host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values
    eventList=[db_classes.Event(0, 0, 0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()
    try:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S.%f")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    except:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    print('   Requested time slice: %s - %s' %(timeStart,timeStop))

    # **** Code to read the database column names is bellow****
    # **** Just print them out for now ****

    #if (eventSingle._Event__lock == False):
    num_streams=len(streams)

    selecStream = ""
    for s in streams:
        if s == streams[-1]:
            selecStream += "eventStreamConfig_stream = %d"%(s)
        else:
            selecStream += "eventStreamConfig_stream = %d OR "%(s)

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('event', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")
        #print '    Number of columns in the table %d' %  num_columns
        #print
        #print '    Column names:'
        #print
        #for ii in xrange(num_columns):
        #    print '    ', r[1][ii][0]
        #print
        if num_streams == 1:
            stmt=("""SELECT * FROM event WHERE rev = (select max(rev) from event as e where e.eventStreamConfig_Stream=event.eventStreamConfig_Stream and e.id=event.id) AND time>= '{}' AND time <= '{}' AND eventStreamConfig_stream = {}""".format(timeStart, timeStop, streams[0]))
        else:
            stmt=("""SELECT * FROM event WHERE (rev = (select max(rev) from event as e where e.eventStreamConfig_Stream=event.eventStreamConfig_Stream and e.id=event.id) AND time>= '{}' AND time <= '{}') AND ({})""".format(timeStart, timeStop, selecStream))

        cur.execute(stmt)
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].stream     = row[0]
            eventList[i].id         = row[1]
            eventList[i].rev        = row[2]
            eventList[i].datetime   = row[3]
            # add microseconds
            eventList[i].datetime  += datetime.timedelta(microseconds=row[4])
            eventList[i].dec        = row[5]
            eventList[i].RA         = row[6]
            eventList[i].sigmaR     = row[7]
            eventList[i].nevents    = row[8]
            eventList[i].deltaT     = row[9]
            eventList[i].sigmaT     = row[10]
            eventList[i].false_pos  = row[11]
            eventList[i].pvalue     = row[12]
            eventList[i].type       = row[13]
            eventList[i].point_RA   = row[14]
            eventList[i].point_dec  = row[15]
            eventList[i].longitude  = row[16]
            eventList[i].latitude   = row[17]
            eventList[i].elevation  = row[18]
            eventList[i].psf_type     = row[19]
            eventList[i].configstream     = row[20]
            #add a space for the next event
            eventList+=[db_classes.Event(0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList
# read event config table and return results as a list of eventConfig class

def read_eventConfig(time_start, time_interval, host_name, user_name, passw_name, db_name):
    """ Read a list of event configurations from the DB. Input start time (datetime), time window
       (in seconds), host name, user name, password and DB name. """

# initiate event list, put dummy identifiers and replace them later with real values

    eventList=[db_classes.EventStreamConfig(0, 0)]

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S.%f")
    print(timeStart)
    timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    print(timeStop)



    try:
        print("Try to connect to DB")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('eventStreamConfig', cur)
        print(r[1][0][0])
        num_columns=len(r[1])
        print('    Number of columns in the table %d' %  num_columns)
        print()
        print('    Column names:')
        print()

        for ii in range(num_columns):
            print('    ', r[1][ii][0])
        print()
        cur.execute("""SELECT * FROM eventStreamConfig WHERE validStart>= %s AND
                           validStop >= %s""", (timeStart, timeStop))

        print("Connected")

        numrows = int(cur.rowcount)

        print("Number of rows selected: %d" % numrows)

        for i in range(numrows):
            print("i=%d" % i)

            row = cur.fetchone()
#                print row[0], row[1], row[2], row[3], row[4], row[5]
            eventList[i].stream     =  row[0]
            eventList[i].rev         =  row[1]
            eventList[i].validStart        =  row[2]
            eventList[i].validStop      =  row[3]
            eventList[i].observ_name = row[4]
            eventList[i].observ_coord_sys        =  row[5]
            eventList[i].astro_coord_sys         = row[6]
            eventList[i].point_type   = row[7]
            eventList[i].point   =  row[8]
            eventList[i].param1Desc  =  row[9]
            eventList[i].param2Desc  =  row[10]
            eventList[i].param3Desc =  row[11]
            eventList[i].psf_type       = row[12]
            eventList[i].psf   = row[13]
            eventList[i].skymap_val1Desc =  row[14]
            eventList[i].skymap_val2Desc       =  row[15]
            eventList[i].skymap_val3Desc       =  row[16]
            eventList[i].sensitivity_type       =  row[17]
            eventList[i].sensitivity          =row[18]
            eventList[i].fov_type          =row[19]
            eventList[i].fov         =row[20]
            eventList[i].ephemeris          =row[21]
            eventList[i].bckgr_type         =row[22]
            eventList[i].backgr          =row[23]
            eventList[i].mag_rigidity          =row[24]

            eventList+=[db_classes.EventStreamConfig(0, 0)] #add new event to the list and populate it
                                           # populate it for the next i values
            cur.close()
            con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    return eventList

def read_alert_single(alert_stream, alert_num, alert_rev, host_name, user_name, passw_name, db_name):
    """ Read a given alert from the DB. Input alert stream name (char), event ID (int)
        event_Rev (int), host name, user name, password and DB name. """

    alertSingle=db_classes.Alert(alert_stream, alert_num, alert_rev)

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    #if (alertSingle._Alert__lock == False):


    try:
        print("Try to connect to DB: %s %s %s" % (alert_stream, alert_num, alert_rev))
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('alert', cur)
        print("Connected")
        print(r[1][0][0])

        num_columns=len(r[1])
        print('    Number of columns in the table %d' %  num_columns)
        print()
        print('    Column names:')
        print()

        for ii in range(num_columns):
            print('    ', r[1][ii][0])
        print()
        cur.execute("""SELECT * FROM alert WHERE alertConfig_stream = %s AND
                    id = %s AND rev = %s""", (alert_stream, alert_num, alert_rev))

        row = cur.fetchone()

        alertSingle.stream     =  row[0]   # defined by input
        alertSingle.id         =  row[1]       # defined by input
        alertSingle.rev        =  row[2]     # defined by input
        alertSingle.datetime      =  row[3]
        alertSingle.datetime +=datetime.timedelta(microseconds=row[4]) # add microseconds
        alertSingle.dec        =  row[5]
        alertSingle.RA         = row[6]
        alertSingle.sigmaR   = row[7]
        alertSingle.nevents  =  row[8]
        alertSingle.deltaT  =  row[9]
        alertSingle.sigmaT       = row[10]
        alertSingle.false_pos   = row[11]
        alertSingle.observing  =  row[12]
        alertSingle.trigger       =  row[13]
        alertSingle.type       =  row[14]
        alertSingle.pvalue     =  row[15]
        alertSingle.skymap     =  row[16]
        alertSingle.anarev          =row[17]
        #alertSingle._Alert__lock=True
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("Event %s %s %s failed to be read." % (alert_stream, alert_num, alert_rev))
        cur.close()
        con.close()

    return alertSingle

def read_alert_timeslice_streams(streams,time_start,time_interval,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of alerts from the DB.
        Input start time (datetime), time window (in seconds),
        host name, user name, password and DB name. """

    # initiate event list, put dummy identifiers
    # and replace them later with real values
    alertList=[db_classes.Alert(0, 0, 0)]
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    try:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S.%f")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    except:
        timeStart=datetime.datetime.strptime(time_start,"%Y-%m-%d %H:%M:%S")
        timeStop=timeStart+datetime.timedelta(seconds=time_interval)
    print('   Requested time slice: %s - %s' %(timeStart,timeStop))

    num_streams=len(streams)

    selecStream = ""
    for s in streams:
        if s == streams[-1]:
            selecStream += "alertConfig_stream = %d"%(s)
        else:
            selecStream += "alertConfig_stream = %d OR "%(s)

    try:
        print("Try to connect to DB")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('alert', cur)
        print(r[1][0][0])

        num_columns=len(r[1])
        #print('    Number of columns in the table %d' %  num_columns)
        #print()
        #print('    Column names:')
        #print()

        #for ii in range(num_columns):
            #print('    ', r[1][ii][0])
        #print()

        if num_streams == 1:
            stmt = ("""SELECT * FROM alert WHERE time>= '{}' AND time <= '{}' AND alertConfig_stream = {} ORDER BY time ASC""".format(timeStart, timeStop, streams[0]))
        else:
            stmt = ("""SELECT * FROM alert WHERE (time>= '{}' AND time <= '{}') AND ({}) ORDER BY time ASC""".format(timeStart, timeStop, selecStream))

        cur.execute(stmt)
        print("Connected")
        numrows = int(cur.rowcount)
        print("Number of rows selected: %d" % numrows)

        for i in range(numrows):
            #print "i=%d" % i
            row = cur.fetchone()
            alertList[i].stream     = row[0]
            alertList[i].id         = row[1]
            alertList[i].rev        = row[2]
            alertList[i].datetime   = row[3]
            # add microseconds
            alertList[i].datetime  += datetime.timedelta(microseconds=row[4])
            alertList[i].dec        = row[5]
            alertList[i].RA         = row[6]
            alertList[i].sigmaR     = row[7]
            alertList[i].nevents    = row[8]
            alertList[i].deltaT     = row[9]
            alertList[i].sigmaT     = row[10]
            alertList[i].false_pos  = row[11]
            alertList[i].observing  = row[12]
            alertList[i].trigger    = row[13]
            alertList[i].type       = row[14]
            alertList[i].pvalue     = row[15]
            alertList[i].skymap     = row[16]
            alertList[i].anarev     = row[17]
            # add a space for the next alert
            alertList+=[db_classes.Alert(0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("Alerts failed to be read.")
        cur.close()
        con.close()
    alertList.pop()  # remove the last dummy event
    return alertList


def read_alertConfig(stream, rev, host_name, user_name, passw_name, db_name):
    """ Read a given alert configuration from the DB. Input stream name (char),
        Rev (int), host name, user name, password and DB name. """

    eventSingle=db_classes.AlertConfig(stream, rev)

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()



    if (stream > -1):

        try:
            print("Try to connect to DB: %s %s" % (stream, rev))
            mydb = db_metadata.DBMetadata()
            r=mydb.table_describe('alertConfig', cur)
            num_columns=len(r[1])
            print('    Number of columns in the table %d' %  num_columns)
            print()
            print('    Column names:')
            print()

            for ii in range(num_columns):
                print('    ', r[1][ii][0])
            print()
            cur.execute("""SELECT * FROM alertConfig WHERE stream = %s AND
                       rev = %s""", (stream, rev))

            print("Connected")

            row = cur.fetchone()

            eventSingle.stream     =  stream   # defined by input
            eventSingle.rev        =  rev      # defined by input
            eventSingle.validStart      =  row[2]
            eventSingle.validStop      =  row[3]
            eventSingle.participating      =  row[4]
            eventSingle.p_thresh        =  row[5]
            eventSingle.N_thresh         = row[6]
            eventSingle.deltaT   = row[7]
            eventSingle.cluster_method   =  row[8]
            eventSingle.sens_thresh   =  row[9]
            eventSingle.skymap_val1Desc   = row[10]
            eventSingle.skymap_val2Desc  =  row[11]
            eventSingle.skymap_val3Desc       =  row[12]
            eventSingle.bufferT       =          row[13]
            eventSingle.R_thresh       =         row[14]
            eventSingle.cluster_thresh       =   row[15]
            cur.close()
            con.close()
        except mdb.Error as e:
            print('Exception %s' %e)
            con.rollback()
            print("AlerConfig %s %s failed to be read." % stream, rev)
            cur.close()
            con.close()

    return eventSingle

def read_skymaps(event_stream, event_num, event_rev, host_name, user_name, passw_name, db_name):
    """ Read a given event skymap from the DB. Input event stream name (char), event ID (int)
        event_Rev (int), host name, user name, password and DB name. """

    #eventSingle=db_classes.Parameter(event_name,event_stream, event_num, event_rev)
    # initiate list with dummy parameters, remove it later
    skymaps = {}
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    #if (eventSingle._Event__lock == False):

    try:
        #print "Try to connect to DB: %s %s %s" % (event_stream, event_num, event_rev)
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('skyMapEvent', cur)
        num_columns=len(r[1])
        #print "Connected"
        #print 'Number of columns in the table %d' %  num_columns
        #print
        #print 'Column names:'
        #print

        #for ii in xrange(num_columns):
            #print r[1][ii][0]
        #print

        cur.execute("""SELECT location FROM skyMapEvent WHERE event_eventStreamConfig_stream = %s AND
                    event_id = %s AND event_rev = %s""", (event_stream, event_num, event_rev))

        numrows=int(cur.rowcount)
        evPars=[]
        for i in range(numrows):
            row = cur.fetchone()
            #eventSingle=db_classes.Parameter(row[0],event_stream,event_num,event_rev)
            # eventList[i].name       =  row[0]
            if 'fits' in row[0]:
                skymaps['skymap_fits'] = row[0]
            if 'png' in row[0]:
                skymaps['skymap_png'] = row[0]

        cur.close()
        con.close()
    except mdb.Error as e:
        #print 'Exception %s' %e
        con.rollback()
        #print "Event %s %s %s failed to be read." % event_stream, event_num, event_rev
        cur.close()
        con.close()
    #print "   %d rows read from the database" % len(eventList)
    return skymaps

def read_parameter_single(event_name,event_stream, event_num, event_rev, host_name, user_name, passw_name, db_name):
    """ Read a given event from the DB. Input event stream name (char), event ID (int)
        event_Rev (int), host name, user name, password and DB name. """

    eventSingle=db_classes.Parameter(event_name,event_stream, event_num, event_rev)

    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    #if (eventSingle._Event__lock == False):

    try:
        print("Try to connect to DB: %s %s %s %s" % (event_name, event_stream, event_num, event_rev))
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('parameter', cur)
        num_columns=len(r[1])
        print("Connected")
        print('Number of columns in the table %d' %  num_columns)
        print()
        print('Column names:')
        print()

        for ii in range(num_columns):
            print(r[1][ii][0])
        print()

        cur.execute("""SELECT * FROM parameter WHERE name = %s AND
                    event_eventStreamConfig_stream = %s AND
                    event_id = %s AND event_rev = %s""", (event_name, event_stream, event_num, event_rev))


        row = cur.fetchone()

        eventSingle.name       =  event_name      # defined by input
        eventSingle.event_eventStreamConfig_stream     =  event_stream   # defined by input
        eventSingle.event_id         =  event_num       # defined by input
        eventSingle.event_rev        =  event_rev      # defined by input
        eventSingle.value     =  row[1]
        eventSingle.units     =  row[2]

        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        #print "Event %s %s %s failed to be read." % event_stream, event_num, event_rev
        cur.close()
        con.close()

    return eventSingle


def read_parameters(event_stream, event_num, event_rev, host_name, user_name, passw_name, db_name):
    """ Read a given event from the DB. Input event stream name (char), event ID (int)
        event_Rev (int), host name, user name, password and DB name. """

    #eventSingle=db_classes.Parameter(event_name,event_stream, event_num, event_rev)
    # initiate list with dummy parameters, remove it later
    eventList=[db_classes.Parameter("energy",0, 0, 0)]
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    #if (eventSingle._Event__lock == False):

    try:
        #print "Try to connect to DB: %s %s %s" % (event_stream, event_num, event_rev)
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('parameter', cur)
        num_columns=len(r[1])
        #print "Connected"
        #print 'Number of columns in the table %d' %  num_columns
        #print
        #print 'Column names:'
        #print

        #for ii in xrange(num_columns):
            #print r[1][ii][0]
        #print

        cur.execute("""SELECT * FROM parameter WHERE event_eventStreamConfig_stream = %s AND
                    event_id = %s AND event_rev = %s""", (event_stream, event_num, event_rev))

        numrows=int(cur.rowcount)
        evPars=[]
        for i in range(numrows):
            row = cur.fetchone()
            #eventSingle=db_classes.Parameter(row[0],event_stream,event_num,event_rev)
            eventList[i].name       =  row[0]
            eventList[i].event_eventStreamConfig_stream     =  event_stream   # defined by input
            eventList[i].event_id         =  event_num       # defined by input
            eventList[i].event_rev        =  event_rev      # defined by input
            eventList[i].value     =  row[1]
            eventList[i].units     =  row[2]
            eventList+=[db_classes.Parameter("energy",0, 0, 0)]
            #evPars.append(eventSingle)
        cur.close()
        con.close()
    except mdb.Error as e:
        #print 'Exception %s' %e
        con.rollback()
        #print "Event %s %s %s failed to be read." % event_stream, event_num, event_rev
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    #print "   %d rows read from the database" % len(eventList)
    return eventList

def read_parameter_interval(stream_name,id_start,id_stop,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of parameters from the DB.
        Input stream, event id minimum and maximum, host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values

    eventList=[db_classes.Parameter("energy",0, 0, 0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    idStart=id_start
    idStop= id_stop
    stream = stream_name
    print('   Requested interval: %s - %s' %(idStart,idStop))

    # **** Code to read the database column names is bellow****
    # **** Just print them out for now ****

    #if (eventSingle._Event__lock == False):

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('parameter', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")

        cur.execute("""SELECT * FROM parameter WHERE event_eventStreamConfig_stream = %s AND
                    event_id>= %s AND event_id <= %s""", (stream_name,idStart, idStop))

        #print "  ...CONNECTED"
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].name     = row[0]
            eventList[i].value         = row[1]
            eventList[i].units        = row[2]
            eventList[i].event_eventStreamConfig_stream   = row[3]
            # add microseconds
            eventList[i].event_id  = row[4]
            eventList[i].event_rev        = row[5]

            eventList+=[db_classes.Parameter("energy",0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def read_parameter_interval_streams(streams_name,id_start,id_stop,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of parameters from the DB from a list of streams,
        within id intervals given in the lists id_start, id_stops for each of
        the stream respectively

    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values
    eventList=[db_classes.Parameter("energy", 0, 0, 0)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    idStart=id_start
    idStop  = id_stop
    streams = streams_name

    # **** Code to read the database column names is bellow****
    # **** Just print them out for now ****

    #if (eventSingle._Event__lock == False):
    num_streams=len(streams)
    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('parameter', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")
        #print '    Number of columns in the table %d' %  num_columns
        #print
        #print '    Column names:'
        #print
        #for ii in xrange(num_columns):
        #    print '    ', r[1][ii][0]
        #print
        if num_streams == 1:
            cur.execute("""SELECT * FROM event WHERE event_id>= %s AND
                        event_id <= %s AND
                        event_eventStreamConfig_stream = %s""", (idStart[0], idStop[0], streams[0]))
        elif num_streams == 2:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s))""",
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1]
                        ))
        elif num_streams == 3:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2]
                        ))
        elif num_streams == 4:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s)) OR
                        ((idStart[3]>= %s AND
                        idStop[3] <= %s) AND (event_eventStreamConfig_stream[3] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2],
                          idStart[3], idStop[3], streams[3]
                        ))
        elif num_streams == 5:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s)) OR
                        ((idStart[3]>= %s AND
                        idStop[3] <= %s) AND (event_eventStreamConfig_stream[3] = %s)) OR
                        ((idStart[4]>= %s AND
                        idStop[4] <= %s) AND (event_eventStreamConfig_stream[4] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2],
                          idStart[3], idStop[3], streams[3],
                          idStart[4], idStop[4], streams[4]
                        ))
        elif num_streams == 6:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s)) OR
                        ((idStart[3]>= %s AND
                        idStop[3] <= %s) AND (event_eventStreamConfig_stream[3] = %s)) OR
                        ((idStart[4]>= %s AND
                        idStop[4] <= %s) AND (event_eventStreamConfig_stream[4] = %s)) OR
                        ((idStart[5]>= %s AND
                        idStop[5] <= %s) AND (event_eventStreamConfig_stream[5] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2],
                          idStart[3], idStop[3], streams[3],
                          idStart[4], idStop[4], streams[4],
                          idStart[5], idStop[5], streams[5]
                        ))
        elif num_streams == 7:
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s)) OR
                        ((idStart[3]>= %s AND
                        idStop[3] <= %s) AND (event_eventStreamConfig_stream[3] = %s)) OR
                        ((idStart[4]>= %s AND
                        idStop[4] <= %s) AND (event_eventStreamConfig_stream[4] = %s)) OR
                        ((idStart[5]>= %s AND
                        idStop[5] <= %s) AND (event_eventStreamConfig_stream[5] = %s)) OR
                        ((idStart[6]>= %s AND
                        idStop[6] <= %s) AND (event_eventStreamConfig_stream[6] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2],
                          idStart[3], idStop[3], streams[3],
                          idStart[4], idStop[4], streams[4],
                          idStart[5], idStop[5], streams[5],
                          idStart[6], idStop[6], streams[6]
                        ))
        else:
            print('Maximum number of streams is 8 for now')
            cur.execute("""SELECT * FROM parameter WHERE ((idStart[0]>= %s AND
                        idStop[0] <= %s) AND (event_eventStreamConfig_stream[0] = %s) ) OR
                        ((idStart[1]>= %s AND
                        idStop[1] <= %s) AND (event_eventStreamConfig_stream[1] = %s)) OR
                        ((idStart[2]>= %s AND
                        idStop[2] <= %s) AND (event_eventStreamConfig_stream[2] = %s)) OR
                        ((idStart[3]>= %s AND
                        idStop[3] <= %s) AND (event_eventStreamConfig_stream[3] = %s)) OR
                        ((idStart[4]>= %s AND
                        idStop[4] <= %s) AND (event_eventStreamConfig_stream[4] = %s)) OR
                        ((idStart[5]>= %s AND
                        idStop[5] <= %s) AND (event_eventStreamConfig_stream[5] = %s)) OR
                        ((idStart[6]>= %s AND
                        idStop[6] <= %s) AND (event_eventStreamConfig_stream[6] = %s)) OR
                        ((idStart[7]>= %s AND
                        idStop[7] <= %s) AND (event_eventStreamConfig_stream[7] = %s))
                        """,
                         (idStart[0], idStop[0], streams[0],
                          idStart[1], idStop[1], streams[1],
                          idStart[2], idStop[2], streams[2],
                          idStart[3], idStop[3], streams[3],
                          idStart[4], idStop[4], streams[4],
                          idStart[5], idStop[5], streams[5],
                          idStart[6], idStop[6], streams[6],
                          idStart[7], idStop[7], streams[7]
                        ))

        #print "  ...CONNECTED"
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].name     = row[0]
            eventList[i].value         = row[1]
            eventList[i].units        = row[2]
            eventList[i].event_eventStreamConfig_stream   = row[3]
            eventList[i].event_id  = row[4]
            eventList[i].event_rev        = row[5]

            eventList+=[db_classes.Parameter("energy",0, 0, 0)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Events failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def alert_count(stream_name, table_name, host_name, user_name, passw_name, db_name):
    """
    Counts the number of alerts from a given stream.
    """
    count=0
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    try:
        cur.execute("""SELECT * FROM alert WHERE alertConfig_stream = %s""" %(stream_name,))
        con.commit()
        count+=cur.rowcount
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        print('   This alert stream is not deleted.')
        con.rollback()
        cur.close()
        con.close()
    return count

def rev_count(stream_name, host_name, user_name, passw_name, db_name):
    """
    Counts the revision number from a given stream in event table.
    """
    count=0
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    try:
        cur.execute("""SELECT max(rev) FROM event WHERE eventStreamConfig_stream = %s""" %(stream_name,))
        con.commit()
        row = cur.fetchone()
        count = row[0]
        print(count)
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        print('   No maximum revision. Check your table.')
        con.rollback()
        cur.close()
        con.close()
    return count

def stream_count_alertconfig(host_name, user_name, passw_name, db_name):
    """
    Counts the analysis stream number from a alertConfig table.
    """
    count=0
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    try:
        cur.execute("""SELECT max(stream) FROM alertConfig""")
        con.commit()
        row = cur.fetchone()
        count = row[0]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        print('   No maximum stream number. Check your table.')
        con.rollback()
        cur.close()
        con.close()
    return count

def alert_max_id(stream_name,host_name, user_name, passw_name, db_name):
    """
    Counts the number of alerts from a given stream.
    """
    count=0
    con = mdb.connect(host_name, user_name, passw_name, db_name)
    cur = con.cursor()

    try:
        cur.execute("""SELECT MAX(id) FROM alert WHERE alertConfig_Stream = %s""" % (stream_name,))
        con.commit()
        row = cur.fetchone()
        #print "max id %s" % (row,)
        count=row[0]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        print('   The max id was not read.')
        con.rollback()
        cur.close()
        con.close()
    return count

def read_alertline_events(streams,ids,revs,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of alertlines from the DB.
        Input streams, event ids and revesions, host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values

    eventList=[db_classes.AlertLine(-1, -1, -1, -1, -1, -1)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    idevent=ids
    rev = revs
    stream = streams

    try:
        print()
        print(" TRYING TO CONNECT TO THE DATABASE...")
        mydb = db_metadata.DBMetadata()
        r=mydb.table_describe('parameter', cur)
        num_columns=len(r[1])
        print("  ...CONNECTED")

        cur.execute("""SELECT * FROM alertLine WHERE event_eventStreamConfig_stream = %s AND
                    event_id= %s AND event_rev = %s""", (streams[0],idevent[0], rev[0]))
        #elif len(idevent) == 2:
        #     cur.execute("""SELECT * FROM alertLine WHERE event_eventStreamConfig_stream = %s AND
        #            event_id= %s AND event_rev = %s""", (streams[0],idevent[0], rev[0]))
        #print "  ...CONNECTED"
        numrows = int(cur.rowcount)
        print('   %d rows selected for reading' % numrows)

        for i in range(numrows):
            row = cur.fetchone()
            eventList[i].stream_alert     = row[0]
            eventList[i].id_alert         = row[1]
            eventList[i].rev_alert        = row[2]
            eventList[i].stream_event   = row[3]
            # add microseconds
            eventList[i].id_event  = row[4]
            eventList[i].rev_event        = row[5]
            eventList+=[db_classes.AlertLine(-1, -1, -1, -1, -1, -1)]
        cur.close()
        con.close()
    except mdb.Error as e:
        print('Exception %s' %e)
        con.rollback()
        print("   Alertlines failed to be read.")
        cur.close()
        con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def read_alertline_events2(streams,ids,host_name,user_name,
                         passw_name, db_name):
    """ Read a list of alertlines from the DB.
        Input streams, event ids, host name, user name, password and DB name.
    """

    # initiate event list, put dummy identifiers and replace
    # them later with real values

    eventList=[db_classes.AlertLine(-1, -1, -1, -1, -1, -1)]

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    cur = con.cursor()

    idevent=ids
    #rev = revs
    stream = streams

    if (len(idevent)==len(stream) and len(stream)>0):
        try:
            print()
            print(" TRYING TO CONNECT TO THE DATABASE...")
            mydb = db_metadata.DBMetadata()
            r=mydb.table_describe('alertLine', cur)
            num_columns=len(r[1])
            print("  ...CONNECTED")

            if len(stream)==1:
                cur.execute("""SELECT * FROM alertLine WHERE event_eventStreamConfig_stream = %s AND
                            event_id= %s""", (stream[0],idevent[0]))
            elif len(stream)==2:
                cur.execute("""SELECT * FROM alertLine WHERE (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) """, (stream[0],idevent[0],stream[1],idevent[1]))
            elif len(stream)==3:
                cur.execute("""SELECT * FROM alertLine WHERE (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s)""", (stream[0],idevent[0],stream[1],idevent[1],
                             stream[2],idevent[2]))
            elif len(stream)==4:
                cur.execute("""SELECT * FROM alertLine WHERE (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) """, (stream[0],idevent[0],stream[1],idevent[1],
                             stream[2],idevent[2],stream[3],idevent[3]))
            elif len(stream)==5:
                cur.execute("""SELECT * FROM alertLine WHERE (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) """, (stream[0],idevent[0],stream[1],idevent[1],
                             stream[2],idevent[2],stream[3],idevent[3], stream[4],idevent[4]))
            else:
                cur.execute("""SELECT * FROM alertLine WHERE (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) OR (event_eventStreamConfig_stream = %s AND
                            event_id= %s) """, (stream[0],idevent[0],stream[1],idevent[1],
                             stream[2],idevent[2],stream[3],idevent[3], stream[4],idevent[4],
                             stream[5],idevent[5]))

            numrows = int(cur.rowcount)
            print('   %d rows selected for reading' % numrows)

            for i in range(numrows):
                row = cur.fetchone()
                eventList[i].stream_alert     = row[0]
                eventList[i].id_alert         = row[1]
                eventList[i].rev_alert        = row[2]
                eventList[i].stream_event   = row[3]
                eventList[i].id_event  = row[4]
                eventList[i].rev_event        = row[5]
                eventList+=[db_classes.AlertLine(-1, -1, -1, -1, -1, -1)]
            cur.close()
            con.close()
        except mdb.Error as e:
            print('Exception %s' %e)
            con.rollback()
            print("   Alertlines failed to be read.")
            cur.close()
            con.close()
    eventList.pop()  # remove the last dummy event
    print("   %d rows read from the database" % len(eventList))
    return eventList

def get_latest_alert_info_from_event(alert_stream,event_id,host_name,user_name,passw_name, db_name):

    con = mdb.connect(host_name,user_name,passw_name,db_name)
    sql = 'SELECT alert_id, alert_rev from alertLine where alert_alertConfig_stream = {} and event_id = {}'.format(alert_stream,event_id)
    df = pd.read_sql(sql,con)

    max_rev = max(df['alert_rev'])
    alert_id = df['alert_id'][0]

    return alert_id, max_rev
