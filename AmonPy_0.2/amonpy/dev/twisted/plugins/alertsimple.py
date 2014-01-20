# Twisted simple server protocol and protocol factory

from twisted.internet.protocol import ServerFactory, Protocol
from twisted.application import internet, service
from twisted.python import usage, log

class AlertProtocol(Protocol):
    """
    Protocol for alert server.
    """
    def connectionMade(self):
        alert = self.factory.service.alert
        log.msg('Sending %d bytes of alert to %s'
                % (len(alert), self.transport.getPeer()))
        self.transport.write(alert)
        self.transport.loseConnection()


class AlertFactory(ServerFactory):
    """
    A factory making server protocols.
    """
    protocol = AlertProtocol

    def __init__(self, service):
        self.service = service

