"""@package inject_coincident
    Makes two coincident events for fake signal injection.
    Also serves as a placeholder for adding various modele signal injections.
"""
from sys import path
path.append("../dbase/")
from db_classes import *
from time import time
import random
from datetime import datetime, timedelta
from numpy import math
import ast
from operator import itemgetter, attrgetter

def make_triplets(Event1, Event2, id_max, id_max2):
    """
    Make two pairs of events coincident with input events Event1 and Event2,
    this will make two fake triplets in simulation.
    """
    stream_injected=Event1.stream
    stream_injected2=Event2.stream
    
                         
    triplets = [Event(stream_injected,id_max+1,0),Event(stream_injected,id_max+2,0)]
    triplets2 = [Event(stream_injected2,id_max2+1,0),Event(stream_injected2,id_max2+2,0)]
    
    atlist = [attr for attr in dir(Event1) if not (attr.startswith('_'))]
    for attr in atlist:
        value = getattr(Event1,attr) 
        #print "atribute %s" % value            
        try:
            value = getattr(Event1,attr)
            if attr == 'datetime':
                setattr(triplets[0], attr, value+timedelta(seconds=0.3))
                setattr(triplets[1], attr, value+timedelta(seconds=0.5))
            elif attr == 'RA':    
                setattr(triplets[0], attr, value+0.1)
                setattr(triplets[1], attr, value+0.01)
            elif attr =='id':
                setattr(triplets[0], attr, id_max+1)
                setattr(triplets[1], attr, id_max+2)  
            elif attr =='pvalue':
                setattr(triplets[0], attr, 0.03)
                setattr(triplets[1], attr, 0.01)        
            else:
                setattr(triplets[0], attr, value)
                setattr(triplets[1], attr, value) 
        except:
            #print "Empty slot" 
            print 
    atlist2 = [attr for attr in dir(Event2) if not (attr.startswith('_'))]
    for attr in atlist2:
        value = getattr(Event2,attr) 
        #print "atribute %s" % value            
        try:
            value = getattr(Event2,attr)
            if attr == 'datetime':
                setattr(triplets2[0], attr, value+timedelta(seconds=1.0))
                setattr(triplets2[1], attr, value+timedelta(seconds=10.0))
            elif attr == 'dec':    
                setattr(triplets2[0], attr, value+0.1)
                setattr(triplets2[1], attr, value+0.05)
            elif attr =='id':
                setattr(triplets2[0], attr, id_max2+1)
                setattr(triplets2[1], attr, id_max2+2) 
            elif attr =='pvalue':
                setattr(triplets2[0], attr, 0.02)
                setattr(triplets2[1], attr, 0.01)        
            else:
                setattr(triplets2[0], attr, value)
                setattr(triplets2[1], attr, value) 
        except:
             print
                     
    return triplets, triplets2                     