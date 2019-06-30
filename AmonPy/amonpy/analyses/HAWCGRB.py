from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase.alert_to_voevent import *
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams, gcn_streams

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer
from amonpy.monitoring.monitor_funcs import slack_message

from astropy.coordinates import SkyCoord
from astropy.time import Time

from time import time

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc, jsonpickle
from amonpy.tools.config import AMON_CONFIG

import sys, shutil, os, subprocess

# Get the DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')#Config.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs','alertdir')

UserFancyName = AMON_CONFIG.get('database','username')#nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#Config.get('database', 'realtime_dbname')
token = AMON_CONFIG.get('alerts','slack_token')#Slack token

# Variable to check in which server/machine we are
prodMachine = eval(AMON_CONFIG.get('machine','prod'))


def hawc_burst_config():
    """
        Returns a HAWC Burst AlertConfig object.
    """
    stream = alert_streams['HWC-GRBlike-Alerts']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['HWC-GRBlike-Alerts'] # index of event streams
    config.deltaT         = 10.00 #80000.0 #100.0               # seconds
    config.bufferT        = 86400.00 #1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 1.00 #10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc= 'N/A'
    config.skymap_val2Desc= 'N/A'
    config.skymap_val3Desc= 'N/A'
    config.N_thresh       = '{8:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2020,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

@app.task(ignore_result=True)
def hawc_burst(new_event=None):

    # max_id = db_read.alert_max_id(alert_streams['HWC-GRBlike-Alerts'],HostFancyName,
    #                                    UserFancyName,
    #                                    PasswordFancy,
    #                                    DBFancyName)

    config = hawc_burst_config()

    # if max_id is None:
    #     idnum = 0
    # else:
    #     idnum = max_id

    # print "Max Id Alert in DB: %d"%(idnum)

    new_event = jsonpickle.decode(new_event)

    t1 = time()
    # events=db_read.read_event_single(new_event.stream,new_event.id,new_event.rev,HostFancyName,
    #                                 UserFancyName,PasswordFancy,DBFancyName)
    params=db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)

    t2 = time()
    print '   Read time: %.2f seconds' % float(t2-t1)
    print ' lenght of parameters %s' % len(params)

    #Event description
    ra = new_event.RA
    dec = new_event.dec
    poserr = new_event.sigmaR
    false_pos = new_event.false_pos
    tevent = new_event.datetime
    content = 'Position RA: %0.2f Dec: %0.2f Ang.Err.: %0.3f, FAR: %0.3e yr^-1, Time: %s'%(ra,dec,poserr,false_pos,str(tevent))
    print content
    if prodMachine is True:
        title='AMON HAWC-GRBlike alert'
    else:
        title='Dev Machine: AMON HAWC-GRBlike alert'

    if (new_event.type == "observation") and (false_pos<=12.0):

        new_alert = Alert(config.stream,new_event.id,config.rev)
        new_alert.dec = dec
        new_alert.RA = ra
        new_alert.sigmaR = poserr
        new_alert.pvalue = new_event.pvalue
        new_alert.deltaT = new_event.deltaT
        new_alert.false_pos = false_pos
        new_alert.observing = config.stream
        new_alert.datetime = tevent
        if (prodMachine == True):
            new_alert.type = 'observation'
        else:
            new_alert.type = 'test'

        fname= 'amon_hawc_burst_%s_%s_%s.xml'%(config.stream, new_event.id, new_event.rev)
        #run_id and event_id come from the alert id, which in HAWC burst is a combination of the search time,
        #run number and event id
        run_id = str(new_event.id)[:-8] # Contains run id an search time if >1sec.
        event_id = str(new_event.id)[-4:]
        VOAlert = Alert2VOEvent([new_alert],'hawc_burst','Alert from HAWC Burst Monitoring',run_id,event_id)

        alertparams = []
        apar = VOAlert.MakeParam(name="stream",ucd="meta.number",unit="",datatype="int",value=gcn_streams["HWC-GRBlike-Alerts"],description="Alert stream identification")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="amon_id",ucd="meta.number",unit="",datatype="string",value=new_event.id,description='AMON id number')
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="rev",ucd="meta.number",unit="",datatype="int",value=new_event.rev,description="Revision of the alert")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="event_id",ucd="meta.number",unit="",datatype="int",value=event_id,description="Event id within a given run")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="run_id",ucd="meta.number",unit="",datatype="int",value=run_id,description="Run id")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="deltaT",ucd="time.timeduration",unit="s",datatype="float",value=new_alert.deltaT,description="Time window of the search")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="far", ucd="stat.probability",unit="yr^-1", datatype="float", value=false_pos, description="False Alarm Rate")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="pvalue", ucd="stat.probability",unit="", datatype="float", value=new_alert.pvalue, description="P-value of the alert")
        alertparams.append(apar)
        apar = VOAlert.MakeParam(name="skymap",ucd="meta.code.multip",unit="", datatype="string", value="",description="Skymap of alert (not available yet)")
        alertparams.append(apar)
        VOAlert.WhatVOEvent(alertparams)
        VOAlert.MakeWhereWhen([new_alert])
        xmlForm = VOAlert.writeXML()
        f1=open(os.path.join(AlertDir,fname), 'w+')
        f1.write(xmlForm)
        f1.close()

        if (prodMachine == True) and (false_pos<=1.0):
            title='AMON HAWC-GRBlike alert: URGENT!'
            try:
                print "HAWC Burst created, sending to GCN"
                cmd = ['comet-sendvo']
                cmd.append('--file=' + os.path.join(AlertDir,fname))
                subprocess.check_call(cmd)
                slack_message(title+"\n"+content,"alerts",token=token)
            except subprocess.CalledProcessError as e:
                print "Send HAWC Burst VOevent alert failed"
                #logger.error("send_voevent failed")
                raise e
            else:
                shutil.move(os.path.join(AlertDir,fname), os.path.join(AlertDir,"archive/"))
        else:
            shutil.move(os.path.join(AlertDir,fname), os.path.join(AlertDir,"archive/"))

    #Send email after everything has been accomplished, all the events
    email_alerts.alert_email_content([new_event],content,title)
