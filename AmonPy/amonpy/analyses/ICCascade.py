from __future__ import print_function
from builtins import str
from builtins import range
from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase import ICcascade_to_voevent, post_on_websites
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams
from amonpy.tools.config import AMON_CONFIG
from amonpy.tools.postAlerts import postAlertGCN
from amonpy.monitoring.monitor_funcs import slack_message

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy.time import Time

from time import time

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc
import jsonpickle
import MySQLdb as mdb

import sys
import shutil
import os
import subprocess


# DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')  # Config.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs', 'alertdir')
AmonPyDir = AMON_CONFIG.get('dirs', 'amonpydir')
prodMachine = eval(AMON_CONFIG.get('machine', 'prod'))
#if prodMachine:
#    channel = 'alerts'
#else:
#    channel = 'test-alerts'


UserFancyName = AMON_CONFIG.get('database', 'username')  # nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database', 'password')  # nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')  # Config.get('database', 'realtime_dbname')
token = AMON_CONFIG.get('alerts', 'slack_token')  # Slack token


def ic_cascade_config():
    """ Returns an IC-Cascade AlertConfig object
    """
    stream = alert_streams['IC-Cascade']
    rev = 0
    config = AlertConfig2(stream, rev)
    config.participating  = alert_streams['IC-Cascade']  # 2**streams['IC-HESE'] + 2**streams['IC-EHE'] # index of event streams
    config.deltaT         = 100.00  # 80000.0 #100.0               # seconds
    config.bufferT        = 86400.00  # 1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 2.00  # 10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc = 'N/A'
    config.skymap_val2Desc = 'N/A'
    config.skymap_val3Desc = 'N/A'
    config.N_thresh       = '{10:1,11:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012, 1, 1, 0, 0, 0, 0)
    config.validStop      = datetime(2020, 1, 1, 0, 0, 0, 0)
    config.R_thresh       = 0.0
    return config


