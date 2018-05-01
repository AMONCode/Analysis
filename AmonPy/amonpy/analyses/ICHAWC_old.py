from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase.alert_to_voevent import alert_to_voevent
from amonpy.analyses.amon_streams import streams, alert_streams

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy.time import Time

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc, jsonpickle
from amonpy.tools.config import AMON_CONFIG

#RAD2DEG = 180./np.pi
#DEG2RAD = np.pi/180

#from amonpy.ops.server.util import DatetimeHandler
#jsonpickle.handlers.registry.register(datetime, DatetimeHandler)

# DB configuration
#config_fname = '/Users/hugo/Software/Analysis/AmonPy/amonpy/amon.ini'
#Config = ConfigParser.ConfigParser()
#Config.read(config_fname)
HostFancyName = AMON_CONFIG.get('database', 'host_name')#Config.get('database', 'host_name')
#nrc_path = AMON_CONFIG.get('dirs', 'amonpydir') + '.netrc'#Config.get('dirs', 'amonpydir') + '.netrc'
#nrc = netrc.netrc(nrc_path)

UserFancyName = AMON_CONFIG.get('database','username')#nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#Config.get('database', 'realtime_dbname')

def ic_hawc_config():
    """ Returns an ICHAWC AlertConfig object
    """
    stream = alert_streams['IC-HAWC']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['IC-HAWC']#2**streams['IC-Singlet'] + 2**streams['HAWC-DM'] # index of event streams
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
    config.N_thresh       = '{0:1,7:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2020,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

def spcang(ra1,ra2,dec1,dec2):
    dec1 = np.deg2rad(dec1)
    dec2 = np.deg2rad(dec2)
    DeltaRA = np.deg2rad(ra1-ra2)
    sep = np.arccos(np.cos(dec1)*np.cos(dec2)*np.cos(DeltaRA) + np.sin(dec1)*np.sin(dec2))
    return np.rad2deg(sep)

def LLH(dec1,ra1,dec2,ra2,poserr1,poserr2,hwcsign):#,icsign):
    """
    Likelihood function for the IC-HAWC analysis.
    Positions should be in degrees.
    """
    #th1 = SkyCoord(ra1,dec1,unit='deg')
    #th2 = SkyCoord(ra2,dec2,unit='deg')
    #dth = th1.separation(th2).value
    dth = spcang(ra1,ra2,dec1,dec2)
    if dth>3.5:
        return -1
    dth = np.deg2rad(dth)
    dec1 = np.deg2rad(dec1)
    ra1 = np.deg2rad(ra1)
    dec2 = np.deg2rad(dec2)
    ra2 = np.deg2rad(ra2)
    sig0 = 1/(1/poserr1**2 + 1/poserr2**2) #Best position error
    f = sig0/poserr2**2 #pre-weight for "linear" interpolation
    a = np.sin((1-f)*dth)/np.sin(dth) #weight 1
    b = np.sin(f*dth)/np.sin(dth) #weight 2

    #vectors
    x = a*np.cos(dec1)*np.cos(ra1)+b*np.cos(dec2)*np.cos(ra2)
    y = a*np.cos(dec1)*np.sin(ra1)+b*np.cos(dec2)*np.sin(ra2)
    z = a*np.sin(dec1)+b*np.sin(dec2)
    #best positions
    ra0 = np.arctan2(y,x)
    ra0 %= 2*np.pi #making sure RA falls between 0 and 2pi
    dec0 = np.arctan2(z,np.sqrt(x**2 + y**2))
    ra0 = np.rad2deg(ra0)
    dec0 = np.rad2deg(dec0)
    if ra0 < 0 : ra0 = ra0 + 360

    #Likelihood calc.
    sigq2 = poserr1**2 + poserr2**2

    pdth = special.erf(dth/(np.sqrt(2)*sigq)) #Probability of distance being less than ∆theta
    pndth = 1 - pdth #probability distance begin more than ∆theta
    if pdth!=1:
        term1 = np.log(pdth) - np.log(pndth)#-np.log(2*np.pi*sigc)/2
    else:
        term1 = -20

    term2 = hwcsign**2

    result = term1 + term2#-np.log(2*np.pi*sigq2)/2 - dth**2/(2*sigmap2) + hwcsign**2# + icsign**2
    return [dec0, ra0, np.sqrt(sig0), result]


