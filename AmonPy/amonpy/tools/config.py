import pkg_resources
from configParser import ConfigParser as CP

AMON_CONFIG = CP()

with open(pkg_resources.resource_filename("amonpy","amon.ini")) as f:
    AMON_CONFIG.readfp(f)
    
