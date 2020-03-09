"""@package basic_sim
    Generates a relatively simple simulation of sme high energy observatories
    The following crude assumptions are made:
    1. Circular FOV
    2. Constant event rate across FOV
    3. Fixed error for PSF
    4. Observatory is fixed to the Earth and cannot change its pointing
    5. No skymap is used (i.e. PSF is analytic)
    6. Run simulation with injected coincidence signal, if desired, with function signal_inject
"""
from __future__ import print_function

from builtins import str
from builtins import range
from sys import path
from time import time
import random
import ast
from datetime import datetime, timedelta
from numpy import math
from operator import itemgetter, attrgetter

from amonpy.dbase.db_classes import *
from amonpy.sim import sidereal_m as sidereal
from amonpy.sim import inject_coincident

def basic_sim(conf,revisions):
    results = []
    for config in conf:
        kk=0  # index in revision array
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

        Event = event_def(config,True)
        sims = [Event(0,0,revisions[kk]) for jj in range(Nsim)]
        kk+=1
        #sims = [SimEvent(config) for jj in xrange(Nsim)]
        t2 = time()
        print('....simulation took %.2f seconds' % float(t2-t1))
        print()

        # put events in temporal order
        sims = sorted(sims,key=attrgetter('datetime'))


        print('Here is some information on the first 5 events:')
        Nshow = min(Nsim, 5)
        for jj in range(Nshow):
            print('stream: ', sims[jj].stream,'id: ',sims[jj].id,\
                  '  RA: ', sims[jj].RA,'  dec: ', sims[jj].dec,\
                  '  datetime: ', sims[jj].datetime)
        print('')

        # combine the results together
        results.extend(sims)

    # sort results and transmit back
    results = sorted(results,key=attrgetter('datetime'))
    return results

def signal_inject(conf,revisions):
    results = []
    for config in conf:
        kk=0  # index in revision array
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

        Event = event_def(config,True)
        #
        #sims = [Event(0,0,revisions[kk]) for jj in xrange(Nsim)]
        # test filed of view overlap
        sims=[]
        ov_antares = 0
        ov_hawc = 0
        for jj in range(Nsim):
            sims+=[Event(0,0,revisions[kk])]

        kk+=1
        #sims = [SimEvent(config) for jj in xrange(Nsim)]
        t2 = time()
        print('....simulation took %.2f seconds' % float(t2-t1))
        print()

        # put events in temporal order
        sims = sorted(sims,key=attrgetter('datetime'))


        print('Here is some information on the first 5 events:')
        Nshow = min(Nsim, 5)
        for jj in range(Nshow):
            print('stream: ', sims[jj].stream,'id: ',sims[jj].id,\
                  '  RA: ', sims[jj].RA,'  dec: ', sims[jj].dec,\
                  '  datetime: ', sims[jj].datetime)
        print('')

        # combine the results together
        results.extend(sims)

    # sort results and transmit back
    results = sorted(results,key=attrgetter('datetime'))

    # pick up a random event from simulation and inject two event
    # coincident in time (0.5 sec time window) and space 0.1 deg from the random event
    # so that there is a triplet

    result_len = len(results)
    print("result lenght %s" % result_len)
    #num_of_triplets=2
    #event_number=[]
    triplets = []
    triplets2 = []

    event_number = int(random.uniform(0,result_len-1))
    event_number2 = int(random.uniform(0,result_len-1))

    stream_injected=results[event_number].stream
    stream_injected2=results[event_number2].stream
    id_max=0
    id_max2=0
    if not stream_injected==stream_injected2:
        for ev in results:
            if ev.stream==stream_injected:
                id_max=max(id_max,ev.id)
            elif ev.stream==stream_injected2:
                id_max2=max(id_max2,ev.id)
            else:
                pass
    else:
        for ev in results:
            if ev.stream==stream_injected:
                id_max=max(id_max,ev.id)
            else:
                pass
        id_max2=id_max+2

    triplets, triplets2 = inject_coincident.make_triplets(results[event_number],
                                                results[event_number2], id_max, id_max2)

    results.extend(triplets)
    results.extend(triplets2)
    results = sorted(results,key=attrgetter('datetime'))
    result_len2=len(results)
    print()
    print("result lenght with the fake signal %s" % result_len2)
    return results

if __name__ == "__main__":
    basic_sim()
