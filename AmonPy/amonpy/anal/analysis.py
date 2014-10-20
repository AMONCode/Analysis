"""@package analysis
   Analysis modules that enable the buffering and analysis
   of incoming events. Realtime and archived events are treated
   identically, as the code is unaware of the state of the parent
   program.
"""
import sys
sys.path.append('../')
sys.path.append('../..')
sys.path.append('../dbase')
from datetime import datetime,timedelta
from collections import deque
import cluster
#from db_classes import Alert, event_def, Event
from amonpy.dbase.db_classes import Alert, event_def, Event
import math
import ast
from operator import itemgetter, attrgetter

# calculator for measuring the duration of the buffer
def bufdur(events):
    """
    Calculator for measuring the duration of the event buffer,
    being held by the analysis server
    """
    Nev = len(events)
    if Nev <= 1:
        dt = 0.
    else:
        dt = abs(timedelta.total_seconds(events[Nev-1].datetime \
                                         -events[0].datetime))
        ##Alternate method might be slower but is reobust to misordering:
        #datetimes = [ev.datetime for ev in events]
        #dt = timedelta.total_seconds(max(datetimes)-min(datetimes))
    return dt

# alert builder (build alerts from preliminary cluster)
def build_alert(config,id,rev,fcluster,evlist, far, pvalue):
    """
    Alert builder. Accepts the event list (ev1,ev2,...),
    as well as the results of the cluster analysis
    that tigered the alert building. 
    """
    new_alert = Alert(config.stream,id,rev)
       
    evlenght = len(evlist)                                
    # calculate trigger information
    triggers = 0
    trg=[]
    #trg = list(set([ev1.stream,ev2.stream]))
    for kk in xrange(evlenght):
        trg.append(evlist[kk].stream)
    for t in trg: triggers+= 2**t                 
    new_alert.trigger = triggers

    # populate non-spatial part of alert
    mindatetime=evlist[0].datetime
    #new_alert.datetime = min(ev1.datetime,ev2.datetime)
    for kk in xrange(evlenght-1):
        new_alert.datetime = min(mindatetime,min(evlist[kk].datetime,evlist[kk+1].datetime))
    maxtimedelta = abs(timedelta.total_seconds(evlist[0].datetime- \
                           evlist[1].datetime))
    for kk in xrange(evlenght-1):   
    #new_alert.deltaT = abs(timedelta.total_seconds(ev2.datetime-ev1.datetime))
        new_alert.deltaT = max(maxtimedelta,abs(timedelta.total_seconds(evlist[kk].datetime- \
                           evlist[kk+1].datetime)))
    new_alert.nevents = evlenght

    # populate spatial results from Fisher class
    new_alert.RA = fcluster.ra0
    new_alert.dec = fcluster.dec0
    new_alert.psf_part1 = fcluster.sigmaW
    new_alert.false_pos=far   
    new_alert.pvalue=pvalue         
    # information not currently in the Alert class, some of which we will
    # will need to add in a future version of db_classes.py
    new_alert.Nsigma = fcluster.Nsigma
    #new_alert.Nsigma_2 = fcluster.Nsigma_2
    #new_alert.Nsigma_3 = fcluster.Nsigma_3
    #new_alert.psi = fcluster.psi 
    # in case we decide to save angles between the events
    #new_alert.psi=[]
    #for kk in xrange(len(fcluster.psi)):
    #    new_alert.psi +=[fcluster.psi[kk]]
    #new_alert.psi1 = fcluster.psi1
    #new_alert.psi2 = fcluster.psi2
    #new_alert.psi3 = fcluster.psi2
    #new_alert.events = [ev1,ev2]
    new_alert.events = []
    for kk in xrange(evlenght):
        new_alert.events.append(evlist[kk])
    # to be loaded from config in the future                 
    new_alert.anastream=new_alert.stream
    new_alert.anarev=0
    return new_alert

