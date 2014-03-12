"""@package amon_server_post
receives events from a client using HTTP protocols in
an xml form (VOEvents), converts then into Event objects
and writes them into DB using twisted adbapi connection pool that 
performs DB transactions in a separate threat, thus keeping the code asynchronous
"""
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.enterprise import adbapi

import cgi, os, getopt, sys
from datetime import datetime, timedelta
from time import time

path = "twisted/"	

sys.path.append("../../dbase")
sys.path.append("../../sim")
sys.path.append("../../tools")

from dbase.db_classes import Event
import dbase.db_write
import dbase.voevent_to_event

#global counter
#counter = 0
class WriteEvent(object):
    counter = 0
    def __init__(self):
        self.HostFancyName='yourhost'
        self.UserFancyName='yourname'
        self.PasswordFancy='yourpass'
        self.DBFancyName='AMON_test2'
        self.eventlist = []
        self.microsec = 0.
        self.dbpool = adbapi.ConnectionPool("MySQLdb", db = self.DBFancyName, 
                                            user = self.UserFancyName, 
                                            passwd = self.PasswordFancy, 
                                            host = self.HostFancyName)
        WriteEvent.counter +=1
        print "Counter %s" % (WriteEvent.counter,)                                    
    def doWriteEvent(self, event):
        #print "Counter %s" % (counter,)  
        self.eventlist.append(event[0])
        if '.' in str(self.eventlist[0].datetime):
            self.microsec=int(float('.'+str(self.eventlist[0].datetime).split('.')[1])*1000000)
                #print 'microseconds %d' % microsec
        else:
            self.microsec=0. 
    
        
        self.dbpool.runQuery("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
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
        self.eventlist.pop()                    
    def Finish(self):
        self.dbpool.close()                                                

class EventPage(Resource):
    isLeaf = True
        
    w = WriteEvent()
    
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
        event=dbase.voevent_to_event.make_event(path+"server_tmp_events/"+fname) 
        event[0].forprint()
        os.remove(path+"server_tmp_events/"+fname)
        # write to DB
        t1 = time()                                                                
        #w = WriteEvent(event)
        EventPage.w.doWriteEvent(event)
        #w.Finish()
        #print "Counter %s" % (counter,)
        t2 = time() 
        print '   DB writing time: %.5f seconds' % float(t2-t1)                                                           

        return request.content.read()

