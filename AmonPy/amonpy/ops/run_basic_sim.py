#!/usr/bin/env python
#run_basic_sim.py
"""@package run_basic_sim
    This is a top level script to run basic
    simulations for triggering observatories.

    Optionally, it also injects a pair of doublets that will form 2 triplets
    with randomly chosen simulated events i.e. 2 fake signal triplets

    Works with the Enthought Canopy package management

    Example: > python run_basic_sim.py dbaccess.txt

    where dbaccess.txt contans a string in dictionary format,
    containing the information required to access the database
"""
import sys
import ast
import wx
import random
from time import time

from amonpy.dbase.db_classes import *
from amonpy.dbase import db_write
from amonpy.sim import basic_sim
from amonpy.dbase import db_delete
from amonpy.dbase import db_read
from amonpy.tools import dialog_choice

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
print
print 'using database access file: ',filename
print ' host: '.ljust(10), db['host']
print ' user: '.ljust(10), db['user']
print ' password: '.ljust(10), db['password']
print ' database: '.ljust(10), db['database']
print

# run a basic simulation or run the same simulation with the three fake coincidences
# injected

choice_sim = ['Basic simulation','Basic simulation with fake signal', 'Cancel']
result_sim = ''
result_sim = dialog_choice.SelectChoice(choice_sim).result
if result_sim=='Cancel':
    print
    print 'Cancelling simulation'
    print
    sys.exit()
print

# identify what to do with output of simulation
choices = ['Do not write to DB','Overwrite event streams',
           'Append events/new rev', 'Cancel']
result_dialog=''
result_dialog = dialog_choice.SelectChoice(choices).result
if result_dialog=='Cancel':
    print
    print 'Cancelling simulation'
    print
    sys.exit()
print

# add options to simulate just some of them
# read in the configuration for this run (example only - for now)
# simulate the IceCube, ANTARES, and HAWC event streams
streams=[0,1,7]
num_streams=len(streams)
print 'Number of streams: %s' % num_streams
revisions=[0,0,0]
conf = [simstream(streams[0]), simstream(streams[1]), simstream(streams[2])]
# hardcoded alert analysis stream for now
streams_alert=[1]

#################################
# EXECUTION OF MAIN SIM CODE
#results=basic_sim.basic_sim(conf)
#################################


if result_dialog==choices[0]:
    print 'Simulations will not be written to DB'
    if result_sim == choice_sim[0]:
        results=basic_sim.basic_sim(conf,revisions)
    elif result_sim==choice_sim[1]:
        results=basic_sim.signal_inject(conf,revisions)
    else:
        print
        print 'Unknown option. Canceling.'
        print
        sys.exit()
elif result_dialog==choices[1]:
    print 'Overwriting event streams in the DB'
    if result_sim == choice_sim[0]:
        results=basic_sim.basic_sim(conf,revisions)
    elif result_sim==choice_sim[1]:
        results=basic_sim.signal_inject(conf,revisions)
    else:
        print
        print 'Unknown option. Canceling.'
        print
        sys.exit()
    for i in xrange(len(streams)):
        print '...stream number %d' % streams[i]
        k=streams[i]
        db_delete.delete_alertline_stream_by_event(streams[i],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)
        #db_delete.delete_alert_stream(streams[i],HostFancyName,
         #                   UserFancyName,PasswordFancy,DBFancyName)
        db_delete.delete_event_stream(streams[i],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)

    for j in xrange(len(streams_alert)):
        print '...stream number %d' % streams_alert[j]
        db_delete.delete_alert_stream(streams_alert[j],HostFancyName,
                            UserFancyName,PasswordFancy,DBFancyName)

    db_write.write_event(1,HostFancyName,UserFancyName,
                            PasswordFancy,DBFancyName, results)
elif result_dialog==choices[2]:
    print 'Simulations will be appended to DB'
    print
    print 'Check if the database is for MC'
    if not (DBFancyName=='AMON_test2'):
        print 'This is not MC database. Terminating.'
        sys.exit(0)
    else:
        for ii in xrange(num_streams):
            revisions[ii]=db_read.rev_count(streams[ii],HostFancyName, UserFancyName,PasswordFancy,DBFancyName)
        #print rev_count(streams[0],HostFancyName, UserFancyName,
                                                  #PasswordFancy,DBFancyName)
            print "Max revision for stream %s is %s" % (streams[ii], revisions[ii])
            revisions[ii]+=1
            print "New revision for stream %s is %s" % (streams[ii], revisions[ii])
        if result_sim == choice_sim[0]:
            results=basic_sim.basic_sim(conf,revisions)
        elif result_sim==choice_sim[1]:
            results=basic_sim.signal_inject(conf,revisions)
        else:
            print
            print 'Unknown option. Canceling.'
            print
            sys.exit()
        db_write.write_event(1,HostFancyName,UserFancyName,
                            PasswordFancy,DBFancyName, results)
else:
    print 'Terminating'
    sys.exit(0)
