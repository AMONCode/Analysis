import sys
from zope.interface import implements
from twisted.application import internet, service

from twisted.python import usage, log
from twisted.plugin import IPlugin
from twisted.web.server import Site

from amonpy.ops.server.amon_server import EventManager

# make a plugin service
class Options(usage.Options):

    optParameters = [
        ['port', 'p', 8000, 'The port number.'],
        ['iface', None, 'localhost', 'The interface.'],
        ]

#class AmonServerServiceMaker(object):

#implements(service.IServiceMaker, IPlugin)
options = Options

def makeService(self, options):

    resource = EventManager()
    factory = Site(resource)
    tcp_service = internet.TCPServer(int(options['port']), factory,
                                     interface=options['iface'])
    return tcp_service

#service_maker = AmonServerServiceMaker()
