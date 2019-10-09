"""@package amon_client_post_events
client that sends events to the server using HTTP 
protocol with method=POST
"""
from __future__ import print_function
from builtins import str
from builtins import object
import sys, getopt, os, shutil, logging, datetime

from twisted.internet import reactor
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

    
# Agent handles connection setup
agent = Agent(reactor)

# check the path for data files  
for filename in os.listdir(path):
    if (os.path.isdir(path+filename) or filename[0]=='.' or filename.find(".log") !=-1):
        pass
    else:	
        print("There is a file: %s"	% (path+filename))
        filelist=os.listdir(path)
        filelist_xml=[]
        for fl in filelist:
            if fl.find(".xml")!=-1:
                filelist_xml.append(fl)
        print("filelist")
        print(filelist)
        print("xml list")
        print(filelist_xml)        
        len1=len(filelist_xml)
        try:				
            datafile=open(path+filename)
            data=datafile.read()
            lenght_data=str(len(data))
            print("file %s read" % (path+filename))
            datafile.close()
            shutil.move(path+filename, path+"archive/"+filename)
            body = StringProducer(data)
            headers = http_headers.Headers({'User-Agent': ['Twisted HTTP Client'],
                                            'Content-Type':['text/xml'], 
                                            'Content-Lenght': [lenght_data],
                                            'Content-Name':[filename]})
            d = agent.request('POST', host, headers, bodyProducer=body)
            print(headers)
            # on success it returns Deferred with a response object
            d.addCallbacks(printResource, printError)
            len1=len1-1
            print("more files to go %s" % (len1,))
            if len1==0: # exclude log and . files
                d.addBoth(stop)
        except:
            logging.error("Error parsing file "+filename+" at:"+datetime.datetime.now().isoformat())				
            
#body = StringProducer(open(sys.argv[2]).read())
#d = agent.request('POST', sys.argv[1], bodyProducer=body)
#d.addCallbacks(printResource, printError)
#d.addBoth(stop)

reactor.run()