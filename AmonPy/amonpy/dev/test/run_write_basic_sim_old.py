#run_basic_sim.py
"""@package run_write_basic_sim
Old module for running basic simulation and writing it into database.
"""
from __future__ import print_function
from builtins import str
from builtins import range
import sys
sys.path.append("../../sim")
sys.path.append("../../tools")
sys.path.append("../")

from basic_sim import * 
from time import time

#from sys import path
#path.append("../dbase/")
from db_classes import *
import random
import db_write

# simulate the IceCube, Auger, and HAWC event streams
conf = [simstream(0), simstream(1), simstream(7)]

results = []
for config in conf:

    # estimate the expected number of events in the simulated data set
    fov = ast.literal_eval(config.fov)           
    bckgr = ast.literal_eval(config.bckgr)
    false_pos = bckgr['false_pos']
    zencut = fov['zencut']
    Omega = 2*pi*(1 - math.cos(math.radians(zencut)))
    Rtot = false_pos*Omega
    Nex = Rtot*config.duration
    # Add some gaussian randomness to the number of simulated events    
    Nsim = int(round(random.gauss(Nex,math.sqrt(Nex))))
    
    # simulate the events
    print()
    print('Simulating '+ str(Nsim) + ' events for ' + config.observ_name +'...')
    t1 = time()
    sims = [SimEvent(config) for jj in range(Nsim)]
    t2 = time()
    print('....run time (sec): ', t2 - t1)
    print() 

    # put events in temporal order
    sims = sorted(sims,key=attrgetter('datetime'))

    real_archive=1 
    stream_name=0  # IceCube=0, obsolete, should be removed

# real_archive= 0  archive, 1 MC/real-time, stream_name stream name from the configuration
#  table in DB. For now only 'IceCube'. This is a foreign key and must be specified 
# in order for event to be written 
# insert your hostname, user name and password bellow
 
#    db_write.write_event(1,stream_name,'db.hpc.rcc.psu.edu', '', '', 'AMON_test2', sims)
    
        
    print('Here is some information on the first 5 events:')
    Nshow = min(Nsim, 5)
    for jj in range(Nshow):
        print('stream: ', sims[jj].stream, 'id: ', sims[jj].id, '  RA: ', sims[jj].RA, '  dec: ', sims[jj].dec, '  datetime: ', sims[jj].datetime) 
    print('')
    
    # combine the results together and sort
    results.extend(sims)
    results = sorted(results,key=attrgetter('datetime'))
    db_write.write_event(1,stream_name,'db.hpc.rcc.psu.edu', 'yourname', 'yourpass', 'AMON_test2', results)