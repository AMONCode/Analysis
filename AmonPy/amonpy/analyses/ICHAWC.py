from __future__ import division
from __future__ import print_function
from builtins import range
from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write, db_populate_class
from amonpy.dbase.alert_to_voevent import *
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams, inv_alert_streams, gcn_streams
from amonpy.monitoring.monitor_funcs import slack_message

from amonpy.tools.IC_PSF import *
from amonpy.tools.IC_FPRD import *
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


import scipy as sc
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
def ic_hawc_config():
    """
    Returns an ICHAWC AlertConfig object
    """
    stream = alert_streams['IC-HAWC']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['IC-HAWC']
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
    config.N_thresh       = '{0:1,7:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2020,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

### Functions for the coincidence analysis
def insideHAWCBrightSources(dec,ra):
    CrabDec, CrabRA = 22.03,83.623
    Mrk421Dec, Mrk421RA = 38.15,166.15
    Mrk501Dec, Mrk501RA = 39.15,235.45
    G1Dec,G1RA = 17.9, 98.0
    G2Dec,G2RA = 15.0, 105.1
    c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
    lon, lat = c.galactic.l.value, c.galactic.b.value
    if spcang(ra,CrabRA,dec,CrabDec)<=1.3:
        return True
    elif spcang(ra,Mrk421RA,dec,Mrk421Dec)<=1.:
        return True
    elif spcang(ra,Mrk501RA,dec,Mrk501Dec)<=1.:
        return True
    elif spcang(ra,G1RA,dec,G1Dec)<=3.:
        return True
    elif spcang(ra,G2RA,dec,G2Dec)<=3.:
        return True
    elif lat<3.0 and lat>-3.0:
        if lon<90.0 and lon>0:
            return True
        else:
            return False
    else:
        return False

# HAWC PDF for spatial null and alternative hypotheses
hwcBkgfile = os.path.join(AmonPyDir,'data/hawc/hawc_bkg_intp.npy')
hwcBkg = np.load(hwcBkgfile, encoding = 'latin1',allow_pickle=True).item()
def probBkgHAWC(dec):
    """Spatial Bkg PDF for a HAWC hotspot. Based on data """
    if dec<-25.: return 0.00619
    if dec>64: return 0.00619
    return hwcBkg(dec)*180./(np.pi*2*np.pi)

def probSigHAWC(spc,sigma):
    """Spatial Signal PDF for a HAWC hotspot. Assumes a gaussian function over the sphere. """
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*(np.deg2rad(sigma)**2))
    return psf

icfprdFile = np.load(os.path.join(AmonPyDir,'data/icecube/FPRD_info.npz'),encoding = 'latin1',allow_pickle=True)
icbkg_interp = icfprdFile['B_spat_interp'].item()
def probBkgIC(cosTh):
    """Spatial Bkg PDF for a IceCube neutrino. Based on simulation"""
    b = icbkg_interp(cosTh)/4.8434e-5 #constant is normalization factor
    b = b*(np.pi/(180.*360.))
    return b

def probSigIC(sigR,muR,lamR):
    """Spatial Signal PDF for a IceCube neutrino. Based on simulation"""
    if lamR==-1:
        psf = log_norm_func2(sigR,muR)
    else:
        psf = comb_psfs2(sigR,muR,lamR,nlog_steps=50)
    return psf #in deg^2

def probSigIC2(spc,sigma):
    """Spatial Signal PDF for a IceCube neutrino. Assumes gaussian function over the sphere"""
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*sigma**2)
    return psf #in deg^2

# Probability of more than 2 neutrino given that we see one neutrino
def pNuCluster(events):
    """
    Function to calculate the probabiliyt of observing 2 or more neutrinos
    after one is already observed. Returns 1 if there's only one neutrino in
    the list.
    """
    val=1
    N=len(events)-1
    if N==1:
        return val
    else:
        lmb = 0.0066887 * events[0][4]*3600.*2*np.pi*(1-np.cos(np.deg2rad(3.5)))/(4*np.pi) #Rate=0.0066887 = 22334./ 3339043.sec
        val = stats.poisson.sf(N-2,lmb)
    return val

