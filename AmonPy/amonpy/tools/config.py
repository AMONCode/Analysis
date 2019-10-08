import pkg_resources
from configparser import ConfigParser as CP

AMON_CONFIG = CP(allow_no_value=True)

with open(pkg_resources.resource_filename("amonpy","amon.ini")) as f:
    AMON_CONFIG.readfp(f)