def far_density_old(evlist, conf, fcluster):
    """
    Old false alarm density calculator (per sr per second), obsolete
    """ 
    far_den=0. 
    ev_len=len(evlist)
    if ev_len==2:
        far_den=evlist[0].false_pos*evlist[1].false_pos*conf.deltaT* 2.*math.pi*( 1. - \
                math.cos(math.radians(fcluster.sigmaQ * conf.cluster_thresh)))
    elif ev_len==3:
        far_den=0.5*evlist[0].false_pos*evlist[1].false_pos*evlist[2].false_pos * \
                (conf.deltaT*2.*math.pi*(1.-math.cos(math.radians(fcluster.sigmaQ*conf.cluster_thresh))))**2
    else:
        # generalize for 3+ events
        pass 
    return far_den 
     
def far_density(evlist, conf, fcluster):
    """
    False alarm density calculator (per sr per second)
    """ 
    far_den=0. 
    ev_len=len(evlist)
    
    #print "number of events in a multiplet %s" % (ev_len,)
    #print "space window in deg %s" %(fcluster.sigmaQ,)
    
    solid_angle = 2.*math.pi*(1. - math.cos(math.radians(fcluster.sigmaQ * conf.cluster_thresh)))
    #print "solid angle %s" % (solid_angle,)
    spaceTimeWind = conf.deltaT * solid_angle
    #print "serach window space-time %s" % (spaceTimeWind, )
    streamCurrent = evlist[0].stream 
    kkCurrent = 0
    kk=1
    event_dict={}
    event_dict[str(streamCurrent)]=[evlist[0]]
    # dictionary of lists of events in the multiplet coming from the same streams
    # e.g. :if a triplet has 2 event from stream 0 and one from stream 1
    #       the dictionary would be {'0': [ice_ev1, ice_ev2], '1': [antares_ev1]}
    #       prob. of this triplet is prob_doublet*prob_singlet
    #       compared to the triplet from 3 different streams
    #      where prob_triplet=prob_singlet1*prob_singlet2*prob_singlet3
    while (kk < ev_len):
        if (evlist[kk].stream ==streamCurrent):
            event_dict[str(streamCurrent)].append(evlist[kk])
             
        else:
            try:
                event_dict[str(evlist[kk].stream)].append(evlist[kk]) 
                streamCurrent = evlist[kk].stream
                
            except:
                event_dict[str(evlist[kk].stream)] = [evlist[kk]]          
                streamCurrent = evlist[kk].stream
        kk+=1       
    # calculate rates (probab. per unit spacetime) for various of stream combination and
    # multiplets
    poiss_prob = 1.
    for k in sorted(event_dict.keys()):
        num_ev = len(event_dict[k]) 
        rate = 0.
        for ll in xrange(num_ev):
            rate +=event_dict[k][ll].false_pos
        rate = rate/float(num_ev)    
        poiss_prob *=(prob_poisson(rate*spaceTimeWind,num_ev)) 
    far_den = poiss_prob/spaceTimeWind                   
      
    return far_den                                                
def pvalue_calc(evlist, conf, fcluster):
    """
    Combined p-value calculator (dummy for now). 
    Calculate p-value for time-clustering analysis only.
    """ 
    ev_len=len(evlist)
    # to this cluster
    # get the rate for an array of poisson processes
    # for all the streams used in the analyses
    # q: how to get bg rate at the best fit position for streams whose events are
    # not currently in the buffer?
    # for now 0=ic, 1 = antares,3=auger, 7=hawc
    rates={'0' : 0.0004438, '1' :0.0001463, '3': 0.0012104, '7':0.0004119}
    rate=0
    streams_dict = ast.literal_eval(conf.N_thresh)
    len_streams = len(streams_dict)
    streams=streams_dict.keys()
    
    # changed on 09/15/2014 in order to run Swift

    #for kk in streams:
        #kk=str(kk)
        #rate+=rates[kk]
    # method bellow is not correct because all rates should be included in poisson process    
    for ii in xrange(ev_len):
        rate+=evlist[ii].false_pos
    
    # time-space window used in analysis
    deltaT=conf.deltaT
    deltaOmega=fcluster.sigmaQ*conf.cluster_thresh
    
    expected = rate*deltaT*deltaOmega
    
    pvalue = 1. - sum_poisson(expected, ev_len)
    
    if pvalue > 0. and pvalue <=1.:
        return pvalue
    else:
        print "WARNING: pvalue is wrong, returning 1"  
        return 1  
        
