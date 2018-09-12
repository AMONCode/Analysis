from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase.alert_to_voevent import alert_to_voevent
from amonpy.dbase import hesealert_to_voevent, ehealert_to_voevent,ofualert_to_voevent
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

import sys, shutil, os, subprocess


# DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')#Config.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs','alertdir')
AmonPyDir = AMON_CONFIG.get('dirs','amonpydir')
prodMachine = eval(AMON_CONFIG.get('machine','prod'))

UserFancyName = AMON_CONFIG.get('database','username')#nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#Config.get('database', 'realtime_dbname')

def ic_hese_ehe_config():
    """ Returns an IC-HESE-EHE AlertConfig object
    """
    stream = alert_streams['IC-HESE-EHE']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['IC-HESE-EHE']#2**streams['IC-HESE'] + 2**streams['IC-EHE'] # index of event streams
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
def ic_hese_ehe(new_event=None):

    max_id = db_read.alert_max_id(alert_streams['IC-HESE-EHE'],HostFancyName,
                                       UserFancyName,
                                       PasswordFancy,
                                       DBFancyName)
    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print "Max Id Alert in DB: %d"%(idnum)

    new_event = jsonpickle.decode(new_event)

    eventHESE = False
    signal_t = 0.
    hese_charge=0.
    signalness=0.
    src_error_50=0.

    t1 = time()
    events=db_read.read_event_single(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
    params=db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)

    t2 = time()
    print '   Read time: %.2f seconds' % float(t2-t1)
    print ' lenght of parameters %s' % len(params)

    #Get some parameters of the event
    if (len(params)>0):
        for i in range(len(params)):
            # if ((params[i].name=='varname') and (params[i].value=='heseEvent')):
            if (params[i].name=='signal_trackness'):
                eventHESE=True
                signal_t = params[i].value
                print 'Signal trackenss %.2f' % signal_t
            if (params[i].name=='causalqtot'):
                hese_charge=params[i].value
            if (params[i].name=='run_id'):
                run_id=params[i].value
            if (params[i].name=='event_id'):
                event_id=params[i].value
            if (params[i].name== 'signalness'):
                signalness=params[i].value
            if (params[i].name== 'src_error'):
                src_error_50=params[i].value
    # note: change signal_t to 0.1 after unblinding

    # check if EHE and HESE are duplicates of each other
    if (events.stream==streams['IC-HESE']):
        events_duplicate=db_read.read_event_single(streams['IC-EHE'],new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
        if events_duplicate is None:
            alertDuplicate=False
        else:
            alertDuplicate=True
        print "alert duplicate"
        print alertDuplicate
    if (events.stream==streams['IC-EHE']):
        events_duplicate=db_read.read_event_single(streams['IC-HESE'],new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
        if events_duplicate is None:
            alertDuplicate=False
        else:
            alertDuplicate=True
        print "alert duplicate"
        print alertDuplicate

    ##########################################
    #if ((eventHESE==True) and (signal_t >= 0.)):
        # send HESE events directly to GCN first
    #    xmlForm=hesealert_to_voevent.hesealert_to_voevent([events],params,alertDuplicate)
    #    fname=os.path.join(AlertDir,'amon_hese_%s_%s_%s.xml'%(events.stream, events.id, events.rev))
    #    f1=open(fname, 'w+')
    #    f1.write(xmlForm)
    #    f1.close()


        #email_alerts.alert_email([events],params)
    #    content = 'HESE_charge = '+str(hese_charge)+'\n'+'HESE_signal_trackness = '+str(signal_t)+'\n'+'HESE_ra = '+str(events.RA)+'\n'+'HESE_dec = '+str(events.dec)+'\n'+'HESE_event_time = '+str(pd.to_datetime(events.datetime))+'\n'+'HESE_run_id = '+str(run_id)+'\n'+'HESE_event_id = '+str(event_id)+'\n'
    #    title = 'Test from Dev machine: HESE'
    #    email_alerts.alert_email_content([events],content,title)
    ##########################################
    """
                modified from
                https://github.com/timstaley/fourpiskytools/blob/master/fourpiskytools/comet.py
                Send a voevent to a broker using the comet-sendvo publishing tool.
                Args:
                host (string): IP address or hostname of VOEvent broker.
                port (int): Port, default 8098.
                code this up!
                comment out code bellow if you do not have comet installed!
    """
    if ((eventHESE==True) and (signal_t >= 0.1) and (hese_charge>=6000.)):
        # send HESE events directly to GCN first
        xmlForm=hesealert_to_voevent.hesealert_to_voevent([events],params,alertDuplicate)
        fname=os.path.join(AlertDir,'amon_hese_%s_%s_%s.xml'%(events.stream, events.id, events.rev))
        f1=open(fname, 'w+')
        f1.write(xmlForm)
        f1.close()
        content = 'HESE_charge = '+str(hese_charge)+'\n'+'HESE_signal_trackness = '+str(signal_t)+'\n'+'HESE_ra = '+str(events.RA)+'\n'+'HESE_dec = '+str(events.dec)+'\n'+'HESE_event_time = '+str(pd.to_datetime(events.datetime))+'\n'+'HESE_run_id = '+str(run_id)+'\n'+'HESE_event_id = '+str(event_id)+'\n'
        if prodMachine is True:
            title = 'HESE Alert'
        else:
            title = 'Test from Dev machine: HESE'
        email_alerts.alert_email_content([events],content,title)
        if (events.type=="observation") and (prodMachine is True):
            try:
                cmd = ['comet-sendvo']
                cmd.append('--file=' + fname)
                # just for dev to prevent sending hese both from dev and pro machine
                print "uncoment this if used on production"
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                print "Send HESE VOevent alert failed"
                logger.error("send_voevent failed")
                raise e
            else:
                shutil.move(fname, os.path.join(AlertDir,"archive/"))
        else:
            shutil.move(fname, os.path.join(AlertDir,"archive/"))
    if (eventHESE==True):
            email_alerts.alert_email([events],params)

    ############################################
    if (events.stream==streams["IC-EHE"]):
        xmlForm=ehealert_to_voevent.ehealert_to_voevent([events],params, alertDuplicate)
        fname=os.path.join(AlertDir,'amon_icecube_ehe_%s_%s_%s.xml'%(events.stream, events.id, events.rev))
        f1=open(fname, 'w+')
        f1.write(xmlForm)
        f1.close()

        if (events.type=="observation") and (prodMachine is True):
            try:
                print "EHE sent to GCN"
                cmd = ['comet-sendvo']
                cmd.append('--file=' + fname)
                subprocess.check_call(cmd)
            except subprocess.CalledProcessError as e:
                print "Send IceCube EHE VOevent alert failed"
                logger.error("send_voevent failed")
                raise e
            else:
                shutil.move(fname, os.path.join(AlertDir,"archive/"))
        else:
            shutil.move(fname, os.path.join(AlertDir,"archive/"))
        content = 'EHE_signalness = '+str(signalness)+'\n'+'EHE_ra = '+str(events.RA)+'\n'+'EHE_dec = '+str(events.dec)+'\n'+'EHE_event_time = '+str(pd.to_datetime(events.datetime))+'\n'+'EHE_run_id = '+str(run_id)+'\n'+'EHE_event_id = '+str(event_id)+'\n'
        if prodMachine is True:
            title = 'EHE Alert'
        else:
            title = 'Test from Dev machine: EHE'
        email_alerts.alert_email_content([events],content,title)
        email_alerts.alert_email([events],params)
