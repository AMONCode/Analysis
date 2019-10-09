from __future__ import print_function
# Twisted plugin for a client receiving alerts. Only a testing version.
# Run with twistd. Default is run as a daemon process.
# twistd -l client.log --pidfile client.pid alertreceive --port 10000 
# Kill it with kill `cat client.pid`

from builtins import object
from clientsimple import AlertClientProtocol, AlertClientFactory

from zope.interface import implements
from twisted.application import internet, service
from twisted.internet import defer

from twisted.python import usage, log
from twisted.plugin import IPlugin


class Options(usage.Options):

    optParameters = [
        ['port', 'p', 10000, 'The port number to connect to.'],
        ['host', 'h', 'localhost', 'The host machine to connect to.'],
        ]
        
class AlertClientServiceMaker(object):

    implements(service.IServiceMaker, IPlugin)

    tapname = "alertreceive"
    description = "Alert receiver service."
    options = Options
    
    def makeService(self, options):
       
        def got_alert(alert):
            print("alert received")
            print(alert) 
       
        d = defer.Deferred()
        d.addCallback(got_alert)
        factory = AlertClientFactory(d)
       
        tcp_service = internet.TCPClient(options['host'], int(options['port']), factory)
        
        return tcp_service

service_maker = AlertClientServiceMaker()