# Calculation of the p_value of the spatial llh. Trying to avoid several calls to CDF_LLH.npz
filename = os.path.join(AmonPyDir,'data/hawc_icecube/CDF_LLH_scramble.npz')
cdfLLH =  np.load(filename)
CDF = [] #dummy variable
for item in cdfLLH.items():
    CDF.append(item[1])
n = CDF[0]
b = CDF[1]
bin_centers = b[:-1] + 0.5*(b[1:] - b[:-1])
f = interp1d(bin_centers, n)
def pSpace(llh):
    if llh < bin_centers[0]:
        return 1.
    elif llh > bin_centers[-1]:
        print("This event has an even smaller p_value than the current interpolation range!!")
        return 1.-f(bin_centers[-1])
    else:
        return 1.-f(llh)

# Calculation of the p_value of IC.
fprd_obj=FPRD(fname=os.path.join(AmonPyDir,'data/icecube/FPRD_info.npz'))
def pHEN(cosTh,y,fprd=None):
    """Function to get the pvalue of an IceCube event"""
    if fprd is None:
        pval=fprd_obj.get_pval(cosTh,y=y)
    else:
        pval=fprd_obj.get_pval(cosTh,fprd=fprd)
    if pval>1.0:
        return 1.0
    else:
        return pval

def totalpHEN(events):
    """Function that combines the p-values of all IceCube events."""
    val=1
    N=len(events)
    if N==2:
        return val*events[1][-3]
    else:
        for i in range(1,N):
            val*=events[i][-3]
        return val

#Calculating the p_value of the analysis. Trying to avoid several calls to CDF_CHI2.npz
filename = os.path.join(AmonPyDir,'data/hawc_icecube/CDF_newChi2_scramble.npz')
cdfChi2 = np.load(filename)
CDF = [] #dummy variable
for item in cdfChi2.items():
    CDF.append(item[1])
n = CDF[0]
b = CDF[1]
xo = b[:-1] + 0.5*(b[1:] - b[:-1])
f2 = interp1d(xo, n)
def pChi2(chi2):
    if chi2 < xo[0]:
        return 1.
    elif chi2 > xo[-1]:
        print("This event has an even smaller p_value than the current interpolation range!!")
        return 1.-f2(xo[-1])
    else:
        return 1.-f2(chi2)

# Define an initial space log-likelihood for each event (dec and ra are coordinates of the source position)
def loglh(sigterm,bkgterm):
    return np.log(sigterm)-np.log(bkgterm)

# Find total log-likelihood considering multiplets: spatial and temporal terms
def spaceloglh(dec,ra,events):
    version = 0. #0: IC Gaussian PSF; 1: IC parameters PSF
    val = 0.
    for nut in events:
        dec1 = nut[1]
        ra1 = nut[2]
        spc=spcang(ra1,ra,dec1,dec)#in degs

        if nut[0]==7:
            sigma1 = nut[3]#in deg
            SH0=nut[5]
            SH1=probSigHAWC(spc,sigma1)
            #print "  HWC:",SH1,SH0
        if nut[0]==0:
            SH0=nut[6]
            try:
                if version == 0:
                    SH1=probSigIC2(spc,nut[3])
                elif version == 1:
                    SH1=nut[4](spc)/(2*np.pi*spc) #units in 1/deg^2
            except TypeError:
                SH1=nut[4](spc,0)

        # adding log-likelihood spatial terms
        val = val + loglh(SH1,SH0)
    return val

