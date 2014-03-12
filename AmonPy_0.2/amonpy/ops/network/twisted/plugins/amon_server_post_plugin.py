"""@package amon_server_post_plugin
receives events from a client using HTTP protocols and saves them in 
database (db writing is perform in a sperate thread, see amon_server_post2 modle 
Twisted plugin for a server receiving events. Only a testing version.
Run with twistd. Default is run as a daemon process.
 twistd -l server.log --pidfile server.pid serverpost --port 8000 --iface localhost
 Kill it with kill `cat server.pid`
 Make a subdirectory server_tmp_events/ in twisted parent directory before running  
"""
import sys
from zope.interface import implements
from twisted.application import internet, service

from twisted.python import usage, log
from twisted.plugin import IPlugin

sys.path.append("../../")

from amon_server_post import EventPage
from twisted.web.resource import Resource

from twisted.web.server import Site

# make a plugin service
class Options(usage.Options):

    optParameters = [
        ['port', 'p', 8000, 'The port number.'],
        ['iface', None, 'localhost', 'The interface.'],
        ]
		
class ServerPostServiceMaker(object):

    implements(service.IServiceMaker, IPlugin)

    tapname = "serverpost"
    description = "Server http post events."
    options = Options

    def makeService(self, options):
        
        resource = EventPage()
        factory = Site(resource)
        
        tcp_service = internet.TCPServer(int(options['port']), factory,
                                         interface=options['iface'])
        return tcp_service

service_maker = ServerPostServiceMaker()	
