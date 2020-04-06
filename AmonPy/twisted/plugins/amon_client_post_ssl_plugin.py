from twisted.application.service import ServiceMaker

broker = ServiceMaker(
    "AMON Client SSL VOEvent Broker", "amonpy.service.broker_client_ssl", "AMON Client http post events + ssl", "clientpostssl"
)
