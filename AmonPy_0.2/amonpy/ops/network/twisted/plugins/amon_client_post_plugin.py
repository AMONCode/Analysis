"""@package amon_client_post_events
client that sends events to the server using HTTP 
protocol with method=POST
Run with twistd. Default is run as a daemon process.
 twistd -l client.log --pidfile client.pid clientpost --hostport "http://127.0.0.1:8000" 
 --epath /path_to_client_ents 
 Kill it with kill `cat client.pid`
 Before running make directory archive within directory where your client events live.
 Each sent event will be moved from client directory to archive directory.
 Modify if you do not want to save sent events.
"""
import sys, getopt, os, shutil, datetime

sys.path.append("../../")

from twisted.internet import reactor
#from twisted.internet.task import LoopingCall
from twisted.internet.defer import Deferred, succeed
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent
from twisted.web.iweb import IBodyProducer
from twisted.web import http_headers

from amon_client_post import StringProducer, printResource, printError

from zope.interface import implements
from twisted.application import internet, service
from twisted.application.internet import TimerService

from twisted.python import usage, log
from twisted.plugin import IPlugin

def check_for_files(hostport, eventpath):
    # check a directory with events (eventpath) for an oldest xml file
    # if found post it to the server (hostport) using HTTP POST protocol
    
    host=hostport
    path=eventpath
    
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
            print "Event %s sent" % (oldest,)
        except:
            log.msg("Error parsing file %s " % (filename,))
            
    else:
        pass

# Make a plugin using IServiceMaker                
 
class Options(usage.Options):

    optParameters = [
        ['hostport', 'hp', None, 'The host and port http address.'],
        ['epath', None, None, 'Path to the directory with VOEvents'],
        ]
		
class ClientPostServiceMaker(object):
    
    implements(service.IServiceMaker, IPlugin)

    tapname = "clientpost"
    description = "Client http post events."
    options = Options
    
    def makeService(self, options):
        #check directory with events for an oldest file
        # do it every 0.1 second using TimerService     
        loop_service = TimerService(0.1, check_for_files, options['hostport'], options['epath'])
        loop_service.startService()
        return loop_service
        
# finally, make a plugin 
service_maker = ClientPostServiceMaker() 
