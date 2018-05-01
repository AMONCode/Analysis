from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
#from amonpy.dbase.alert_to_voevent import alert_to_voevent
from amonpy.dbase import gfualert_to_voevent
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams


from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy.time import Time

from time import time

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc, jsonpickle
from amonpy.tools.config import AMON_CONFIG

import sys, shutil, os

# DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')#Config.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs','alertdir')

UserFancyName = AMON_CONFIG.get('database','username')#nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#Config.get('database', 'realtime_dbname')

def ic_gfu_config():
    """ Returns an IC GFU AlertConfig object
    """
    stream = alert_streams['GFU-Alerts']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['GFU-Alerts']#2**streams['IC-HESE'] + 2**streams['IC-EHE'] # index of event streams
    config.deltaT         = 100.00 #80000.0 #100.0               # seconds
    config.bufferT        = 86400.00 #1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 2.00 #10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc= 'N/A'
    config.skymap_val2Desc= 'N/A'
    config.skymap_val3Desc= 'N/A'
    config.N_thresh       = '{10:1,11:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2020,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

@app.task(ignore_result=True)
def ic_gfu(new_event=None):

    max_id = db_read.alert_max_id(alert_streams['GFU-Alerts'],HostFancyName,
                                       UserFancyName,
                                       PasswordFancy,
                                       DBFancyName)
    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print "Max Id Alert in DB: %d"%(idnum)

    new_event = jsonpickle.decode(new_event)

    t1 = time()
    events=db_read.read_event_single(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
    params=db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)

    t2 = time()
    print '   Read time: %.2f seconds' % float(t2-t1)
    print ' lenght of parameters %s' % len(params)
    if (events.type == "observation"):
        xmlForm=gfualert_to_voevent.gfualert_to_voevent([events],params)
        fname=self.alertDir + 'amon_icecube_sf_%s_%s_%s.xml' \
            % (events.stream, events.id, events.rev)
        f1=open(fname, 'w+')
        f1.write(xmlForm)
        f1.close()
        if (self.prodMachine == True):
            try:
                print "GFU created"
                cmd = ['comet-sendvo']
                cmd.append('--file=' + fname)
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                print "Send IceCube GFU VOevent alert failed"
                #logger.error("send_voevent failed")
                raise e
            else:
                shutil.move(fname, os.path.join(AlertDir,"archive/"))
        else:
            shutil.move(fname, os.path.join(AlertDir,"archive/"))
