"""@package basic_sim
    Generates a relatively simple simulation of sme high energy observatories
    The following crude assumptions are made:
    1. Circular FOV
    2. Constant event rate across FOV
    3. Fixed error for PSF
    4. Observatory is fixed to the Earth and cannot change its pointing 
    5. No skymap is used (i.e. PSF is analytic)
    6. Run simulation with injected signal if desired with function signal_inject 
    7. Calculates FOV overlap  
"""
from __future__ import print_function
from __future__ import absolute_import

from builtins import str
from builtins import range
from sys import path
from amonpy.dbase.db_classes import *
from time import time
import random
from datetime import datetime, timedelta
from numpy import math
from . import sidereal_m as sidereal
import ast
from operator import itemgetter, attrgetter




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
        ov_icecube = 0.
        ov_antares = 0.
        ov_auger =0. 
        ov_hawc = 0.
        ov_ic_ant_aug=0
        ov_ic_ant_hawc=0
        ov_ic_aug_hawc=0
        ov_ant_aug_hawc=0
        ov_allobs=0

        for jj in range(Nsim):
            sims+=[Event(0,0,revisions[kk])]
            ov_all = overlap(sims[jj].RA, sims[jj].dec, sims[jj].datetime)
            ov_icecube+=float(ov_all[0])/Nsim
            ov_antares+=float(ov_all[1])/Nsim
            ov_auger+=float(ov_all[2])/Nsim
            ov_hawc+=float(ov_all[3])/Nsim
            if (sims[jj].stream==0):
                ov_alltp=overlap_tp(0,sims[jj].RA, sims[jj].dec, sims[jj].datetime)
                ov_ic_ant_aug+=float(ov_alltp[0])/Nsim
                ov_ic_ant_hawc+=float(ov_alltp[1])/Nsim
                ov_ic_aug_hawc+=float(ov_alltp[2])/Nsim
                ov_obs=overlap_all(0,sims[jj].RA, sims[jj].dec, sims[jj].datetime)
                ov_allobs+=float(ov_obs[0])/Nsim
            elif (sims[jj].stream==1):
                ov_alltp=overlap_tp(1,sims[jj].RA, sims[jj].dec, sims[jj].datetime)    
                ov_ant_aug_hawc+=float(ov_alltp[0])/Nsim
            else:
                pass   
        """                 
        print 'Overlap with IceCube %s' % ov_icecube
        print 'Overlap with ANATARES %s' % ov_antares
        print 'Overlap with Auger %s' % ov_auger
        print 'Overlap with HAWC %s' % ov_hawc  
        """
        if (sims[0].stream==0):
            ov_icecube*=2.*math.pi
            ov_antares*=2.*math.pi
            ov_auger*=2.*math.pi
            ov_hawc*=2.*math.pi
            ov_ic_ant_aug*=2.*math.pi
            ov_ic_ant_hawc*=2.*math.pi
            ov_ic_aug_hawc*=2.*math.pi
            ov_allobs*=2.*math.pi
            print('Overlap with IceCube %s' % ov_icecube)
            print('Overlap with ANATARES %s' % ov_antares)
            print('Overlap with Auger %s' % ov_auger)
            print('Overlap with HAWC %s' % ov_hawc) 
            print('IceCube, ANTARES, Auger %s' % ov_ic_ant_aug)
            print('IceCube, ANATRES, HAWC %s' % ov_ic_ant_hawc)
            print('IceCube, Auger, HAWC %s' % ov_ic_aug_hawc)
            print('All 4 %s' % ov_allobs)
        elif (sims[0].stream==1): 
            ov_ant_aug_hawc*=2.*math.pi 
            print('ANTARES, Auger, HAWC %s' % ov_ant_aug_hawc)
        else:
            pass    
        """
        print 'Overlap with IceCube %s' % (ov_icecube)*2.*math.pi
        print 'Overlap with ANATARES %s' % ov_antares*2.*math.pi
        print 'Overlap with Auger %s' % ov_auger*2.*math.pi
        print 'Overlap with HAWC %s' % ov_hawc *2. 
        """
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
    for ev in results:
        if ev.stream==stream_injected:
            id_max=max(id_max,ev.id)
        elif ev.stream==stream_injected2:
            id_max2=max(id_max2,ev.id) 
        else:
            pass    
            
    triplets = [Event(stream_injected,id_max+1,0),Event(stream_injected,id_max+2,0)]
    triplets2 = [Event(stream_injected2,id_max2+1,0),Event(stream_injected2,id_max2+3,0)]
    
    atlist = [attr for attr in dir(results[event_number]) if not (attr.startswith('_'))]
    for attr in atlist:
        value = getattr(results[event_number],attr) 
        print("atribute %s" % value)            
        try:
            value = getattr(results[event_number],attr)
            if attr == 'datetime':
                setattr(triplets[0], attr, value+timedelta(seconds=0.3))
                setattr(triplets[1], attr, value+timedelta(seconds=0.5))
            elif attr == 'RA':    
                setattr(triplets[0], attr, value+0.1)
                setattr(triplets[1], attr, value+0.01)
            elif attr =='id':
                setattr(triplets[0], attr, id_max+1)
                setattr(triplets[1], attr, id_max+2)     
            else:
                setattr(triplets[0], attr, value)
                setattr(triplets[1], attr, value) 
        except:
            print("Empty slot") 
    atlist2 = [attr for attr in dir(results[event_number2]) if not (attr.startswith('_'))]
    for attr in atlist2:
        value = getattr(results[event_number2],attr) 
        print("atribute %s" % value)            
        try:
            value = getattr(results[event_number2],attr)
            if attr == 'datetime':
                setattr(triplets2[0], attr, value+timedelta(seconds=0.1))
                setattr(triplets2[1], attr, value+timedelta(seconds=0.4))
            elif attr == 'dec':    
                setattr(triplets2[0], attr, value+0.1)
                setattr(triplets2[1], attr, value+0.01)
            elif attr =='id':
                setattr(triplets2[0], attr, id_max2+1)
                setattr(triplets2[1], attr, id_max2+2)     
            else:
                setattr(triplets2[0], attr, value)
                setattr(triplets2[1], attr, value) 
        except:
            print("Empty slot")                  
    results.extend(triplets)
    results.extend(triplets2)
    results = sorted(results,key=attrgetter('datetime')) 
    return results 