@app.task(ignore_result=True)
def ic_cascade(new_event=None):

    max_id = db_read.alert_max_id(alert_streams['IC-Cascade'], HostFancyName,
                                  UserFancyName,
                                  PasswordFancy,
                                  DBFancyName)
    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print("Max Id Alert in DB: %d" % (idnum))

    new_event = jsonpickle.decode(new_event, classes=Event)

    energy = 0.
    signalness = 0.
    # src_error_50 = 0.
    # src_error_90 = 0.
    far = 0.
    event_name = ""

    t1 = time()
    # new_event=db_read.read_event_single(new_event.stream,new_event.id,new_event.rev,HostFancyName,
    #                                 UserFancyName,PasswordFancy,DBFancyName)
    params = db_read.read_parameters(new_event.stream, new_event.id, new_event.rev, HostFancyName,
                                     UserFancyName, PasswordFancy, DBFancyName)

    skymaps = db_read.read_skyMapEvent(new_event.stream, new_event.id, new_event.rev, HostFancyName,
                                     UserFancyName, PasswordFancy, DBFancyName)

    t2 = time()
    print('   Read time: %.2f seconds' % float(t2 - t1))
    print(' Length of parameters %s' % len(params))

    # Add name IceCube-Cascade-YYMMDDa to parameters
    con = mdb.connect(HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
    cur = con.cursor()

    if new_event.rev == 0:
        subthreshold = False
        for i in range(len(params)):
            if params[i].name == "signalness" and params[i].value == -1:
                print('Signalness %.2f' % params[i].value)
                extension = "sub"
                subthreshold = True

        today = str(pd.to_datetime(new_event.datetime))
        if not subthreshold:
            #Get number of overthreshold cascade events in the same UTC day
            cur.execute("SELECT id FROM event WHERE eventStreamConfig_stream=26 AND type='observation' AND time>'%s' AND rev=0;"%(today))
            today_events = [item[0] for item in cur.fetchall()]
            N_events_today = 0
            if len(today_events)>0:
                today_ids = ""
                for id_ in today_events:
                    if len(today_ids) > 0:
                        today_ids += " OR "
                    today_ids += "event_id="+str(id_)
                
                cur.execute("""SELECT event_id FROM parameter WHERE event_eventStreamConfig_stream=26 AND name='signalness' AND (%s) AND value!=-1;"""%(today_ids))
                today_overThresh_events = [item[0] for item in transaction.fetchall()]
                today_overThresh_events = list(dict.fromkeys(today_overThresh_events)) # Remove duplicates (revisions)
                N_events_today = max(0, len(today_overThresh_events)-1)
            #Make name
            alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
            extension = alphabet[N_events_today]
        event_name = "IceCubeCascade-"+today[2:4]+today[5:7]+today[8:10]+extension
        print(event_name)
    else:
        cur.execute("""SELECT value FROM parameter WHERE event_eventStreamConfig_stream = 26 AND name='event_name' AND event_id=%s AND event_rev=0""",(new_event.id))
        event_name = cur.fetchone()[0]
    #Write it as parameter
    cur.execute("""INSERT INTO parameter VALUES(%s,%s,%s,%s,%s,%s)""",
        (event_name,
        0,
        'NA',
        new_event.stream,
        new_event.id,
        new_event.rev))             
    con.commit()

    # Read parameters again, now including the event_name
    params = db_read.read_parameters(new_event.stream, new_event.id, new_event.rev, HostFancyName,
                                     UserFancyName, PasswordFancy, DBFancyName)
    # Get some parameters of the event
    if (len(params) > 0):
        for i in range(len(params)):
            # if ((params[i].name=='varname') and (params[i].value=='heseEvent')):
            if (params[i].name == 'signalness'):
                signalness = params[i].value
                print('Signalness %.2f' % signalness)
            if (params[i].name == 'run_id'):
                run_id = params[i].value
            if (params[i].name == 'event_id'):
                event_id = params[i].value
            if (params[i].name == 'src_error'):
                src_error_50 = params[i].value
            if (params[i].name == 'src_error90'):
                src_error_90 = params[i].value
            if (params[i].name == 'energy'):
                energy = params[i].value
            if (params[i].name == 'far'):
                far = params[i].value
            if (params[i].name[0:14] == 'IceCubeCascade'):
                event_name = params[i].name
            # if (params[i].name == 'fits_url'):
            #     fits_url = params[i].value
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
    if prodMachine is True:
        title = 'IC Cascade Alert'
    else:
        title = 'Dev machine: IC Cascade'
    content = 'Event name = ' + str(event_name) + '\n'\
            + 'FAR = ' + str(far) + '\n'\
            + 'Energy = ' + str(energy/1000.) + ' TeV\n'\
            + 'Signalness = ' + str(signalness) + '\n'\
            + 'RA = ' + str(new_event.RA) + '\n'\
            + 'Dec = ' + str(new_event.dec) + '\n'\
            + 'Event_time = ' + str(pd.to_datetime(new_event.datetime)) + '\n'\
            + 'Run_id = ' + str(int(run_id)) + '\n'\
            + 'Event_id = ' + str(int(event_id)) + '\n'\
            + 'Skymap_fits = ' + skymaps['skymap_fits'] + '\n'\
            + 'Skymap_png = ' + skymaps['skymap_png'] + '\n'

    # Create Alert xml file
    xmlForm = ICcascade_to_voevent.ICcascade_to_voevent([new_event], params, skymaps)
    fname = os.path.join(AlertDir, 'amon_ic-cascade_%s_%s_%s.xml' % (new_event.stream, new_event.id, new_event.rev))
    f1 = open(fname, 'w+')
    f1.write(xmlForm)
    f1.close()

    if (new_event.type == "observation") and (prodMachine is True) and (signalness != -1):
        channel="alerts"
        try:
            postAlertGCN(fname)
            if new_event.rev == 0:
                post_on_websites.ICCascade_to_OpenAMON(new_event,params,skymaps)
        except subprocess.CalledProcessError as e:
            print("Send Cascade VOevent alert failed")
            slack_message(title+" FAILED TO SEND <!channel>\n"+"File: {}\n".format(fname)+content,channel,prodMachine,token=token)
            raise e
        else:
            shutil.move(fname, os.path.join(AlertDir, "archive/"))
            slack_message(title+" <!channel>\n"+content, channel, prodMachine, token=token)
    else:
        channel="test-alerts"
        shutil.move(fname, os.path.join(AlertDir, "archive/"))
        slack_message(title+"\n"+content, channel, prodMachine, token=token)

    #post_on_websites.ICCascade_to_OpenAMON(new_event,params,skymaps)
    email_alerts.alert_email_content([new_event], content, title)
    # email_alerts.alert_email([new_event],params)