def sum_poisson(expect,obs):
    """
    Poisson sum from 0 to obs-1
    """           
    sum=0.
    
    for ii in xrange(obs):
        sum+=(expect**ii)*math.exp(-1.*expect)/math.factorial(ii)
    return sum        
    #return 1.

def prob_poisson(expect,obs):
    """
    Poisson probability to observe obs number of events in a given stream
    """           
    sum=0.
    sum=(expect**obs)*math.exp(-1.*expect)/math.factorial(obs)
    return sum
# used for late arrival events in real-time code, i.e. for events that our out of time buffer

def check_nsigma(nsigma,cluster_th):
    """
    check if each pair of events within a cluster are separated by # of sigma < clusterThreshold
    return True if yes, False if not
    """
    checkSigma = True
    for kk_nsigma in nsigma:
        if kk_nsigma > cluster_th:
            checkSigma = False
    return checkSigma    
                
def alerts_late(events_rec, eve, config_rec, max_id):
    """
    analyser to be called in real-time analysis in case of very late
    arrival events (events out of time buffer)
    """
    Nalerts = 0
    Nalerts_tp = 0
    alerts = []
    alerts_tp = []
    # remove later
    numreceived=0
    id = max_id #max_id+1 is the first alert 
    #events=deque()
    events=events_rec
    ev = eve # the late arrival event
    #sort event
    events = sorted(events,key=attrgetter('datetime'), reverse=True)
    config=config_rec
    print "Late arival event analysis (archival) started"
    print
    print "Config dT %d" % config.deltaT
                        
    Nevents = len(events)
               #jj = 1
    #jj=0
    inBuffer = False
    alertCluster=False
    evIndex=0
        
    if isinstance(ev,Event):
        #for jj in xrange(Nevents):             
            # assuming temporal order, continue loop until deltaT exceeded
        for eve in events:
            if ((ev.stream == eve.stream) and (ev.id == eve.id)):
                if (ev.rev > eve.rev):
                    print "Old event revision in the archival time slice, remove it."
                    events.pop(events.index(eve)) 
                elif (ev.rev < eve.rev):
                    print "Old event revision arrived later than a newer one."
                    print "No analysis for this obsolete event"
                    inBuffer==True 
                else:
                    #ev = eve   # this is our real time event   
                    evIndex = events.index(eve)
           
        if (inBuffer==False):
                               
            Nev = len(events)
                
            jj=0
                
            while True:
                alertCluster = False
                    #print Nev, jj, ev.id
                if (jj >= Nev):
                    break
                if ((evIndex==jj) and (jj< Nev-1)):
                    jj+=1
                    # assuming temporal order, continue loop until deltaT exceeded
                dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))
                
                while dt > config.deltaT:
                    jj+=1
                    if (jj >= Nev):
                        break
                    elif (evIndex !=jj):   
                        dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))
                    else:
                        jj+=1
                        if (jj >= Nev):
                            break 
                        else:
                            dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))  
                        
                if (jj >= Nev):
                    break        
                    
                    #check for time clustering           
                if ((dt <= config.deltaT) and (evIndex !=jj)): 
                        # time clusters
                    list_time = [ev, events[jj]]
                        # check if there are more events within the (dt<t<deltaT-dt)
                        # to form time cluster
                    if (evIndex !=jj+1):
                        kk = jj+1
                    else:
                        kk = jj+2    
                        
                    if kk<Nev:
                        
                        dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                        if (kk < evIndex):
                            while (dt2 < dt):
                                if kk > Nev -1:
                                    break
                                if (evIndex!=kk):
                                    list_time.append(events[kk])
                                kk+=1
                                if kk >= Nev -1:
                                    break
                                dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                        elif (kk > evIndex and jj < evIndex):
                            while (dt2 < config.deltaT - dt):
                                if kk > Nev -1:
                                    break
                                if (evIndex!=kk):
                                    list_time.append(events[kk])
                                kk+=1
                                if kk >= Nev -1:
                                    break
                                dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                        elif (kk > evIndex and jj > evIndex):
                            while (dt2 < config.deltaT):
                                if kk > Nev -1:
                                    break
                                if (evIndex!=kk):
                                    list_time.append(events[kk])
                                kk+=1
                                if kk >= Nev -1:
                                    break
                                dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                        elif (kk == evIndex):
                            kk+=1 
                            dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            while (dt2 < config.deltaT):
                                if kk > Nev -1:
                                    break
                                if (evIndex!=kk):
                                    list_time.append(events[kk])
                                kk+=1
                                if kk >= Nev -1:
                                    break
                                dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                        else:
                            break         
                                           
                        #print "Lenght of time cluster is: %s" % (len(list_time),)
                        
                        # check space clustering for each multiplet from time cluster 
                        #containing new event (ev) in it
                    list_space=[ev]
                    for ll in xrange (len(list_time)-1):
                        list_space.append(list_time[ll+1])
                            # check fisher for list space      
                        # check if cluster distance is within threshold
                        # code FisherNew and new fNsigma check 
                        f = cluster.Fisher(list_space)
                        Nsigma_check = check_nsigma(f.Nsigma,config.cluster_thresh)
                        if Nsigma_check:
                                # calculate false alarm rate
                            evlist=list_space
                            far = far_density(evlist,config,f)
                            pvalue = pvalue_calc(evlist,config,f)
                            if (alertCluster==True):
                                    # higher multiplet found, remove lower multiplet
                                    # no need to increase id, since it will be 
                                    # taken from obsolete old multiplet 
                                print "higher multiplet found"
                                print "remove lower multiplet"
                                alerts.pop() 
                                Nalerts-=1
                            else:
                                    # this is the first multiplet, increase id    
                                id+=1
                                alertCluster = True
                            rev = 0
                                #evlist = [events[jj],ev]
                            new_alert = build_alert(config,id,rev,f,evlist,far, pvalue)
                            Nalerts +=1             
                            alerts +=[new_alert]
                            #if jj>1: # look for triplets
                            print "New alert"
                            print "With new event %s %s %s" % (ev.stream,ev.id,ev.rev )
                            print "With old event %s %s %s" % (events[jj].stream,events[jj].id,events[jj].rev )
                                                
                jj+=1       
                
        else:
            print "No analysis, event revision is older than previously arived event"        
                                
    else:
        print "Not event"  
    print 'Found %s doublets' % Nalerts
    #print 'Found %s triplets' % Nalerts_tp                                  
    return alerts        
        
    # shutdown    
