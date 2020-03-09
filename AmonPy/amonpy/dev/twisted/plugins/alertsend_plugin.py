# Twisted plugin for a server sending alerts. Only a testing version.
# Run with twistd. Default is run as a daemon process.
# twistd alertsend --port 10000 --alert alerts/alername.xml
# Test it with "nc localhost 10000"
# Kill it with kill `cat twistd.pid`

from builtins import object
from zope.interface import implements
from twisted.application import internet, service

from alertsimple import AlertProtocol, AlertFactory

from twisted.python import usage, log
from twisted.plugin import IPlugin

class AlertService(service.Service):
    """
    A service delivering alerts to any protocol.
    Can be used by different types of protocols,
    not only by AlertProtocol. 
    """
    def __init__(self, alert_file):
        self.alert_file = alert_file

    def startService(self):
        service.Service.startService(self)
        self.alert = open(self.alert_file).read()
        log.msg('Got alert from: %s' % (self.alert_file,))

class Options(usage.Options):

    optParameters = [
        ['port', 'p', 10000, 'The port number.'],
        ['alert', None, None, 'The alert name'],
        ['iface', None, 'localhost', 'The interface.'],
        ]

# Service maker

class AlertServiceMaker(object):

    implements(service.IServiceMaker, IPlugin)

    tapname = "alertsend"
    description = "Alert sender service."
    options = Options

    def makeService(self, options):
        top_service = service.MultiService()

        alert_service = AlertService(options['alert'])
        alert_service.setServiceParent(top_service)

        factory = AlertFactory(alert_service)
        tcp_service = internet.TCPServer(int(options['port']), factory,
                                         interface=options['iface'])
        tcp_service.setServiceParent(top_service)

        return top_service

service_maker = AlertServiceMaker()