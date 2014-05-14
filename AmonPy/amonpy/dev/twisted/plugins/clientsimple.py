# simple client protocola and factory that receive alerts from a server 


from twisted.internet import defer
from twisted.internet.protocol import Protocol, ClientFactory
from sys import stdout

class AlertClientProtocol(Protocol):

    alert = ''

    def dataReceived(self, data):
        self.alert += data
        #stdout.write(data)

    def connectionLost(self, reason):
        self.alertReceived(self.alert)

    def alertReceived(self, alert):
        self.factory.alert_finished(alert)


class AlertClientFactory(ClientFactory):

    protocol = AlertClientProtocol

    def __init__(self, deferred):
        self.deferred = deferred

    def alert_finished(self, alert):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(alert)
            
    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)