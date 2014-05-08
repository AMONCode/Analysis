"""@package amon_server_post
- receives events from a client using HTTP protocols in
an xml form (VOEvents), 
- converts then into Event and Parameter objects
- writes them into DB using twisted adbapi connection pool that 
performs DB transactions in a separate threat, thus keeping the code asynchronous
- send a message to AMON analysis code about new event (event stream, id and rev)
"""
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
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

class EventPage(Resource):
    isLeaf = True
    #from amon_server_post4 import WriteEvent 
    #w = WriteEvent()
    
    # initiate celery task that will send message to analysis server 
    # about new incoming event
    #n=AnalRT()
    
    HostFancyName='localhost'
    UserFancyName='yourname'
    PasswordFancy='yourpass'
    DBFancyName='AMON_test2'
    eventlist = []
    paramlist = []
    microsec = 0.
    counter = 1
    
    print "Event page is %d" % counter
    dbpool = adbapi.ConnectionPool("MySQLdb", db = DBFancyName, 
                                            user = UserFancyName, 
                                            passwd = PasswordFancy, 
                                            host = HostFancyName,
                                            cp_min=1,
                                            cp_max=1)
        
        # initialize task for AMON analysis in analyser.runanal
    ana=AnalRT()

    def render_POST(self, request):
    
        def _writeEventParam(transaction, event, evparam):
            # this will run in a separate thread, allowing us to use series of queries 
            # without blocking the rest of the code
                
            # take microsecond part from datetime because of the older versions of mysql
        
            if '.' in str(event[0].datetime):
                microsec=int(float('.'+str(event[0].datetime).split('.')[1])*1000000)
                    #print 'microseconds %d' % microsec
            else:
                microsec=0.0
                      
            transaction.execute("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                            %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(event[0].stream,
                            event[0].id,
                            event[0].rev,
                            event[0].datetime, 
                            microsec, 
                            event[0].dec,
                            event[0].RA, 
                            event[0].sigmaR, 
                            event[0].nevents,
                            event[0].deltaT,
                            event[0].sigmaT,
                            event[0].false_pos,
                            event[0].pvalue,
                            event[0].type,
                            event[0].point_RA,
                            event[0].point_dec,
                            event[0].longitude, 
                            event[0].latitude,
                            event[0].elevation,
                            event[0].psf_type,
                            0)) 
                            
            transaction.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",
                           (evparam[0].name,
                            evparam[0].value,
                            evparam[0].units,
                            evparam[0].event_eventStreamConfig_stream, 
                            evparam[0].event_id,evparam[0].event_rev))
            return event                
                           
        def writeEventParam(event, evparam):
            return EventPage.dbpool.runInteraction(_writeEventParam, event, evparam) 
            #dd.addCallbacks(self.printResult, self.printError)
            #return dd 
        
        def printResult(result):
            print "This event is written"
            print result[0].stream, result[0].id, result[0].rev
            
            #after Event and Parameter are written in DB, it is safe to send 
            # a message to the analyser about new event to be read from DB and added to 
            # analyses 
            
            EventPage.ana.apply_async((result[0].stream, result[0].id, result[0].rev),
                                link_error=error_handler.s())      
            
        def printError(error):
            print "Got Error: %r" % error
            error.printTraceback()                              
    
        def Finish():
            # do not call this function in reaal-time settings 
            EventPage.dbpool.close()
        
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

        #t1 = time()                                                                
                  
        #write event to DB (does it in a separate thread)
        d = writeEventParam(event, evParam)
        
        # send a meesage to the analyser in case event and parameter
        # are written to DB, otherwise print error
        
        d.addCallbacks(printResult, printError)
        
        #t2 = time() 
        #print '   DB writing time: %.5f seconds' % float(t2-t1) 
        
        request.finish()
        return NOT_DONE_YET
        #return request.content.read()

                               
