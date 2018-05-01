"""@package create_voevents
Create test VOEvents by reading events from DB
use this VOEvents to test AMON server and real-time analysis
"""
from __future__ import absolute_import
import sys

from datetime import datetime, timedelta

import amonpy.dbase.db_read as db_read
from amonpy.dbase.db_classes import Event, Parameter
import amonpy.dbase.event_to_voevent as event_to_voevent

HostFancyName='localhost'
UserFancyName='root'
PasswordFancy='***REMOVED***'
DBFancyName='AMON_test2'

event_streams = [0,1,3,7]

validStart = datetime(2012,1,1,0,0,0,0)
validStop = datetime(2013,1,1,0,0,0,0)
TimeSlice = timedelta.total_seconds(validStop - validStart)

TimeStart = str(validStart)
TimeStop  = str(validStop)


events=db_read.read_event_timeslice_streams(event_streams, TimeStart,TimeSlice,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
#parameters = []
nevents=len(events)

##Make fname a variable

for kk in xrange(nevents):
    parameters=[Parameter("energy",events[kk].stream, events[kk].id, events[kk].rev)]

    xml1=event_to_voevent.event_to_voevent([events[kk]], parameters)
    #print xml1
    fname = ''
    if (events[kk].stream == 0):
        fname='/Users/hugo/AMON/Test_DB/server_tmp_events/events_icecube/event_%s.xml' % (kk,)
    elif (events[kk].stream == 1):
        fname='/Users/hugo/AMON/Test_DB/server_tmp_events/events_antares/event_%s.xml' % (kk,)
    elif (events[kk].stream == 3):
        fname='/Users/hugo/AMON/Test_DB/server_tmp_events/events_auger/event_%s.xml' % (kk,)
    elif (events[kk].stream == 7):
        fname='/Users/hugo/AMON/Test_DB/server_tmp_events/events_hawc/event_%s.xml' % (kk,)
    else:
        print "unsupported stream for now"
        pass
    print fname
    f1=open(fname, 'w+')
    f1.write(xml1)
    f1.close()
