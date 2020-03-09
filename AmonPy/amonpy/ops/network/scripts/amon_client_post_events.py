"""@package amon_client_post_events
client that sends events to the server using HTTP 
protocol with method=POST
"""
from __future__ import print_function
from builtins import str
from builtins import object
import sys, getopt, os, shutil, logging, datetime

from twisted.internet import reactor
from twisted.internet.task import LoopingCall
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.iweb import IBodyProducer
from twisted.web import http_headers

from zope.interface import implements

path=log=host=False

# usage of the program

def usage():
	"""Displays program usage menu"""
	print("""Usage:
	        -s --host        Host server
			-p --path        Path to check for new data files and archive e.g. /path/to/datafiles/
			-l --log         Name and path to create log file. e.g. path/to/logfile/clientlog.log
			-h --help        Show usage menu and quit.
		  """)
	exit()
	
try:
	opts, args = getopt.getopt(sys.argv[1:], "s:p:l:h", ["host=","path=", "log="])
except getopt.GetoptError as err:
	print(str(err))
	usage()
	
for o, a in opts:
	if o in ("-p", "--path"):
		path=a
		if path[-1] != '/':
			path = path+'/'
	elif o in ("-l", "--log"):
		log=a
	elif o in ("-s", "--host"):
		host=a
	elif o in ("-h", "--help"):
		usage()
	else:
		print("Option",o,"not recognized.")
		usage()

# set up archive directory where the events are moved after sending them to server

if not (path):
	path="./"
if not (log):
	log=path+"AmonClient.log"
if not (os.path.isdir(path+"archive/")):
	os.mkdir(path+"archive/")

# log file
try:
	logging.basicConfig(filename=log, level=logging.DEBUG)
except:
	print("Could not open or create log file:",log+". Please make sure the directory exists and has proper write permissions.")
	exit()

# options for logging 

logging.info("""*** Program Initiated at %s ***
Path to archives: %s
Log File: %s
""" % (datetime.datetime.now().isoformat(),path, log))	

# To post data with Agent, need to implement producer

class StringProducer(object):
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class ResourcePrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, data):
        print(data)

    def connectionLost(self, reason):
        self.finished.callback(None)

def printResource(response):
    finished = Deferred()
    response.deliverBody(ResourcePrinter(finished))
    return finished

def printError(failure):
    print(failure, file=sys.stderr)

def stop(result):
    reactor.stop()

def check_for_files(path):
    agent = Agent(reactor)
    
    files = sorted(os.listdir(path), key=lambda p: os.path.getctime(os.path.join(path, p)))
    files_xml=[]
    
    for filename in files:
        if (os.path.isdir(path+filename) or filename[0]=='.' or filename.find(".log") !=-1):
            pass
        elif (filename.find(".xml")!=-1):
            files_xml.append(filename)
        else:
            pass
            
    if len(files_xml)>0:
        oldest = files_xml[0] 
        try:
            datafile=open(path+oldest)
            data=datafile.read()
            lenght_data=str(len(data))
            #datafile.close()
            shutil.move(path+oldest, path+"archive/"+oldest)
            body = StringProducer(data)
            headers = http_headers.Headers({'User-Agent': ['Twisted HTTP Client'],
                                            'Content-Type':['text/xml'], 
                                            'Content-Lenght': [lenght_data],
                                            'Content-Name':[filename]})
            d = agent.request('POST', host, headers, bodyProducer=body)
            # on success it returns Deferred with a response object
            d.addCallbacks(printResource, printError)
            datafile.close()
            print("Event %s sent" % (oldest,))
        except:
            logging.error("Error parsing file "+filename+" at:"+datetime.datetime.now().isoformat())
    else:
       pass               
# user TimerService with twistd instead of LoopingCall            
lc=LoopingCall(check_for_files, path)
lc.start(0.1)
reactor.run()