# check the fov overlap, returns overlap with IceCube, ANTARES, Auger,HAWC as 1, or 0 
# otherwise
def overlap(era, edec,evtime): 
    conf = [simstream(0), simstream(1), simstream(3), simstream(7)]  
    #conf = [simstream(0)]    
    #Event1 = event_def(conf[1],True)
    fov=[]
    zen=[]
    lon=[]
    lat=[]
    h=[] # hour angle
    altaz=[]
    overlap=[]
    evtime_lst=[]
    rarec = sidereal.RADec(math.radians(era),math.radians(edec))
    evtime_gst = sidereal.SiderealTime.fromDatetime(evtime)
    for kk in range(len(conf)):
        fov+=[ast.literal_eval(conf[kk].fov)]
        zen+= [fov[kk]['zencut']]
        lon+=[fov[kk]['lon']]
        lat+=[fov[kk]['lat']]
        evtime_lst += [evtime_gst.lst(math.radians(lon[kk]))]
        h+=[rarec.hourAngle(evtime,math.radians(lon[kk]))] # hour angel in radians
    # overlap with icecube (result should be 2pi)
        altaz+=[rarec.altAz (h[kk], math.radians(lat[kk]))]
        if ((kk==0) or (kk==1)): #icecube and antares
            #if kk==0: 
                #print math.degrees(altaz[kk].alt)
            if (altaz[kk].alt <=math.radians(90.-zen[kk])):
                overlap+=[1]
            else:
                overlap+=[0]
        else:
            if (altaz[kk].alt >=math.radians(90.-zen[kk])):
                overlap+=[1]
            else:
                overlap+=[0]
    return overlap  
    
def overlap_tp(stream,era, edec,evtime): 
    conf = [simstream(0), simstream(1), simstream(3), simstream(7)]  
    #conf = [simstream(0)]    
    #Event1 = event_def(conf[1],True)
    fov=[]
    zen=[]
    lon=[]
    lat=[]
    h=[] # hour angle
    altaz=[]
    overlap=[]
    evtime_lst=[]
    rarec = sidereal.RADec(math.radians(era),math.radians(edec))
    evtime_gst = sidereal.SiderealTime.fromDatetime(evtime)
    for kk in range(len(conf)):
        fov+=[ast.literal_eval(conf[kk].fov)]
        zen+= [fov[kk]['zencut']]
        lon+=[fov[kk]['lon']]
        lat+=[fov[kk]['lat']]
        evtime_lst += [evtime_gst.lst(math.radians(lon[kk]))]
        h+=[rarec.hourAngle(evtime,math.radians(lon[kk]))] # hour angel in radians
    # overlap with icecube (result should be 2pi)
        altaz+=[rarec.altAz (h[kk], math.radians(lat[kk]))]
    if (stream==0):
        if ((altaz[1].alt <=math.radians(90.-zen[1])) and \
            (altaz[2].alt >=math.radians(90.-zen[2]))):
            overlap+=[1]
        else:
            overlap+=[0]
        if ((altaz[1].alt <=math.radians(90.-zen[1])) and \
            (altaz[3].alt >=math.radians(90.-zen[3]))):
            overlap+=[1]
        else:
            overlap+=[0] 
        if ((altaz[2].alt >=math.radians(90.-zen[2])) and \
           (altaz[3].alt >=math.radians(90.-zen[3]))):
            overlap+=[1]
        else:
            overlap+=[0]       
    elif (stream==1):
             
        if ((altaz[2].alt >=math.radians(90.-zen[2])) and \
            (altaz[3].alt >=math.radians(90.-zen[3]))):
            overlap+=[1]
        else:
            overlap+=[0]
    else:
        pass         
    return overlap  

def overlap_all(stream,era, edec,evtime): 
    conf = [simstream(0), simstream(1), simstream(3), simstream(7)]  
    #conf = [simstream(0)]    
    #Event1 = event_def(conf[1],True)
    fov=[]
    zen=[]
    lon=[]
    lat=[]
    h=[] # hour angle
    altaz=[]
    overlap=[]
    evtime_lst=[]
    rarec = sidereal.RADec(math.radians(era),math.radians(edec))
    evtime_gst = sidereal.SiderealTime.fromDatetime(evtime)
    for kk in range(len(conf)):
        fov+=[ast.literal_eval(conf[kk].fov)]
        zen+= [fov[kk]['zencut']]
        lon+=[fov[kk]['lon']]
        lat+=[fov[kk]['lat']]
        evtime_lst += [evtime_gst.lst(math.radians(lon[kk]))]
        h+=[rarec.hourAngle(evtime,math.radians(lon[kk]))] # hour angel in radians
    # overlap with icecube (result should be 2pi)
        altaz+=[rarec.altAz (h[kk], math.radians(lat[kk]))]
    if (stream==0):
        if ((altaz[1].alt <=math.radians(90.-zen[1])) and \
            (altaz[2].alt >=math.radians(90.-zen[2])) and \
            (altaz[3].alt >=math.radians(90.-zen[3]))):
            overlap+=[1]
        else:
            overlap+=[0]
    else:
        pass    
    return overlap                           
                 
if __name__ == "__main__":
    basic_sim()        
        
