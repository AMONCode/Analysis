"""@package amon_server_post
- receives events from a client using HTTP protocols in
an xml form (VOEvents), 
- converts then into Event objects
- writes them into DB using twisted adbapi connection pool that 
performs DB transactions in a separate threat, thus keeping the code asynchronous
- send a message to AMON analysis code about new event (event stream, id and rev)
"""
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.enterprise import adbapi

import cgi, os, getopt, sys
from datetime import datetime, timedelta
from time import time

path = "twisted/"	
sys.path.append('../')
sys.path.append('../../')
sys.path.append('../../../')
sys.path.append("../../../tools")
sys.path.append("../../dbase")
sys.path.append("../../sim")
sys.path.append("../../tools")
sys.path.append("../../ops")

from dbase.db_classes import Event
import dbase.db_write
import dbase.voevent_to_event

from analyser.runanal import *

#global counter
#counter = 0
class WriteEvent(object):
    counter = 0
    def __init__(self):
        self.HostFancyName='localhost'
        self.UserFancyName='yourname'
        self.PasswordFancy='yourpass'
        self.DBFancyName='AMON_test2'
        self.eventlist = []
        self.paramlist = []
        self.microsec = 0.
        self.dbpool = adbapi.ConnectionPool("MySQLdb", db = self.DBFancyName, 
                                            user = self.UserFancyName, 
                                            passwd = self.PasswordFancy, 
                                            host = self.HostFancyName)
        WriteEvent.counter +=1
        print "Counter %s" % (WriteEvent.counter,) 
        # initialize task for AMON analysis in analyser.runanal
        #self.ana=AnalRT() 
        
    # run dbpool interaction instead of run query, which allows for a series of queries 
    # to be run one after anther  
    
    def _writeEventParam(self,transaction, event, evparam):
        # this will run in a separate thread, allowing us to use series of queries 
        # without blocking the rest of the code
        
        # need to add event to self.eventlist because of a later callback 
        #( e.g. printResult bellow) 
        
        if (len(self.eventlist)) > 0:
            self.eventlist.pop()  
        self.eventlist.append(event[0])
        
        # take microsecond part from datetime because of the older versions of mysql
        
        if '.' in str(self.eventlist[0].datetime):
            self.microsec=int(float('.'+str(self.eventlist[0].datetime).split('.')[1])*1000000)
                #print 'microseconds %d' % microsec
        else:
            self.microsec=0.
          
        # add parameter to self.parameterlist because of later callbacks
            
        if (len(self.paramlist)) > 0:
            self.paramlist.pop()  
        self.paramlist.append(evparam[0])    
        
        transaction.execute("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(self.eventlist[0].stream,
                            self.eventlist[0].id,
                            self.eventlist[0].rev,
                            self.eventlist[0].datetime, 
                            self.microsec, 
                            self.eventlist[0].dec,
                            self.eventlist[0].RA, 
                            self.eventlist[0].sigmaR, 
                            self.eventlist[0].nevents,
                            self.eventlist[0].deltaT,
                            self.eventlist[0].sigmaT,
                            self.eventlist[0].false_pos,
                            self.eventlist[0].pvalue,
                            self.eventlist[0].type,
                            self.eventlist[0].point_RA,
                            self.eventlist[0].point_dec,
                            self.eventlist[0].longitude, 
                            self.eventlist[0].latitude,
                            self.eventlist[0].elevation,
                            self.eventlist[0].psf_type,
                            0)) 
        transaction.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",
                           (self.paramlist[0].name,
                            self.paramlist[0].value,
                            self.paramlist[0].units,
                            self.paramlist[0].event_eventStreamConfig_stream, 
                            self.paramlist[0].event_id,self.paramlist[0].event_rev))
    
    def writeEventParam(self, event, evparam):
        return self.dbpool.runInteraction(self._writeEventParam, event, evparam)                                             
    
    def printResult(self,result):
        print "This event is written"
        print self.eventlist[0].stream, self.eventlist[0].id, self.eventlist[0].rev
        print "This parameter is written"
        print self.paramlist[0].event_eventStreamConfig_stream, self.paramlist[0].event_id, \
            self.paramlist[0].event_rev
        
        #after Event and Parameter are written in DB, it is safe to send 
        # a message to the analyser about new event to be read from DB and added to 
        # analyses 
            
        AnalRT().apply_async((self.eventlist[0].stream, self.eventlist[0].id, self.eventlist[0].rev),
                                link_error=error_handler.s())      
         
    def printError(self,error):
        print "Got Error: %r" % error
        error.printTraceback()                              
    
    def Finish(self):
        # do not call this function in reaal-time settings 
        self.dbpool.close()  
                                                      

class EventPage(Resource):
    isLeaf = True
        
    w = WriteEvent()
    
    # initiate celery task that will send message to analysis server 
    # about new incoming event
    #n=AnalRT()

    def render_POST(self, request):
        self.headers = request.getAllHeaders()
        print self.headers
        try:
            postfile = cgi.FieldStorage(
                fp = request.content,
                headers = self.headers,
                
                environ = {'REQUEST_METHOD':'POST',
                        'CONTENT_TYPE': self.headers['content-type'],
                        }
                )
        except Exception as e:
            print 'something went wrong: ' + str(e)
       
        print  request.content.getvalue()
        fname=self.headers['content-name']
        
        fp = open(path+"server_tmp_events/"+fname, "w")
        fp.write(request.content.getvalue())
        fp.close()
        # convert it to Event object
        event, evParam=dbase.voevent_to_event.make_event(path+"server_tmp_events/"+fname) 
        event[0].forprint()
        evParam[0].forprint()
        
        os.remove(path+"server_tmp_events/"+fname)
        # write to DB
        t1 = time()                                                                
        #w = WriteEvent(event)
                  
        #write event to DB (does it in a separate thread)
        d = EventPage.w.writeEventParam(event, evParam)
        # send a meesage to the analyser in case event and parameter
        # are written to DB, otherwise print error
        d.addCallbacks(EventPage.w.printResult, EventPage.w.printError)
        t2 = time() 
        print '   DB writing time: %.5f seconds' % float(t2-t1) 
        
        return request.content.read()

