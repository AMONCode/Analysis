"""@package amon_server_post_events
receives events from a client using HTTP protocols and saves them in 
an archive directory called server_events
"""
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
import cgi, os, getopt, sys

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
        print "filename is %s" % (fname,)
        fp = open(path+"server_events/"+fname, "w")
        fp.write(request.content.getvalue())
        fp.close()
        return request.content.read() #[::-1]

resource = EventPage()
factory = Site(resource)
reactor.listenTCP(8000, factory)
reactor.run()