"""@package amon_server_post
receives events from a client using HTTP protocols in
an xml form (VOEvents), converts then into Event objects
and writes them into DB
"""
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

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

class EventPage(Resource):
    isLeaf = True
    
    HostFancyName='localhost'
    UserFancyName='username'
    PasswordFancy='userpass'
    DBFancyName='AMON_test2'
    
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
        dbase.db_write.write_event(0, self.HostFancyName, self.UserFancyName, 
                                   self.PasswordFancy, self.DBFancyName,event)   
        t2 = time() 
        print '   DB writing time: %.5f seconds' % float(t2-t1)                                                           

        return request.content.read()

