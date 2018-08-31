"""@package amon_client_post_events
client that sends events to the server using HTTP
protocol with method=POST
"""
import sys, os, shutil, logging
import resource
import fcntl

from twisted.internet import reactor
from twisted.python import log
from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol
from twisted.web.client import Agent, FileBodyProducer
from twisted.web import http_headers

path=host=False


class ResourcePrinter(Protocol):
    def __init__(self, finished):
        self.finished = finished

    def dataReceived(self, data):
        print data

    def connectionLost(self, reason):
        print 'Finished receiving body:', reason.getErrorMessage()
        self.finished.callback(None)

def printResource(response):
    finished = Deferred()
    response.deliverBody(ResourcePrinter(finished))
    return finished

def printError(failure):
    d=Deferred()
    d.addCallbacks(printNotSent)
    print >>sys.stderr, failure

def stop(result):
    reactor.stop()

def moveFile(path,fname):
    shutil.move(os.path.join(path,fname), os.path.join(path,"archive",fname))
    print "File %s sent" % (fname,)

def printSent(fname):
    print "File %s sent" % (fname,)

def printNotSent(filename):
    print "File %s not sent" % (fname,)

def check_open_fds():
    fds = []
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    for fd in range(0, soft):
        try:
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        except IOError:
            continue
        fds.append(fd)
    return soft, fds

def check_for_files(hostport, eventpath):
    # check a directory with events (eventpath) for an oldest xml file
    # if found post it to the server (hostport) using HTTP POST protocol

    # check for number of open file descriptors first, OS X is limited by default to 256
    # each OS has its own limitation, file descriptors are open not only when the file
    # is open, but for each new socket/connection opened as well

    fds = []
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    for fd in range(0, soft):
        try:
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
        except IOError:
            continue
        fds.append(fd)

    if (len(fds)<=soft):
        host=hostport
        path=eventpath

        agent = Agent(reactor)

        files = sorted(os.listdir(path), key=lambda p: os.path.getctime(os.path.join(path, p)))
        files_xml=[]

        for filename in files:
            if (os.path.isdir(os.path.join(path,filename)) or filename[0]=='.' or filename.find(".log") !=-1):
                pass
            elif (filename.find(".xml")!=-1):
                files_xml.append(filename)
            else:
                pass

        if len(files_xml)>0:
            oldest = files_xml[0]
            try:
                datafile=open(os.path.join(path,oldest))
                #data=datafile.read()
                #lenght_data=str(len(data))

                #body = StringProducer(data)
                body=FileBodyProducer(datafile)
                length_data=str(body.length)
                headers = http_headers.Headers({'User-Agent': ['Twisted HTTP Client'],
                                            'Content-Type':['text/xml'],
                                            'Content-Length': [length_data],
                                            'Content-Name':[oldest]})
                d = agent.request('POST', host, headers, bodyProducer=body)
                # on success it returns Deferred with a response object
                d.addCallbacks(printResource, printError)
                #shutil.move(path+oldest,path+"archive/"+oldest)
                #datafile.close()
                #print "Event %s sent" % (oldest,)
            except:
                log.msg("Error parsing file %s " % (path+oldest,))

            moveFile(path, oldest)

        else:
            pass
    else:
        pass
