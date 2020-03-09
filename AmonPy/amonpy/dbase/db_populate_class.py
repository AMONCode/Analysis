"""@package db_populate_class
Module to populate python classes that will be written into DB. 
"""
from builtins import range
import sys

# amonpy imports
from amonpy.dbase.db_classes import Alert, AlertLine

def populate_alertline(alerts):
    """
    Populates AlertLine class with the information from Alert class.
    """
    stream_num=0
#    alerts=[]
    alertlines=[]
    new_alertline=[]
    num_alerts=0
    num_events=0  # num
    i=0
    j=0
    id=0
    
    num_alerts=len(alerts)
    num_alertlines=0

    #print 'There is %d alerts to create alertlines' % num_alerts

    # populate alertline class
    k=0
    for i in range(num_alerts):
        #num_events=len(alerts[i].event_stream)
        num_events=len(alerts[i].events)
        for j in range(num_events):
            new_alertline+=[AlertLine(stream_num,id,0,-1,-1,-1)]
            new_alertline[j].stream_alert = alerts[i].stream
            new_alertline[j].id_alert = alerts[i].id
            new_alertline[j].rev_alert = alerts[i].rev
            #new_alertline[j].stream_event = alerts[i].event_stream[j]
            #new_alertline[j].id_event = alerts[i].event_id[j]
            #new_alertline[j].rev_event = alerts[i].event_rev[j]
            new_alertline[j].stream_event = alerts[i].events[j].stream
            new_alertline[j].id_event = alerts[i].events[j].id
            new_alertline[j].rev_event = alerts[i].events[j].rev
            #new_alertline[j].forprint()
            alertlines+=[new_alertline[j]]
            #print alertlines[k]
            k+=1 
        new_alertline=[] 
    num_alertlines=len(alertlines)
    #print  'There is %d alertlines created', num_alertlines  
         
    return alertlines    
        
        
