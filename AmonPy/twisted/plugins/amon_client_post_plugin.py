from twisted.application.service import ServiceMaker

broker = ServiceMaker(
    "AMON Client VOEvent Broker", "amonpy.service.broker_client", "AMON Client http post events", "clientpost"
)
