#run_amon_archive.py
"""@package run_amon_archival
Old module for running archival clustering analysis.
"""
from __future__ import print_function
from builtins import str
from builtins import range
import sys
from time import time
from amonpy.dbase import db_read, db_write, db_delete
from amonpy.anal import cluster
from amonpy.dbase.db_classes import Alert

from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
from numpy import array, where, math


def amon_archival():
    # Establish start and stop periods
    # These could ultimately be taken from a configuration: 
    #start = sys.argv[1]
    #stop  = sys.argv[2]
    start = datetime(2000,1,1,0,0,0,0)
    stop  = datetime(2013,1,1,0,0,0,0)
    TimeSlice = timedelta.total_seconds(stop - start)
    #TimeSlice = 10000.
    TimeStart = str(start)
    TimeStop  = str(stop)

    # set up the database connection
    HostFancyName='db.hpc.rcc.psu.edu'
    UserFancyName='yourname' 
    PasswordFancy='yourpass' 
    DBFancyName='AMON_test2'

    # read events from the database
    t1 = time()
    events=db_read.read_event_timeslice(TimeStart,TimeSlice,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
    t2 = time()
    print()
    print(len(events), 'events have been read from the database') 
    print('read time (s): ', t2-t1)
    print()

    # select out icecube only events (for testing)
    events = [ev for ev in events if ev.stream!=-1]
    print('Events: ', len(events))


    # put events in temporal order
    events = sorted(events,key=attrgetter('datetime'))

    # since events are in temporal order, we need only
    # look into the future for coincidence pairs

    # maxmimum deltaT, Nsigma should be read  from a config table
    # but just set it for now
    deltaTmax = 100.
    Nsigma_max= 2.
    alerts = []
    stream_num = 1 # stream name, !=0 is archival, 0 real-time

    # build candidate alerts, derived from cluster object
    Nevents = len(events)
    #for testing...
    #Nevents = 5000
    for ii in range(Nevents):
        jj = ii + 1
        deltaT = 0.
        while ((deltaT < deltaTmax) and (jj < Nevents)):
            deltaT =timedelta.total_seconds(events[jj].datetime-events[ii].datetime)
            if (deltaT <= deltaTmax):
                f = cluster.Fisher(events[jj],events[ii])
                if (f.Nsigma <= Nsigma_max):
                    # create alert, with id next in the buffered list
                    id = len(alerts)              
                    new_alert = Alert(stream_num,id,0)
                                    
                    # calculate trigger information
                    triggers = 0
                    trg = list(set([events[ii].stream,events[jj].stream]))
                    for t in trg: triggers+= 2**t                 
                    new_alert.trigger = triggers

                    # populate non-spatial part of alert
                    new_alert.datetime = events[ii].datetime
                    new_alert.deltaT = deltaT
                    new_alert.nevents = 2

                    # populate spatial results from Fisher class
                    new_alert.RA = f.ra0
                    new_alert.dec = f.dec0
                    new_alert.psf_part1 = f.sigmaW
                
                    # information not currently in the Alert class
                    new_alert.Nsigma = f.Nsigma
                    new_alert.psi = f.psi 
                    new_alert.event_stream = [events[ii].stream,events[jj].stream]
                    new_alert.event_id = [events[ii].id,events[jj].id]
                    new_alert.event_rev = [events[ii].rev,events[jj].rev]
                    
                    
                    new_alert.event_id = [events[ii].id,events[jj].id]
                    new_alert.event_rev = [events[ii].rev,events[jj].rev]
                    new_alert.psi1 = f.psi1
                    new_alert.psi2 = f.psi2
                    new_alert.pos = [[events[ii].RA,events[ii].dec],
                                     [events[jj].RA,events[jj].dec]]
                    # to be loaded from config in the future                 
                    new_alert.anastream=new_alert.stream
                    new_alert.anarev=0                 
                                 
                    # add alert to the buffered alert list
                    alerts +=[new_alert]
                    #new_alert.forprint()
                
                    #print   
                              
            jj+=1
    return stream_num, alerts            
             
if __name__ == "__main__":

    t1 = time()
    stream_num, alerts = amon_archival()     
    t2 = time()
    print()
    print('*** Alert generation complete***')
    print('    Time taken (sec): ', t2 -t1) 
    print('    No. of alerts generated: ', len(alerts))
    print()

    
