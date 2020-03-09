from __future__ import print_function
from builtins import object
import sys
import math
import ast
import jsonpickle
from datetime import datetime,timedelta
import pandas as pd
#from amonpy.ops.server.util import DatetimeHandler
#jsonpickle.handlers.registry.register(datetime, DatetimeHandler)
# import logging
# logger = logging.getLogger('spam_application')
# logger.setLevel(logging.DEBUG)

from operator import itemgetter, attrgetter

from amonpy.dbase.db_classes import Event, event_def

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
        dt = abs(timedelta.total_seconds(pd.to_datetime(events[Nev-1].datetime) \
                                         -pd.to_datetime(events[0].datetime)))
        ##Alternate method might be slower but is reobust to misordering:
        #datetimes = [ev.datetime for ev in events]
        #dt = timedelta.total_seconds(max(datetimes)-min(datetimes))
    return dt

class EventBuffer(object):
    def __init__(self):
        self.events=[]
        self.event_streams=[]

    def toJSON(self):
        #return json.dumps(self,default=lambda o: o.__dict__, sort_keys=True,indent=4)
        jsonstr=jsonpickle.encode(self)
        return jsonstr

    def addStream(self,stream):
        self.event_streams.append(stream)

    #Probably put this function inside the server. For some reason it is not working
    def addEvent(self,event,config):
        #Check stream of the event and add it to the buffer
        f=open("/Users/hugo/AMON/HAWC_pipeline/test2.txt",'a')
        inBuffer = False
        latest = datetime(1900,1,1,0,0,0,0)
        eventout = Event(-1,-1,-1)
        f.write("Got event\n")
        #f.write(event)
        #logger.info(type(event))

        what=True
        #if isinstance(event,Event):
        if what is True:
            #Check if event is already in the buffer
            for e in self.events:
                f.write(e)
                if((event[0].stream == e[0].stream) and (event[0].id == e[0].id)):
                    if(event[0].rev == e[0].rev):
                        print("Event is already in the buffer. It will not be added to the buffer.")
                        inBuffer = True
                    elif (event[0].rev < e[0].rev):
                        print("Old event revision arrived later than a newer one.")
                        print("No analysis for this obsolete event")
                        inBuffer = True
                    else:
                        print("Old event revision in the buffer, remove it.")
                        self.events.pop(self.events.index(e))
            #Add the event to the buffer
            if inBuffer is False:
                f.write('Save event in buffer\n')
                #f.write(jsonpickle.encode(event))
                #print event[0].datetime
                f.close()
                #f.write(event)
                self.events.append(event)
                #self.evParams.append(evParams)

                #check the temporal order of the new event. Buffer is in reverse temporal order.
                '''if event[0].datetime < latest:
                    print '  reordering analysis buffer due to latent event'
                    self.events = sorted(self.events,key=attrgetter('datetime'),reverse=True)
                else:
                    latest = event.datetime
                    self.events = sorted(self.events,key=attrgetter('datetime'),reverse=True)

                # Clean the buffer according to the configuration buffer time
                while bufdur(self.events) > config.bufferT:
                    eventout = self.events.pop()
                    if ((eventout.stream==event.stream) and (eventout.id==event.id) and (eventout.rev==event.rev)):
                        print 'The new event came late into the buffer. Not using it'
                '''
            else:
                f.write('Event not added\n')
                f.close()
        else:
            f.write('event is not AMON Event')
            f.write("WHAT")
            f.close()
