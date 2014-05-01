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
    new_alert.psi = fcluster.psi 
    new_alert.psi1 = fcluster.psi1
    new_alert.psi2 = fcluster.psi2
    #new_alert.psi3 = fcluster.psi2
    #new_alert.events = [ev1,ev2]
    new_alert.events = []
    for kk in xrange(evlenght):
        new_alert.events.append(evlist[kk])
    # to be loaded from config in the future                 
    new_alert.anastream=new_alert.stream
    new_alert.anarev=0
    return new_alert

def far_density(evlist, conf, fcluster):
    """
    False alarm density calculator (per sr per second)
    """ 
    far_den=0. 
    ev_len=len(evlist)
    if ev_len==2:
        far_den=evlist[0].false_pos*evlist[1].false_pos*conf.deltaT*fcluster.sigmaQ * \
                conf.cluster_thresh
    elif ev_len==3:
        far_den=0.5*evlist[0].false_pos*evlist[1].false_pos*evlist[2].false_pos * \
                (conf.deltaT*fcluster.sigmaQ*conf.cluster_thresh)**2
    else:
        # generalize for 3+ events
        pass 
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
        
    for kk in streams:
        kk=str(kk)
        rate+=rates[kk]
    # method bellow is not correct because all rates should be included in poisson process    
    #for ii in xrange(ev_len):
    #    rate+=evlist[kk].false_pos
    
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
    
    while True:
        
        # look for incoming packet in the pipe
        try:
            ev=server.recv()
        except EOFError:
            break

        # check to see if an AMON Event type was received 
        if isinstance(ev,Event):
            numreceived+=1
            # add the new event to the buffer (or start buffer)
            # buffer is in reverse temporal order
            try:
                events.appendleft(ev)
            except:
                events = deque([ev])
            
            # ensure that the new event didn't mess up the order of the buffer
            if (ev.datetime < latest):
                print '  reordering analysis buffer due to latent event'
                events = sorted(events,key=attrgetter('datetime'))
            else:
                # the new event is the latest event
                latest = ev.datetime

            #clean up the buffer (assumes temporal order)
            while bufdur(events) > config.bufferT:
                events.pop()

            # search the event buffer for *pairings* (v0.1)
            Nev = len(events)
            jj = 1

            while True:
                #print Nev, jj, ev.id
                if jj >= Nev:
                    break
                
                # assuming temporal order, continue loop until deltaT exceeded
                dt = timedelta.total_seconds(ev.datetime-events[jj].datetime)
                if dt > config.deltaT:
                    break

                # check if cluster distance is within threshold
                f = cluster.Fisher(events[jj],ev)
                if (f.Nsigma <= config.cluster_thresh):
                    # calculate false alarm rate
                    evlist=[events[jj],ev]
                    far = far_density(evlist,config,f)
                    pvalue = pvalue_calc(evlist,config,f)
                    # create alert, with id next in list
                    #id=Nalerts + Nalerts_tp
                    id+=1
                    rev = 0
                    evlist = [events[jj],ev]
                    new_alert = build_alert(config,id,rev,f,evlist,far, pvalue)
                    Nalerts +=1             
                    alerts +=[new_alert]
                if jj>1: # look for triplets
                    
                    f_tp = cluster.Fisher_tp(events[jj-1], events[jj], ev) 
                    if ((f_tp.Nsigma <= config.cluster_thresh) and \
                       (f_tp.Nsigma_2 <= config.cluster_thresh) and \
                       (f_tp.Nsigma_3 <= config.cluster_thresh)):
                        # create alert, with id next in list
                        evlist=[events[jj-1],events[jj],ev]
                        far = far_density(evlist,config,f)
                        pvalue = pvalue_calc(evlist,config,f)
                        #id=Nalerts + Nalerts_tp
                        id+=1
                        rev = 0
                        new_alert= build_alert(config,id,rev,f_tp, evlist, far, pvalue)
                        Nalerts_tp +=1             
                        alerts +=[new_alert]
                       
                jj+=1
            #print 'Found %s doublets' % Nalerts
            #print 'Found %s triplets' % Nalerts_tp
        # check to see if client has requested alerts        
        elif (ev=='get_alerts'):
            print 'Found %s doublets' % Nalerts
            print 'Found %s triplets' % Nalerts_tp
            if len(alerts)==0:
                server.send("Empty") 
            else: 
                try:    
                    server.send(alerts)
                except:
                    server.send("Problem")
                        
            alerts=[]
            Nalerts=0
            Nalerts_tp=0
            #print "lenghts of alerts %s" % (len(alerts),)

        # check to see if client has requested quit    
        elif (ev=='quit'):
            break

        # check for invalid request 
        else:
            print '   Event sent to analysis.anal() not recognized'
            print ev
        
    # shutdown

