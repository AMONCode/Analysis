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
import resource
import fcntl

from zope.interface import implements
from twisted.application import internet, service
from twisted.application.internet import TimerService
from twisted.plugin import IPlugin
from twisted.python import usage, log

from amonpy.ops.network.amon_client_post import check_for_files
from twisted.python import usage, log
# Make a plugin using IServiceMaker

class Options(usage.Options):

    optParameters = [
        ['hostport', 'hp', "http://127.0.0.1:8000", 'The host and port http address.'],
        ['epath', None, "./", 'Path to the directory with VOEvents'],
        ['looptime', 'dt', 1.0, 'How often epath is checked for files in seconds']
        ]

#class ClientPostServiceMaker(object):

#implements(service.IServiceMaker, IPlugin)

options = Options

def makeService(options):
    #check directory with events for an oldest file
    # do it every 0.1 second using TimerService
    # set it to 10 sec to simulate real-time data arriving at AMON
    archive_path = os.path.join(options['epath'], "archive")
    if not os.path.isdir(archive_path):
        os.makedirs(archive_path)
    loop_service = TimerService(float(options['looptime']), check_for_files,\
                        options['hostport'], options['epath'])
    loop_service.startService()
    return loop_service

# finally, make a plugin
#service_maker = ClientPostServiceMaker()