# main analysis process


def anal(pipe,config):
    """
    Main analysis process, which is run as a server, accepting events
    from the parent code and returning alerts when requested. 
    """
    server,client = pipe
    client.close()   # close the client pipe on the server
    latest = datetime(1900,1,1,0,0,0,0)
    Nalerts = 0
    Nalerts_tp = 0
    alerts = []
    alerts_tp = []
    # remove later
    numreceived=0
    id = -1 # -1 no alerts, 0 first alert 
    #events=deque()
    events=[]
    inBuffer = False
    eventLate = False
    eventAnalysed = False
    alertCluster = False
    eveout = Event(-1,-1,-1)
    print "Config dT %d" % config.deltaT
    print "Buffer dT %d" % config.bufferT
    while True:
        
        # look for incoming packet in the pipe
        try:
            ev=server.recv()
        except EOFError:
            break

        # check to see if an AMON Event type was received 
        if isinstance(ev,Event):
            numreceived+=1
            inBuffer = False
            eventAnalysed = False
            eventIn=ev
            eventLate = False
            alertCluster = False
            
            #print "I received %d events" % numreceived
            #print "with this date %s" % ev.datetime
            # g.t. is not working in real-time setting; 
            # works only in archival setup 
            # add the new event to the buffer (or start buffer)
            # buffer is in reverse temporal order
            #try:
            #    events.appendleft(ev)
            #    print "appended"
            #except:
            #    events = deque([ev])
            #    print "dequed"
                       
            # do not search or add event if it is already in the buffer
            for eve in events:
                if ((ev.stream == eve.stream) and (ev.id == eve.id)):
                    if (ev.rev == eve.rev):
                        print "Event is already in the buffer. It will not be added to the buffer."
                        inBuffer = True
                    elif (ev.rev < eve.rev):
                        print "Old event revision arrived later than a newer one."
                        print "No analysis for this obsolete event"
                        
                        inBuffer = True
                    else:    
                        print "Old event revision in the buffer, remove it."
                        events.pop(events.index(eve))    
                        
             
            #
            # add the new event to the buffer (or start buffer)
            # buffer is in reverse temporal order, so sorted afterward 
            if (inBuffer==False):
                events+=[ev]        
                
                #print 'lenght of buffer is %d' % len(events)
                # ensure that the new event didn't mess up the order of the buffer
                if (ev.datetime < latest):
                    print '  reordering analysis buffer due to latent event'
                    events = sorted(events,key=attrgetter('datetime'),reverse=True)
                else:
                # the new event is the latest event
                    latest = ev.datetime
                    events = sorted(events,key=attrgetter('datetime'),reverse=True)
                    
                #clean up the buffer (assumes temporal order)
                while bufdur(events) > config.bufferT:
                    #cleaning buffer, but first check if the new event
                    # is one that is late arrival i.e.out of time buffer as well
                    eveout=events.pop()
                    if ((eveout.stream==ev.stream) and (eveout.id==ev.id) and (eveout.rev==ev.rev)):
                        #alerts = alerts_late(eveout,config.deltaT)
                        eventLate= True
                # if new events is in time buffer 
                # search the event buffer for *pairings* (v0.1)
                Nev = len(events)
                
                # do archival also if event is less or deltaT before end of the buffer
                # do it if buffer is long enough, otherwise every new event starting 
                # from the first will be analysed by archival instead RL
                 
                #if (bufdur(events) > (config.bufferT - config.deltaT)):
                #    if (abs(timedelta.total_seconds(events[Nev-1].datetime-ev.datetime))
                #        <=config.deltaT):
                #        eventLate= True     
                
               #jj = 1
                jj=0
                
                while True:
                    AlertCluster = False
                    #print Nev, jj, ev.id
                    if (jj >= Nev) or (eventLate==True):
                        break
                    if ((events.index(ev)==jj) and (jj< Nev-1)):
                        jj+=1
                    # assuming temporal order, continue loop until deltaT exceeded
                    dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))
                
                    # g.t. do not brake here since in case of late arrival our event will
                    # not be on the top of the buffer list
                    # add code for jj< ev index and jj> event index
                    while dt > config.deltaT:
                        jj+=1
                        if (jj >= Nev):
                            break
                        elif (events.index(ev) !=jj):   
                            dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))
                        else:
                            jj+=1
                            if (jj >= Nev):
                                break 
                            else:
                                dt = abs(timedelta.total_seconds(ev.datetime-events[jj].datetime))  
                        
                    if (jj >= Nev):
                        break        
                    
                    #check for time clustering           
                    if ((dt <= config.deltaT) and (events.index(ev) !=jj)): 
                        # time clusters
                        list_time = [ev, events[jj]]
                        # check if there are more events within the (dt<t<deltaT-dt)
                        # to form time cluster
                        if (events.index(ev) !=jj+1):
                            kk = jj+1
                        else:
                            kk = jj+2    
                        
                        if kk<Nev:
                        
                            dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            if (kk < events.index(ev)):
                                while (dt2 < dt):
                                    if kk > Nev -1:
                                        break
                                    if (events.index(ev)!=kk):
                                        list_time.append(events[kk])
                                    kk+=1
                                    if kk >= Nev -1:
                                        break
                                    dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            elif (kk > events.index(ev) and jj < events.index(ev)):
                                while (dt2 < config.deltaT - dt):
                                    if kk > Nev -1:
                                        break
                                    if (events.index(ev)!=kk):
                                        list_time.append(events[kk])
                                    kk+=1
                                    if kk >= Nev -1:
                                        break
                                    dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            elif (kk > events.index(ev) and jj > events.index(ev)):
                                while (dt2 < config.deltaT):
                                    if kk > Nev -1:
                                        break
                                    if (events.index(ev)!=kk):
                                        list_time.append(events[kk])
                                    kk+=1
                                    if kk >= Nev -1:
                                        break
                                    dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            elif (kk == events.index(ev)):
                                kk+=1 
                                dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                                while (dt2 < config.deltaT):
                                    if kk > Nev -1:
                                        break
                                    if (events.index(ev)!=kk):
                                        list_time.append(events[kk])
                                        
                                    kk+=1
                                    if kk >= Nev -1:
                                        break
                                    dt2 = abs(timedelta.total_seconds(ev.datetime-events[kk].datetime))
                            else:
                                break         
                                           
                        print "Lenght of time cluster is: %s" % (len(list_time),)
                        
                        # check space clustering for each multiplet from time cluster 
                        #containing new event (ev) in it
                        list_space=[ev]
                        for ll in xrange (len(list_time)-1):
                            list_space.append(list_time[ll+1])
                            # check fisher for list space      
                        # check if cluster distance is within threshold
                        # code FisherNew and new fNsigma check 
                            f = cluster.Fisher(list_space)
                            Nsigma_check = check_nsigma(f.Nsigma,config.cluster_thresh)
                            if Nsigma_check:
                                # calculate false alarm rate
                                evlist=list_space
                                far = far_density(evlist,config,f)
                                pvalue = pvalue_calc(evlist,config,f)
                                if alertCluster==True:
                                    # higher multiplet found, remove lower multiplet
                                    # no need to increase id, since it will be 
                                    # taken from obsolete old multiplet 
                                    print "higher multiplet found"
                                    print "remove lower multiplet"
                                    alerts.pop() 
                                    Nalerts-=1
                                else:
                                    # this is the first multiplet, increase id    
                                    id+=1
                                    AlertCluster = True
                                rev = 0
                                #evlist = [events[jj],ev]
                                new_alert = build_alert(config,id,rev,f,evlist,far, pvalue)
                                Nalerts +=1             
                                alerts +=[new_alert]
                            #if jj>1: # look for triplets
                                print "New alert"
                                print "With new event %s %s %s" % (ev.stream,ev.id,ev.rev )
                                print "With old event %s %s %s" % (events[jj].stream,events[jj].id,events[jj].rev )
                                                
                    jj+=1
                    #print 'Found %s doublets' % Nalerts
                    #print 'Found %s triplets' % Nalerts_tp
                    # check to see if client has requested alerts        
        elif (ev=='get_alerts'):
            print 'Found %s alerts' % Nalerts
            #print 'Found %s triplets' % Nalerts_tp
            if (len(alerts))==0:
                if (eventLate==False):
                    server.send("Empty") 
                else:
                    # send the event out of time buffer so that archival analysis can be started
                    server.send([eventLate,eventIn])    
                
            else: 
                try:    
                    server.send(alerts)
                except:
                    server.send("Problem")
                        
            alerts=[]
            Nalerts=0
            Nalerts_tp=0
            eventLate=False
            inBuffer=False
            alertCluster = False
            #print "lenghts of alerts %s" % (len(alerts),)

        # check to see if client has requested quit    
        elif (ev=='quit'):
            break

        # check for invalid request 
        else:
            print '   Event sent to analysis.anal() not recognized'
            print ev
        
    # shutdown
