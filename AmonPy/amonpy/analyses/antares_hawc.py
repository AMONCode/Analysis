from __future__ import division
from __future__ import print_function

from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write, db_populate_class
from amonpy.dbase.alert_to_voevent import *
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams, inv_alert_streams, gcn_streams
from amonpy.monitoring.monitor_funcs import slack_message

from amonpy.tools.hawc_functions import *
from amonpy.tools.antares_functions import *
from amonpy.tools.angularsep import spcang
from amonpy.tools.config import AMON_CONFIG

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy import units as u
from astropy.time import Time

import numpy as np
import pandas as pd

from datetime import datetime, timedelta
import netrc, jsonpickle, os

import scipy
from scipy import optimize, stats, special
from scipy.interpolate import interp1d

import subprocess, shutil, os

# DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs','alertdir')
AmonPyDir = AMON_CONFIG.get('dirs','amonpydir')
prodMachine = eval(AMON_CONFIG.get('machine','prod'))

if prodMachine:
    channel = 'alerts'
else:
    channel = 'test-alerts'

UserFancyName = AMON_CONFIG.get('database','username')
PasswordFancy = AMON_CONFIG.get('database','password')
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')
token = AMON_CONFIG.get('alerts','slack_token')#Slack token

# Alert configuration
def antares_hawc_config():
    """
    Returns an ANTARES-HAWC AlertConfig object
    """
    stream = alert_streams['ANTARES-HAWC']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['ANTARES-HAWC']
    config.deltaT         = 100.00 #80000.0 #100.0               # seconds
    config.bufferT        = 86400.00 #1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 6.48 #10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc= 'N/A'
    config.skymap_val2Desc= 'N/A'
    config.skymap_val3Desc= 'N/A'
    config.N_thresh       = '{1:1,7:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2021,1,1,0,0,0,0)
    config.validStop      = datetime(2025,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config


def loglh(sigterm,bkgterm):
    return np.log(sigterm)-np.log(bkgterm)

def spaceloglh(dec,ra,events):
    val = 0.
    for nut in events:
        dec1 = nut[1]
        ra1 = nut[2]
        spc=spcang(ra1,ra,dec1,dec)#in degs

        if nut[0]==7:
            sigma1 = nut[3]#in deg
            SH0=nut[5]
            SH1=probSigHAWC(spc,sigma1)
        if nut[0]==1:
            sigma1 = nut[3]#in deg
            SH0=nut[6]
            SH1=probSigANTARES(spc,sigma1)

        # adding log-likelihood spatial terms
        val = val + loglh(SH1,SH0)
    return val

# Calculation of the p_value of the spatial llh. Trying to avoid several calls to CDF_LLH.npz
filename = os.path.join(AmonPyDir,'data/antares_hawc/CDF_LLH_scramble_RT_new.npz')
cdfLLH =  np.load(filename)
CDF = [] #dummy variable
for item in cdfLLH.items():
    CDF.append(item[1])
b = CDF[0]
n = CDF[1]
f = interp1d(b, n)
def pSpace(llh):
    if llh < b[0]:
        return 1.
    elif llh > b[-1]:
        print("This event has an even smaller p_value than the current interpolation range!!")
        return 1.-f(bin_centers[-1])
    else:
        return 1.-f(llh)

#Calculating the p_value of the analysis. Trying to avoid several calls to CDF_CHI2.npz
filename = os.path.join(AmonPyDir,'data/antares_hawc/CDF_RS_scramble_RT_new.npz')
cdfChi2 = np.load(filename)
CDF = [] #dummy variable
for item in cdfChi2.items():
    CDF.append(item[1])
b2 = CDF[0]
n2 = CDF[1]
f2 = interp1d(b2, n2)
def pChi2(chi2):
    if chi2 < b2[0]:
        return 1.
    elif chi2 > b2[-1]:
        print("This event has an even smaller p_value than the current interpolation range!!")
        return 1.-f2(b2[-1])
    else:
        return 1.-f2(chi2)



def maximizeLLH(all_events):

    coincs=[]
    for ev in all_events:
        try:
            solution = sc.optimize.minimize(lambda x: -spaceloglh(x[0],x[1],ev),np.array([ev[0][1]+0.1,ev[0][2]+0.1]), method = 'SLSQP')
        except ValueError:
            try:
                solution = sc.optimize.minimize(lambda x: -spaceloglh(x[0],x[1],ev),np.array([ev[0][1]+0.1,ev[0][2]+0.1]), method = 'BFGS')
            except ValueError:
                print("Error in minimization")
                return coincs
        res = list(solution.x)
        stderr = 0.

        if solution.success:
            for part in ev:
                #print part[0],part[1],part[2],solution.x[0],solution.x[1]

                stderr += 1./(part[3]**2)

            stderr = np.sqrt(1/stderr)
            #print("Number of neutrinos: %d"%(len(ev)-1))
            pcluster=pNuCluster(ev)
            phwc = ev[0][-3]
            logspace = -1*(solution.fun)
            pspace = pSpace(logspace)
            antpvalue = totalpHEN(ev)
            chi2 = -2 * np.log(pspace * phwc * pcluster * antpvalue) #The main quantity
            nnus = len(ev)-1

            ddof = nnus*2 + 6
            pvalChi2 = stats.chi2.sf(chi2,ddof)
            newchi2 = -np.log10(pvalChi2)
            pvalue = pChi2(newchi2) #
            far = np.power(10,-1.29*newchi2 + 1.52) #parameters from linear fit from archival data.

            coincs.append([solution.x[0],solution.x[1],stderr,newch2,nnus,far,pvalue,ev])
    return coincs

def coincAnalysisHWC(new_event):
    """
    This function receives a HAWC event and looks for any ANTARES events according to the Spatial
    and Time constraints.
    """

    new_param = db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    dec1 = new_event.dec
    ra1 = new_event.RA
    poserr1 = new_event.sigmaR
    hwcsig = new_param[2].value
    phwc = 1.-stats.norm.cdf(hwcsig) #HAWC p_value

    #Check that event is outside HAWC bright sources: Plane, Crab, Geminga, Gamigo, Mrk 421, Mrk 501
    if insideHAWCBrightSources(dec1,ra1) is True:
        coincs = []
        return coincs


    hwcRT = float(new_param[0].value) #HAWC Rise Time
    hwcST = float(new_param[1].value) #HAWC Set Time
    hwcDuration = (hwcST - hwcRT)*23.96*3600 #From days to seconds
    hrt = Time(hwcRT,format='mjd')
    hrt.format = 'iso'
    hst = Time(hwcST,format='mjd')
    hst.format = 'iso'

    eventList = db_read.read_event_timeslice_streams([streams['Antares']],hrt.value,hwcDuration,
                             HostFancyName,UserFancyName,
                             PasswordFancy,DBFancyName)

    alldatalist= []
    datalist = []
    datalist.append([streams['HAWC-DM'],dec1,ra1,poserr1,hwcDuration,probBkgHAWC(dec1),phwc,new_event.id,new_event.rev])
    print("HAWC event: ")
    print("Pos: %0.2f,%0.2f,%0.2f"%(ra1,dec1,poserr1))
    print("ID: {}".format(new_event.id))

    for e in eventList:
        dec2 = e.dec
        ra2 = e.RA
        spc=spcang(ra1,ra2,dec1,dec2)

        if spc<3.5:

            poserr2 = 0.697 #ANTARES has a fixed angErr for realtime. This is the 1sigma containment radius

            pvalANT = e.pvalue

            print("ANTARES event: ")
            print("RA: {:0.1f} Dec: {:0.1f} Uncert: {:0.1f} p-value: {:0.3e}".format(ra2,dec2,poserr2,pval))

            bkgANT = probBkgANTARES(dec2)
            datalist.append([streams['Antares'], dec2, ra2, poserr2, pd.to_datetime(e.datetime), bkgANT, pvalANT, e.id, e.rev])

    alldatalist.append(datalist)

    all_ev_nut = [x for x in alldatalist if len(x)>1]

    coincs = maximizeLLH(all_ev_nut)

    return coincs

def coincAnalysisANTARES(new_event):
    coincs = []
    new_param = db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    new_event.datetime = pd.to_datetime(new_event.datetime)
    raANT = new_event.RA
    decANT = new_event.dec
    poserrANT = new_event.sigmaR

    eventList = db_read.read_events_angle_separation([streams['HAWC-DM']],3.5,raANT,decANT,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    print("Probably a late ANTARES event, not doing anything for now")
    for e in eventList:
        coincs.append(coincAnalysisHWC(e))

    return coincs

@app.task(ignore_result=True)
def antares_hawc(new_event=None):
    """
    This is a celery task for the antares+hawc analysis
    """
    max_id = db_read.alert_max_id(alert_streams['ANTARES-HAWC'],HostFancyName,
                                       UserFancyName,
                                       PasswordFancy,
                                       DBFancyName)

    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print("Max Id Alert in DB: %d"%(idnum))

    new_event = jsonpickle.decode(new_event, classes=Event)

    config = antares_hawc_config()

    #Do the analysis
    alerts = []
    alertline_lst = []

    send = True

    if new_event.stream == streams['HAWC-DM']:
        result = coincAnalysisHWC(new_event)
        #Save results in DB
        print("Found %d coincidences"%(len(result)))

        for r in result:
            dec = r[0]
            ra = r[1]
            sigmaR = r[2]
            chi2 = r[3]
            nev = r[4]
            far = r[5]
            pvalue = 1.#r[6]
            nuEvents = r[-1][1:]
            phEvent = r[-1][0]
            alertTime = []

            for j in nuEvents:
                alertTime.append(j[5])

            rev = 0
            alertid = idnum+1
            send = True

            if new_event.rev > 0:
                print("Using udpated information, new HAWC event has bigger significance")
                alertid,rev=db_read.get_latest_alert_info_from_event(alert_streams['ANTARES-HAWC'],new_event.id,
                    HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                if alertid<0:
                    alertid = idnum+1
                rev+=1
            else:
                prev_alerts = db_read.read_alert_timeslice_streams([alert_streams['ANTARES-HAWC']],str(pd.to_datetime(new_event.datetime)-timedelta(seconds=20.*60)),40.*60,
                    HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                bestfar = far
                bestid = alertid
                bestrev = rev
                for pa in prev_alerts:
                    dangle = spcang(ra,pa.RA,dec,pa.dec)
                    if dangle>2.0:
                        continue

                    if bestfar>pa.false_pos:
                        send=False
                    if pa.id<bestid:
                        bestid = pa.id
                    if pa.rev>=bestrev:
                        bestrev =pa.rev + 1
                alertid = bestid
                rev = bestrev

            new_alert = Alert(config.stream,alertid,rev)
            new_alert.dec = float("{:.2f}".format(dec))
            new_alert.RA = float("{:.2f}".format(ra))
            new_alert.sigmaR = float("{:.2f}".format(1.18*sigmaR)) #Send 50% r=sigma(-2*ln(1-cdf))
            new_alert.deltaT = float("{:.2f}".format(phEvent[4])) # in seconds
            new_alert.pvalue = 1.#pvalue
            new_alert.false_pos = float("{:.2f}".format(far))
            new_alert.nevents = nev  #Number of neutrinos

            #We will use the end of the hawc transit for the alert time
            new_alert.datetime = pd.to_datetime(new_event.datetime) #using HAWC set time
            timest = str(new_alert.datetime)
            new_alert.observing = config.stream

            if (prodMachine==True):
                new_alert.type='observation'
            else:
                new_alert.type = 'test'
            alerts.append(new_alert)

            # if new alert crosses threshold send email_alerts and GCN
            fname='amon_antares-hawc_%s_%s_%s.xml'%(new_alert.stream, new_alert.id, new_alert.rev)
            filen=os.path.join(AlertDir,fname)
            print(filen)
            f1=open(filen, 'w+')

            #Create Alert xml file
            eventdate="{}{}{}{}".format(timest[2:4],timest[5:7],timest[8:10],"A")
            alertname="ANTARES-HAWC-{}".format(new_alert.id)

            VOAlert = Alert2VOEvent([new_alert],'nu_em_coinc','Nu-EM Coincidence Alert from Daily Monitoring HAWC and ANTARES',gcn_streams["Gamma-Nu-Coinc"],new_alert.id)

            alertparams = []
            apar = VOAlert.MakeParam(name="gcn_stream",ucd="meta.number",unit="",datatype="int",value=gcn_streams["Gamma-Nu-Coinc"],description="GCN Socket Identification")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="amon_stream",ucd="meta.number",unit="",datatype="int",value=new_alert.stream,description="AMON Alert stream identification")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="event_id",ucd="meta.number",unit="",datatype="int",value=new_alert.id,description='AMON id number')
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="run_id",ucd="meta.number",unit="",datatype="int",value="0",description='Run ID number. Zero for coincidences')
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="rev",ucd="meta.number",unit="",datatype="int",value=new_alert.rev,description="Revision of the alert")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="nameID",ucd="meta.id",unit="",datatype="string",value="{}".format(alertname),description="Name of the alert")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="event_date",ucd="meta.id",unit="",datatype="string",value="{}".format(eventdate),description="Date of the alert")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="deltaT",ucd="time.timeduration",unit="s",datatype="float",value=new_alert.deltaT,description="Transit time of the HAWC hotspot")
            alertparams.append(apar)
            if far<0.1:
                apar = VOAlert.MakeParam(name="far", ucd="stat.probability",unit="yr^-1", datatype="float", value=0.1, description="False Alarm Rate (<0.1)")
                alertparams.append(apar)
            else:
                apar = VOAlert.MakeParam(name="far", ucd="stat.probability",unit="yr^-1", datatype="float", value=new_alert.false_pos, description="False Alarm Rate")
                alertparams.append(apar)
            apar = VOAlert.MakeParam(name="pvalue", ucd="stat.probability",unit="", datatype="float", value=new_alert.pvalue, description="P-value of the alert")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name="src_error90", ucd="stat.error.sys",unit="deg", datatype="float", value=2.15*sigmaR, description="Angular error of the source (90% containment)")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name='private',ucd="meta.number",unit='',datatype='int',value=0,description="Indicates that alert is private if 1, no if 0")
            alertparams.append(apar)
            apar = VOAlert.MakeParam(name='retraction',ucd="meta.number",unit='',datatype='int',value=0,description="Indicates alert is retracted if 1, no retracted if 0")
            alertparams.append(apar)
            VOAlert.WhatVOEvent(alertparams)
            VOAlert.MakeWhereWhen([new_alert])
            xmlForm = VOAlert.writeXML()

            f1.write(xmlForm)
            f1.close()
            MOVEFILE=True

            content = 'Times: '
            print(content)
            print('Time of Alert: ',new_alert.datetime)
            print('  First ANTARES time: ',alertTime[0])
            print('  Last ANTARES time: ',alertTime[-1])
            print('HAWC Set Time: ',new_event.datetime)
            #print 'HAWC Set Time: ',datetime(pd.to_datetime(new_event.datetime)) + timedelta(seconds=r[0][4])
            content = 'Alert ID: %d, Rev: %d\n Position RA: %0.2f Dec: %0.2f Ang.Err.: %0.3f\n P-value: %0.3f\n Chi2: %0.2f\n FAR: %0.2f yr^-1\n NNus: %d'%(alertid,rev,ra,dec,sigmaR*1.18,new_alert.pvalue,chi2,new_alert.false_pos,nev)
            print(content)

            content2 = 'ANTARES-HAWC alert\nName:{}\nAlert ID: {}\nRev: {}\nSearch Time {} - {}\nRA: {:0.2f} deg J2000\nDec: {:0.2f} deg J2000\nAng Err (50%) {:0.2f} deg\nAng. Err (90%) {:0.2f} deg\nFAR: {} yr^-1'.format(alertname,alertid,rev,
                    new_alert.datetime-timedelta(seconds=new_alert.deltaT),new_alert.datetime,ra,dec,1.18*sigmaR,2.15*sigmaR,new_alert.false_pos)
            if far<0.1:
                content2 = 'ANTARES-HAWC alert\nName:{}\nAlert ID: {}\nRev: {}\nSearch Time {} - {}\nRA: {:0.2f} deg J2000\nDec: {:0.2f} deg J2000\nAng Err (50%) {:0.2f} deg\nAng. Err (90%) {:0.2f} deg\nFAR: {} yr^-1'.format(alertname,alertid,rev,
                        new_alert.datetime-timedelta(seconds=new_alert.deltaT),new_alert.datetime,ra,dec,1.18*sigmaR,2.15*sigmaR,"<0.1")
            emails=['hgayala@psu.edu']
            emails2=['hgayala@psu.edu','dorner@astro.uni-wuerzburg.de','julie.e.mcenery@nasa.gov','fabian.schussler@cea.fr','tmorokuma@ioa.s.u-tokyo.ac.jp','hawc-followup@umdgrb.umd.edu','roc@icecube.wisc.edu','alberto@inaoep.mx','tboroson@lcogt.net','lipunov@sai.msu.ru','Thomas.A.Prince@jpl.nasa.gov','miguel@psu.edu','scott.d.barthelmy@nasa.gov','adf15@psu.edu','konstancja.satalecka@desy.de','brunner@cppm.in2p3.fr','dornic@cppm.in2p3.fr']

            title='AMON ANTARES-HAWC alert'
            # TEMPORAL UNITL GCN IS ON
            if far<=4.0:
                email_alerts.alert_email_content([new_alert],content,title)
                #email_alerts.alert_email_content_emails(content2,title,emails2)
                slack_message(title+"\n"+content+"\n"+filen,channel,prodMachine,token=token)
            if far<=4.0 and far>0.01:
                print("ID: %d"%new_alert.id)
                print("Alert Stream: %s"%inv_alert_streams[new_alert.stream])
                #fname.write(alert_to_voevent(new_alert))
                if (prodMachine == True and send == True):
                    try:
                        cmd = ['/home/ubuntu/Software/miniconda3/bin/comet-sendvo','-f',filen]
                        #cmd.append('--file=' + filen)
                        # just for dev to prevent sending hese both from dev and pro machine
                        #print "uncoment this if used on production"
                        subprocess.check_call(cmd)
                        #shutil.move(filen, os.path.join(AlertDir,"archive/",fname))

                    except subprocess.CalledProcessError as e:
                        print("Send alert failed")
                        logger.error("send_voevent failed")
                        logger.error("File: {}".format(fname))
                        MOVEFILE=False
                        raise e
                    #else:
                        #shutil.move(filen, os.path.join(AlertDir,"archive/",fname))
                #else:
                email_alerts.alert_email_content_emails(content2,title,emails)
                slack_message(title+"\n"+content+"\n"+filen,"test-alerts",False,token=token)
            elif far<0.1:
                email_alerts.alert_email_content_emails(content2,title+" LOWFAR",emails)
                slack_message(title+"\n"+content2+"\n"+fname,channel,prodMachine,token=token)

            if MOVEFILE:
                shutil.move(filen, os.path.join(AlertDir,"archive/",fname))

            #alertLine for HAWC
            al = AlertLine(new_alert.stream,new_alert.id,new_alert.rev,streams['HAWC-DM'],phEvent[-2],phEvent[-1])
            alertline_lst.append(al)
            #alertLine for ANTARES
            for n in nuEvents:
                al = AlertLine(new_alert.stream,new_alert.id,new_alert.rev,streams['Antares'],n[-2],n[-1])
                alertline_lst.append(al)
        #Write results to the DB
        if len(alerts) > 0:
            db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
            db_write.write_alertline(HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alertline_lst)
    elif new_event.stream == streams['Antares']:
        print("Neutrino event. Not doing anything for now.") 
    else:
        print('Event should not be part of this analysis')

    print("###########")
