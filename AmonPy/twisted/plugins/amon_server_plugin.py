from twisted.application.service import ServiceMaker

broker = ServiceMaker(
    "AMON VOEvent Broker", "amonpy.service.broker_server", "AMON VOEvent broker.", "amonserverpost"
)
