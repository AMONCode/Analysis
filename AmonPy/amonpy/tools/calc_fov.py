#!/usr/bin/env python
#calc_fov.py
"""@package calc_fov
    This is a top level script to run basic
    simulations for triggering observatories.

    It also injects a doublet of events that will form a triplet
    with a randomly chosen simulated event i.e. fake signal triplet

    Works with the Enthought Canopy package management

    Example: > python calc_fov.py dbaccess.txt

    where dbaccess.txt contans a string in dictionary format,
    containing the information required to access the database
    Modified to print Field of View overlap between streams
    0, 1, 3 and 7 (IceCube, ANTARES, Auger and HAWC)
"""
import sys

from time import time
from amonpy.dbase.db_classes import *
from amonpy.dbase import db_write, db_delete, db_read
from amonpy.sim import basic_sim, basic_sim_fov
import random

import wx
from amonpy.tools import dialog_choice
import ast

# Get the database access information
try:
    filename = sys.argv[1]
except:
    filename = 'dbaccess.txt'
file = open(filename)
line = file.readline()
db = ast.literal_eval(line)
file.close()
HostFancyName=db['host']
UserFancyName=db['user']
PasswordFancy=db['password']
DBFancyName=db['database']
print()
print('using database access file: ',filename)
print(' host: '.ljust(10), db['host'])
print(' user: '.ljust(10), db['user'])
print(' password: '.ljust(10), db['password'])
print(' database: '.ljust(10), db['database'])
print()

# identify what to do with output of simulation
choices = ['Do not write to DB','Overwrite event streams',
           'Append events/new rev', 'Cancel']
result_dialog=''
result_dialog = dialog_choice.SelectChoice(choices).result
if result_dialog=='Cancel':
    print()
    print('Cancelling simulation')
    print()
    sys.exit()
print()

# read in the configuration for this run (example only - for now)
# simulate the IceCube, ANTARES, and HAWC event streams
streams=[0,1,7]
num_streams=len(streams)
print('Number of streams: %s' % num_streams)
revisions=[0,0,0]
conf = [simstream(streams[0]), simstream(streams[1]), simstream(streams[2])]
#conf = [simstream(streams[0])]
# hardcoded alert analysis stream for now
streams_alert=[1]

#################################
# EXECUTION OF MAIN SIM CODE
#results=basic_sim.basic_sim(conf)
#################################


if result_dialog==choices[0]:
    print('Simulations will not be written to DB')
    results=basic_sim_fov.signal_inject(conf,revisions)
elif result_dialog==choices[1]:
    print('Overwriting event streams in the DB')
    results=basic_sim_fov.signal_inject(conf, revisions)
    for i in range(len(streams)):
        print('...stream number %d' % streams[i])
        k=streams[i]
        db_delete.delete_alertline_stream_by_event(streams[i],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)
        #db_delete.delete_alert_stream(streams[i],HostFancyName,
         #                   UserFancyName,PasswordFancy,DBFancyName)
        db_delete.delete_event_stream(streams[i],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)

    for j in range(len(streams_alert)):
        print('...stream number %d' % streams_alert[j])
        db_delete.delete_alert_stream(streams_alert[j],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)

    db_write.write_event(1,HostFancyName,UserFancyName,
                            PasswordFancy,DBFancyName, results)
elif result_dialog==choices[2]:
    print('Simulations will be appended to DB')
    print()
    print('Check if the database is for MC')
    if not (DBFancyName=='AMON_test2'):
        print('This is not MC database. Terminating.')
        sys.exit(0)
    else:
        for ii in range(num_streams):
            revisions[ii]=db_read.rev_count(streams[ii],HostFancyName, UserFancyName,PasswordFancy,DBFancyName)
        #print rev_count(streams[0],HostFancyName, UserFancyName,
                                                  #PasswordFancy,DBFancyName)
            print("Max revision for stream %s is %s" % (streams[ii], revisions[ii]))
            revisions[ii]+=1
            print("New revision for stream %s is %s" % (streams[ii], revisions[ii]))
        results=basic_sim_fov.signal_inject(conf,revisions)
        db_write.write_event(1,HostFancyName,UserFancyName,
                            PasswordFancy,DBFancyName, results)
        #sys.exit(0)
    #print 'This option is not supported yet, terminating.'
    #sys.exit(0)
    # need to:
    # 1. Somewhere check that we are using a simulations database
    # 2. Identify lowest unsused rev number
    # 3. Pass this rev number to the simulation code
else:
    print('Terminating')
    sys.exit(0)
