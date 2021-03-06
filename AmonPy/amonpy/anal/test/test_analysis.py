#test_analysis.py
"""
@package test_analysis
Module for testing analysis modules.
"""
from __future__ import print_function
from builtins import str
import sys
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
from numpy import array, where, math
from multiprocessing import Pipe, Process
from time import time

from amonpy.dbase import db_read, db_write, db_delete
from amonpy.anal import cluster
from amonpy.dbase.db_classes import Alert, exAlertConfig
from amonpy.anal.analysis import anal


def test_anal():

    config = exAlertConfig()

    # set up the database connection
    HostFancyName='yourhostname' #'db.hpc.rcc.psu.edu'
    UserFancyName='yourusername'
    PasswordFancy='yourpass' #
    DBFancyName='AMON_test2'

    # read events from the database
    TimeSlice = timedelta.total_seconds(config.validStop - config.validStart)
    TimeStart = str(config.validStart)
    TimeStop  = str(config.validStop)
    t1 = time()
    events=db_read.read_event_timeslice(TimeStart,TimeSlice,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
    t2 = time()
    print()
    print(len(events), 'events have been read from the database')
    print('read time (s): ', t2-t1)
    print()

    # select out icecube only events (for testing)
    # by changing the following to if ev.stream == 0
    #events = [ev for ev in events if ev.stream!=-1]

    # put events in temporal order
    events = sorted(events,key=attrgetter('datetime'))

    # Launch the sever process
    (server,client) = Pipe()
    anal_p = Process(target=anal,args=((server,client),config))
    anal_p.start()

    alerts = []
    t1 = time()

    #loop over the list of events, calling analysis for each
    for ev in events:

        client.send(ev)
        #new_alerts = (client.recv())
        #if len(new_alerts) !=0:
        #    alerts += new_alerts

    client.send('get_alerts')
    alerts = client.recv()

    t2 = time()
    print()
    print('*** Alert generation complete***')
    print('    Time taken (sec): ', t2 -t1)
    print('    No. of alerts generated: ', len(alerts))
    print()

    #Close the server pipe in the client
    server.close()
    #Done. Close the pipe
    client.close()


if __name__ == "__main__":
    test_anal()