def coincAnalysis(new_event,eventList):
    coincs = []
    new_param = db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)
    for e in eventList:
        param = db_read.read_parameters(e.stream,e.id,e.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)
        #Check the time of the IC event is between the HAWC period.
        if new_event.stream == streams['HAWC-DM']:
            hwcRT = float(new_param[0].value) #HAWC Rise Time
            hwcST = float(new_param[1].value) #HAWC Set Time
            hrt = Time(hwcRT,format='mjd')
            hrt.format = 'isot'
            hst = Time(hwcST,format='mjd')
            hst.format = 'isot'
            if (pd.to_datetime(hrt.value) <= pd.to_datetime(e.datetime) and pd.to_datetime(hst.value) >= pd.to_datetime(e.datetime)):
                #Do the LLH calculation.
                dec1 = new_event.dec
                ra1 = new_event.RA
                poserr1 = new_event.sigmaR
                hwcsig = new_param[2].value
                dec2 = e.dec
                ra2 = e.RA
                poserr2 = e.sigmaR
                #icsign = ice[0].sigmaT
                #print 'Doing Likelihood calculation'
                llh = LLH(dec1,ra1,dec2,ra2,poserr1,poserr2,hwcsig)#,icsign)
                if llh != -1:
                    coincs.append(llh)

        elif new_event.stream == streams['IC-Singlet']:
            hwcRT = float(param[0].value) #HAWC Rise Time
            hwcST = float(param[1].value)
            hrt = Time(hwcRT,format='mjd')
            hrt.format = 'isot'
            hst = Time(hwcST,format='mjd')
            hst.format = 'isot'
            if (pd.to_datetime(hrt.value) <= pd.to_datetime(new_event.datetime) and pd.to_datetime(hst.value) >= pd.to_datetime(new_event.datetime)):
                #Do the LLH calculation.
                dec1 = e.dec
                ra1 = e.RA
                poserr1 = e.sigmaR
                hwcsig = param[2].value
                dec2 =new_event.dec
                ra2 = new_event.RA
                poserr2 = new_event.sigmaR
                #icsign = ice[0].sigmaT
                #print 'Doing Likelihood calculation'
                llh = LLH(dec1,ra1,dec2,ra2,poserr1,poserr2,hwcsig)#,icsign)
                if llh != -1:
                    coincs.append(llh)
    return coincs

@app.task(ignore_result=True)
def ic_hawc(eventbuffer,max_id,new_event=None):
#def ic_hawc(eventbuffer,config,max_id):
    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print "Max Id Alert in DB: %d"%(idnum)

    Buffer = jsonpickle.decode(eventbuffer)
    new_event = jsonpickle.decode(new_event)

    config = ic_hawc_config()

    #Separate HAWC and IC events
    hwcevents = []
    ICevents = []
    for e in Buffer.events:
        if e.stream == streams['HAWC-DM']:
            hwcevents.append(e)
        elif e.stream == streams['IC-Singlet']:
            ICevents.append(e)
        else:
            print 'Event should not be part of this buffer'

    #Do the analysis
    if new_event.stream == streams['HAWC-DM']:
        result = coincAnalysis(new_event,ICevents)
    elif new_event.stream == streams['IC-Singlet']:
        result = coincAnalysis(new_event,hwcevents)
    else:
        print 'Event should not be part of this buffer'

    #Save results in DB

    print "Found %d coincidences"%(len(result))

    alerts = []


    for r in result:
        llh = r[3]
        dec = r[0]
        ra = r[1]
        sigmaR = np.sqrt(r[2])
        line = "LLH: "+str(llh)+"; Pos: dec: "+str(dec)+" RA:"+str(ra)+" Error Radius:"+str(sigmaR)+"\n"
        print line

        new_alert = Alert(config.stream,idnum+1,config.rev)
        new_alert.dec = dec
        new_alert.RA = ra
        new_alert.sigmaR = sigmaR
        new_alert.pvalue = llh
        new_alert.datetime = datetime.now()
        new_alert.observing = config.stream
        new_alert.nevents = 1
        alerts.append(new_alert)
        idnum = idnum+1
        # if new alert crosses threshold send email_alerts
        #f=open()
        #f.write(alert_to_voevent(new_alert))

    #Write results to the DB
    if len(alerts) > 0:
        db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
    print "###########"