def temploglh(events):
    val=0.
    if len(events) > 2:
        T=0.
        for i in range(1,len(events)-1) :
            for j in range(i+1,len(events)) :
                # adding temporal term (T is a normlization factor that can be modified to match spatial terms)
                T += np.log(events[0][4]*3600.) - np.log(abs(((events[j][5]-events[i][5])).seconds))
        val+=T

    return val


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
            #print stderr
            print("Number of neutrinos: %d"%(len(ev)-1))
            pcluster=pNuCluster(ev)
            phwc = ev[0][-3]
            pspace = pSpace(-1*(solution.fun))#+temploglh(ev)))
            icpvalue = totalpHEN(ev)
            chi2 = -2 * np.log(pspace * phwc * pcluster * icpvalue) #The main quantity
            nnus = len(ev)-1

            ddof = nnus*2 + 6
            pvalChi2 = stats.chi2.sf(chi2,ddof)
            newchi2 = -np.log10(pvalChi2)
            pvalue = pChi2(newchi2) #
            far = np.power(10,-0.74*newchi2 + 5.40) #parameters from linear fit from archival data.

            coincs.append([solution.x[0],solution.x[1],stderr,newchi2,nnus,far,pvalue,ev])
    return coincs

def coincAnalysisHWC(new_event):
    """
    This function receives a HAWC event and looks for any IceCube events according to the Spatial
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
    if insideHAWCBrightSources(dec1,ra1):
        coincs = []
        return coincs


    hwcRT = float(new_param[0].value) #HAWC Rise Time
    hwcST = float(new_param[1].value) #HAWC Set Time
    hwcDuration = (hwcST - hwcRT)*23.96*3600 #From days to seconds
    hrt = Time(hwcRT,format='mjd')
    hrt.format = 'iso'
    hst = Time(hwcST,format='mjd')
    hst.format = 'iso'

    eventList = db_read.read_event_timeslice_streams([streams['IC-Singlet']],hrt.value,hwcDuration,
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
        #print "DeltaTH: ",spc
        #print "FPRD: ",e.false_pos

        if spc<3.5:

            poserr2 = e.sigmaR #If version is 0, this value will be used.
            param = db_read.read_parameters(e.stream,e.id,e.rev,HostFancyName,
                                            UserFancyName,PasswordFancy,DBFancyName)
            fprd = 0.0
            bdt_score = 0.0
            energy = 0.0
            for p in param:
                if p.name == 'signalness': bdt_score= p.value #sigacc = p.value ## Temporal solution to the FPRD
                else: sigacc = 1.0
                if p.name == 'lambdaR': lamR = p.value
                else: lamR = -1.0
                if p.name == 'sigmaR': sigR = p.value
                else: sigR = 1.0
                if p.name == 'muR': muR = p.value
                else: muR = 1.0
                if p.name == 'energy': energy = p.value
                #else: energy = 1000 #In GeV

            print("IC event: ")
            print("RA: {:0.1f} Dec: {:0.1f} Uncert: {:0.1f} Energy: {:0.1f} BDT: {:0.3f} ".format(ra2,dec2,sigR,energy,bdt_score))

            psfIC = probSigIC(sigR,muR,lamR)
            sinDec = np.sin(np.deg2rad(dec2))
            cosTh = -1*sinDec
            sinTh = np.sqrt(1-cosTh**2)
            bkgIC = np.abs(-1*sinTh*probBkgIC(cosTh))
            if np.rad2deg(np.arccos(cosTh)) > 82.:
                y=np.log10(energy)
            else:
                y=bdt_score
            pvalIC = pHEN(cosTh,y)
            datalist.append([streams['IC-Singlet'], dec2, ra2, poserr2, psfIC, pd.to_datetime(e.datetime), bkgIC, pvalIC, e.id, e.rev])

    alldatalist.append(datalist)

    all_ev_nut = [x for x in alldatalist if len(x)>1]

    coincs = maximizeLLH(all_ev_nut)

    return coincs

def coincAnalysisIC(new_event):
    coincs = []
    new_param = db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    new_event.datetime = pd.to_datetime(new_event.datetime)
    raIC = new_event.RA
    decIC = new_event.dec
    poserrIC = new_event.sigmaR

    eventList = db_read.read_events_angle_separation([streams['HAWC-DM']],3.5,raIC,decIC,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    #alldatalist= []
    #datalist = []
    #datalist.append([decIC,raIC,poserrIC])
    print("Probably a late IC event, not doing anything for now")
    for e in eventList:
        coincs.append(coincAnalysisHWC(e))

    return coincs

@app.task(ignore_result=True)
def ic_hawc(new_event=None):
    """
    This is the celery task, which receives a new event from the server and prepares the event to
    be analyzed.
    """
    max_id = db_read.alert_max_id(alert_streams['IC-HAWC'],HostFancyName,
                                       UserFancyName,
                                       PasswordFancy,
                                       DBFancyName)

    if max_id is None:
        idnum = 0
    else:
        idnum = max_id

    print("Max Id Alert in DB: %d"%(idnum))

    new_event = jsonpickle.decode(new_event, classes=Event)

    config = ic_hawc_config()


    #Do the analysis
    alerts = []
    alertline_lst = []

    send = True

    if new_event.stream == streams['HAWC-DM']:
        #Check that HAWC event is not close to another one,
        #since it could be the same event but from different Transit
        #if new_event.rev == 0:
            #alert_rev, send = HAWC_event_check(new_event)
             #prev_alerts = read_alert_timeslice(time_start,time_interval,host_name,user_name,
             #                         passw_name, db_name)
             #pd.to_datetime(new_event.datetime)

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
            #total = sum(dt.hour * 3600 + dt.minute * 60 + dt.second for dt in alertTime)
            #avg = total / len(alertTime)
            #minutes, seconds = divmod(int(avg),60)
            #hours,minutes = divmod(minutes,60)

            rev = 0
            alertid = idnum+1
            send = True

            if new_event.rev > 0:
                print("Using udpated information, new HAWC event has bigger significance")
                alertid,rev=db_read.get_latest_alert_info_from_event(alert_streams['IC-HAWC'],new_event.id,
                    HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                rev+=1
            else:
                prev_alerts = db_read.read_alert_timeslice_streams([alert_streams['IC-HAWC']],str(pd.to_datetime(new_event.datetime)-timedelta(seconds=20.*60)),40.*60,
                    HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                bestfar = far
                bestid = alertid
                bestrev = rev
                for pa in prev_alerts:
                    dangle = spcang(ra,pa.RA,dec,pa.dec)
                    if dangle>1.8:
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
            fname='amon_ic-hawc_%s_%s_%s.xml'%(new_alert.stream, new_alert.id, new_alert.rev)
            filen=os.path.join(AlertDir,fname)
            print(filen)
            f1=open(filen, 'w+')

            #Create Alert xml file
            if far<=4.0 and far>0.01:
                alertname="IceCube-HAWC-{}{}{}{}".format(timest[2:4],timest[5:7],timest[8:10],"A")
            else:
                alertname="IC-HAWC-{}".format(new_alert.id)

            VOAlert = Alert2VOEvent([new_alert],'nu_em_coinc','Gamma-Nu Coincidence Alert from Daily Monitoring HAWC and IceCube',gcn_streams["Gamma-Nu-Coinc"],new_alert.id)

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
            print('  First IC time: ',alertTime[0])
            print('  Last IC time: ',alertTime[-1])
            print('HAWC Set Time: ',new_event.datetime)
            #print 'HAWC Set Time: ',datetime(pd.to_datetime(new_event.datetime)) + timedelta(seconds=r[0][4])
            content = 'Alert ID: %d, Rev: %d\n Position RA: %0.2f Dec: %0.2f Ang.Err.: %0.3f\n P-value: %0.3f\n Chi2: %0.2f\n FAR: %0.2f yr^-1\n NNus: %d'%(alertid,rev,ra,dec,sigmaR*1.18,new_alert.pvalue,chi2,new_alert.false_pos,nev)
            print(content)

            content2 = 'IceCube-HAWC alert\nName:{}\nAlert ID: {}\nRev: {}\nSearch Time {} - {}\nRA: {:0.2f} deg J2000\nDec: {:0.2f} deg J2000\nAng Err (50%) {:0.2f} deg\nAng. Err (90%) {:0.2f} deg\nFAR: {} yr^-1'.format(alertname,alertid,rev,
                    new_alert.datetime-timedelta(seconds=new_alert.deltaT),new_alert.datetime,ra,dec,1.18*sigmaR,2.15*sigmaR,new_alert.false_pos)
            if far<0.1:
                content2 = 'IceCube-HAWC alert\nName:{}\nAlert ID: {}\nRev: {}\nSearch Time {} - {}\nRA: {:0.2f} deg J2000\nDec: {:0.2f} deg J2000\nAng Err (50%) {:0.2f} deg\nAng. Err (90%) {:0.2f} deg\nFAR: {} yr^-1'.format(alertname,alertid,rev,
                        new_alert.datetime-timedelta(seconds=new_alert.deltaT),new_alert.datetime,ra,dec,1.18*sigmaR,2.15*sigmaR,"<0.1")
            emails=['hgayala@psu.edu']
            emails2=['hgayala@psu.edu','dorner@astro.uni-wuerzburg.de','julie.e.mcenery@nasa.gov','fabian.schussler@cea.fr','tmorokuma@ioa.s.u-tokyo.ac.jp','hawc-followup@umdgrb.umd.edu','roc@icecube.wisc.edu','alberto@inaoep.mx','tboroson@lcogt.net','lipunov@sai.msu.ru','Thomas.A.Prince@jpl.nasa.gov','miguel@psu.edu','scott.d.barthelmy@nasa.gov','adf15@psu.edu','konstancja.satalecka@desy.de','brunner@cppm.in2p3.fr','dornic@cppm.in2p3.fr']

            title='AMON IC-HAWC alert'
            # TEMPORAL UNITL GCN IS ON
            if far<=4.0:
                email_alerts.alert_email_content([new_alert],content,title)
                email_alerts.alert_email_content_emails(content2,title,emails2)
                slack_message(title+"\n"+content+"\n"+filen,channel,prodMachine,token=token)
            if far<3650.:# and far>0.01:
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
            #alertLine for IceCube
            for n in nuEvents:
                al = AlertLine(new_alert.stream,new_alert.id,new_alert.rev,streams['IC-Singlet'],n[-2],n[-1])
                alertline_lst.append(al)
        #Write results to the DB
        if len(alerts) > 0:
            db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
            db_write.write_alertline(HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alertline_lst)
    elif new_event.stream == streams['IC-Singlet']:
        print("Neutrino event. Not doing anything for now.")
    #    result = []#coincAnalysisIC(new_event)
    #    for res in result:
            # for r in res:
            #     pvalue = r[3]
            #     dec = r[0]
            #     ra = r[1]
            #     sigmaR = r[2]
            #     chi2 = r[4]
            #     nev = r[5]
            #     #line = "p_value: "+str(pvalue)+"; Pos: dec: "+str(dec)+" RA:"+str(ra)+" Error Radius:"+str(sigmaR)+"\n"
            #     #print line
            #
            #     new_alert = Alert(config.stream,idnum+1,config.rev)
            #     new_alert.dec = dec
            #     new_alert.RA = ra
            #     new_alert.sigmaR = sigmaR
            #     new_alert.deltaT = events[0][4]*3600.
            #     new_alert.pvalue = 1.#pvalue
            #     new_alert.datetime = datetime.now()
            #     new_alert.observing = config.stream
            #     new_alert.nevents = nev
            #     new_alert.type = 'test'
            #     alerts.append(new_alert)
            #     idnum = idnum+1
            #     # if new alert crosses threshold send email_alerts
            #     #if chi2>=60:
            #     #f=open()
            #     #f.write(alert_to_voevent(new_alert))
            #
            # #Write results to the DB
            # if len(alerts) > 0:
            #     db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
    else:
        print('Event should not be part of this analysis')



    print("###########")
