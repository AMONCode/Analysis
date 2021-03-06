"""@package amon_client_post_events_ssl
client that sends events to the server using HTTP
protocol with method=POST
Run with twistd. Default is run as a daemon process.
 twistd -l client.log --pidfile client.pid clientpostssl --hostport "https://isis.rcc.psu.edu/amon"
 --epath /path_to_client_ents --cfile client.crt --kfile client.key
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

from amonpy.ops.network.amon_client_post_ssl import check_for_files
from twisted.python import usage, log
# Make a plugin using IServiceMaker

class Options(usage.Options):

    optParameters = [
        ['hostport', 'hp', None, 'The host for https address.'],
        ['epath', None, None, 'Path to the directory with VOEvents'],
        ['looptime', 'dt', 5.0, 'How often epath is checked for files in seconds'],
        ['kfile', None, None,'Key file name'],
        ['cfile', None,None, 'Certificate name'],
        ]

#class ClientPostServiceMaker(object):

#implements(service.IServiceMaker, IPlugin)

options = Options

def makeService(options):
    #check directory with events for an oldest file
    # do it every N second using TimerService
    loop_service = TimerService(float(options['looptime']), check_for_files, options['hostport'], options['epath'],
                    options['kfile'], options['cfile'])
    loop_service.startService()
    return loop_service

# finally, make a plugin
#service_maker = ClientPostServiceMaker()
