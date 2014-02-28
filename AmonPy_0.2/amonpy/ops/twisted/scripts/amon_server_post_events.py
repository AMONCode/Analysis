"""@package amon_server_post_events
receives events from a client using HTTP protocols and writes them into database 
"""
import cgi, os, getopt, sys
from datetime import datetime, timedelta
from time import time
import tempfile

from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site

sys.path.append("../../../dbase")
sys.path.append("../../../sim")
sys.path.append("../../../tools")

from dbase.db_classes import Event
import dbase.db_write
import dbase.voevent_to_event

global path
path=False

# usage of the program 
def usage():
	"""Displays program usage menu"""
	print """Usage:
			-p --path        Path to install archive directories for received events
			-h --help        Show usage menu and quit.
		  """
	exit()

try:
	opts, args = getopt.getopt(sys.argv[1:], "p:hi", ["path=", "help"])
except getopt.GetoptError, err:
	print str(err)
	usage()
	
for o, a in opts:
	if o in ("-p", "--path"):
		path=a
		if path[-1] != '/':
			path = path+'/'
	elif o in ("-h", "--help"):
		usage()
	else:
		print "Option",o,"not recognized."
		usage()	
		
# set up archive directory

if not (path):
	path="./"
if not (os.path.isdir(path+"server_events/")):
	os.mkdir(path+"server_events/")		
	
class EventPage(Resource):
    isLeaf = True
    
    HostFancyName='localhost'
    UserFancyName='Goci'
    PasswordFancy='niki4laza6'
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
        
        fp = open(path+"server_events/"+fname, "w")
        fp.write(request.content.getvalue())
        fp.close()
        # convert it to Event object
        event=dbase.voevent_to_event.make_event(path+"server_events/"+fname) 
        event[0].forprint()
        os.remove(path+"server_events/"+fname)
        # write to DB
        t1 = time()                                                                
        dbase.db_write.write_event(0, self.HostFancyName, self.UserFancyName, 
                                   self.PasswordFancy, self.DBFancyName,event)   
        t2 = time() 
        print '   DB writing time: %.5f seconds' % float(t2-t1)                                                           

        return request.content.read() #[::-1]

resource = EventPage()
factory = Site(resource)

reactor.listenTCP(8000, factory, interface='127.0.0.1')
reactor.run()