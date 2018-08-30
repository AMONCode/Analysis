from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase.alert_to_voevent import *
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams, inv_alert_streams

from amonpy.tools.IC_PSF import *
from amonpy.tools.IC_FPRD import *
from amonpy.tools.angularsep import spcang
from amonpy.tools.config import AMON_CONFIG

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy.time import Time


import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc, jsonpickle, os


import scipy as sc
from scipy import optimize, stats, special
from scipy.interpolate import interp1d

import subprocess, shutil, os, subprocess

# DB configuration
HostFancyName = AMON_CONFIG.get('database', 'host_name')#Config.get('database', 'host_name')
AlertDir = AMON_CONFIG.get('dirs','alertdir')
AmonPyDir = AMON_CONFIG.get('dirs','amonpydir')
prodMachine = eval(AMON_CONFIG.get('machine','prod'))

UserFancyName = AMON_CONFIG.get('database','username')#nrc.hosts[HostFancyName][0]
PasswordFancy = AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#Config.get('database', 'realtime_dbname')

# Alert configuration
def ic_hawc_config():
    """
    Returns an ICHAWC AlertConfig object
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

### Functions for the coincidence analysis
# HAWC PDF for spatial null and alternative hypotheses
#hwcBkgfile = os.path.join(AmonPyDir,'analyses/hawc_bkg_intp.npy')
hwcBkgfile = os.path.join(AmonPyDir,'data/hawc/hawc_bkg_intp.npy')

hwcBkg = np.load(hwcBkgfile).item()
def probBkgHAWC(dec):
    """Spatial Bkg PDF for a HAWC hotspot. Based on data """
    if dec<-25.: return 0.00619
    if dec>64: return 0.00619
    return hwcBkg(dec)*180./(np.pi*2*np.pi)

def probSigHAWC(spc,sigma):
    """Spatial Signal PDF for a HAWC hotspot. Assumes a gaussian function over the sphere. """
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*(np.deg2rad(sigma)**2))
    return psf


##IC PDFs for spatial null hypotheses
## The alternative  is given by an interpolator for each event.
icfprdFile = np.load(os.path.join(AmonPyDir,'data/icecube/FPRD_info.npz'))
icbkg_interp = icfprdFile['B_spat_interp'].item()
def probBkgIC(cosTh):
    """Spatial Bkg PDF for a IceCube neutrino. Based on simulation"""
    b = icbkg_interp(cosTh)/4.8434e-5 #constant is normalization factor
    b = b*(np.pi/(180.*360.))
    return b

# def probBkgIC(sinDec):
#     x=sinDec
#     #numbers obtained from archival data after doing a fit
#     a=1.035595
#     x0=-0.117645
#     g1 = 0.81984
#     g2 = 1.655227
#     y = a*(1/np.pi) * ((g1/2)/((x-x0)**2 + (g1**2/4))) * ((x-x0)<0)
#     y+= (a*g2/g1)*((1/np.pi) * ((g2/2)/((x-x0)**2 + (g2**2/4))) ) * ((x-x0)>=0)
#     return y*np.pi/(180.*360.)# units of deg^2, SigPSF is given in deg^2 #/(2*np.pi)

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
filename = os.path.join(AmonPyDir,'analyses/newCDF_LLH_200yr.npz')
#filename = os.path.join(AmonPyDir,'data/hawc/CDF_LLH.npz')
cdfLLH =  np.load(filename)
CDF = [] #dummy variable
for item in cdfLLH.iteritems():
    CDF.append(item[1])
n = CDF[0]
b = CDF[1]
bin_centers = b[:-1] + 0.5*(b[1:] - b[:-1])
f = interp1d(bin_centers, n)
def pSpace(llh):
    if llh < bin_centers[0]:
        return 1.
    elif llh > bin_centers[-1]:
        print "This event has an even smaller p_value than the current interpolation range!!"
        return 1.-f(bin_centers[-1])
    else:
        return 1.-f(llh)

# Calculation of the p_value of IC.
#filename = os.path.join(AmonPyDir,'analyses/log10fprd_up_trunc_intp_bwp05_xf5_yf1.npy')
filename = os.path.join(AmonPyDir,'data/icecube/log10fprd_up_trunc_intp_bwp05_xf5_yf1.npy')
Rup = np.load(filename).item()
#filename = os.path.join(AmonPyDir,'analyses/log10fprd_down_intp_bwp01.npy')
filename = os.path.join(AmonPyDir,'data/icecube/log10fprd_down_intp_bwp01.npy')
Rdn = np.load(filename).item()

#fprd_obj=FPRD(fname=os.path.join(AmonPyDir,'analyses/FPRD_info.npz'))
fprd_obj=FPRD(fname=os.path.join(AmonPyDir,'data/icecube/FPRD_info.npz'))
def pHEN(cosTh,fprd):
    """Function to get the pvalue of an IceCube event"""
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
        return val*events[1][-1]
    else:
        for i in range(1,N):
            val*=events[i][-1]
        return val

#Calculating the p_value of the analysis. Trying to avoid several calls to CDF_CHI2.npz
filename = os.path.join(AmonPyDir,'analyses/newCDF_newChi2_200.npz')
#filename = os.path.join(os.path.split(AmonPyDir,'data/analysis/HWCIC_CDF_Chi2.npz')
cdfChi2 = np.load(filename)

CDF = [] #dummy variable
for item in cdfChi2.iteritems():
    CDF.append(item[1])
n = CDF[0]
b = CDF[1]
xo = b[:-1] + 0.5*(b[1:] - b[:-1])
f2 = interp1d(xo, n)
def pChi2(chi2):
    if chi2 < xo[0]:
        return 1.
    elif chi2 > xo[-1]:
        print "This event has an even smaller p_value than the current interpolation range!!"
        return 1.-f2(xo[-1])
    else:
        return 1.-f2(chi2)

# Define an initial space log-likelihood for each event (dec and ra are coordinates of the source position)
#def loglh(dec1,ra1,dec,ra,sigma1,bkgterm):
def loglh(sigterm,bkgterm):
    return np.log(sigterm)-np.log(bkgterm)

# Find total log-likelihood considering multiplets: spatial and temporal terms
def spaceloglh(dec,ra,events):
#def tloglh_time(dec,ra,events):
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
                print "Error in minimization"
                return coincs
        res = list(solution.x)
        stderr = 0.


        if solution.success:
            for part in ev:
                #print part[0],part[1],part[2],solution.x[0],solution.x[1]

                stderr += 1./(part[3]**2)

            stderr = np.sqrt(1/stderr)
            #print stderr
            print "Number of neutrinos: %d"%(len(ev)-1)
            pcluster=pNuCluster(ev)
            phwc = ev[0][-1]
            pspace = pSpace(-1*(solution.fun+temploglh(ev)))
            icpvalue = totalpHEN(ev)
            chi2 = -2 * np.log(pspace * phwc * pcluster * icpvalue) #The main quantity
            nnus = len(ev)-1
            #pchi2 = pChi2(chi2) #The p-value of the chi2 distribution
            coincs.append([solution.x[0],solution.x[1],stderr,chi2,nnus,ev])#,pcluster,hwcsigma,ev])
    return coincs

def coincAnalysisHWC(new_event):
    """
    This function receives a HAWC event and looks for any IceCube events according to the Spatial
    and Time constraints.
    """

    new_param = db_read.read_parameters(new_event.stream,new_event.id,new_event.rev,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    hwcRT = float(new_param[0].value) #HAWC Rise Time
    hwcST = float(new_param[1].value) #HAWC Set Time
    hwcDuration = (hwcST - hwcRT)*23.96*3600 #From days to seconds
    hrt = Time(hwcRT,format='mjd')
    hrt.format = 'iso'
    #hst = Time(hwcST,format='mjd')
    #hst.format = 'iso'

    eventList = db_read.read_event_timeslice_streams([streams['IC-Singlet']],hrt.value,hwcDuration,
                             HostFancyName,UserFancyName,
                             PasswordFancy,DBFancyName)

    dec1 = new_event.dec
    ra1 = new_event.RA
    poserr1 = new_event.sigmaR
    hwcsig = new_param[2].value
    phwc = 1.-stats.norm.cdf(hwcsig) #HAWC p_value

    alldatalist= []
    datalist = []
    datalist.append([streams['HAWC-DM'],dec1,ra1,poserr1,hwcDuration,probBkgHAWC(dec1),phwc])
    print "HAWC event: "
    print "Pos: %0.2f,%0.2f,%0.2f"%(ra1,dec1,poserr1)

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
            for p in param:
                if p.name == 'signalness': fprd = p.value #sigacc = p.value ## Temporal solution to the FPRD
                else: sigacc = 1.0
                if p.name == 'lambdaR': lamR = p.value
                else: lamR = -1.0
                if p.name == 'sigmaR': sigR = p.value
                else: sigR = 1.0
                if p.name == 'muR': muR = p.value
                else: muR = 1.0
                if p.name == 'energy': energy = p.value
                else: energy = 1000 #1 TeV?

            #The next lines will be deleted after the false_pos has values in the realtime stream
            if e.false_pos != 0.0:
                fprd = e.false_pos  #TEMPORAL SOLUTION FOR FPRD (Currently is the value of signalness)
            if fprd ==0.:
                cosz = np.sin(np.deg2rad(dec2)) #cos(zenith)=sin(Dec) for IC since the zenith = -90deg in dec
                if cosz <0.13:
                    fprd = np.power(10,Rup(cosz,np.log10(energy)))
                else:
                    fprd = np.power(10,Rdn(cosz,0.015)) #fixed at a BDT score value for now

            #if lamR==-1:
                #psfIC = log_norm_func2(sigR,muR)
            #else:
                #psfIC = comb_psfs2(sigR,muR,lamR,nlog_steps=50)
            print "IC event: "
            print "Pos: %0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2e "%(ra2,dec2,sigR,muR,lamR,e.sigmaR,fprd)

            psfIC = probSigIC(sigR,muR,lamR)
            #bkgIC = np.cos(np.deg2rad(dec2))*probBkgIC(np.sin(np.deg2rad(dec2)))
            sinDec = np.sin(np.deg2rad(dec2))
            cosTh = -1*sinDec
            sinTh = np.sqrt(1-cosTh**2)
            bkgIC = np.abs(-1*sinTh*probBkgIC(cosTh))
            #pvalIC = pHEN(np.sin(np.deg2rad(dec2)),fprd)
            pvalIC = pHEN(cosTh,fprd)
            datalist.append([streams['IC-Singlet'],dec2,ra2,poserr2,psfIC,pd.to_datetime(e.datetime), bkgIC , pvalIC])

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

    eventList = db_read.read_events_angle_sepration([streams['HAWC-DM']],3.5,raIC,decIC,HostFancyName,
                                        UserFancyName,PasswordFancy,DBFancyName)

    #alldatalist= []
    #datalist = []
    #datalist.append([decIC,raIC,poserrIC])
    print "Probably a late IC event, not doing anything for now"
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

    print "Max Id Alert in DB: %d"%(idnum)

    new_event = jsonpickle.decode(new_event)

    config = ic_hawc_config()


    #Do the analysis
    alerts = []
    if new_event.stream == streams['HAWC-DM']:
        result = coincAnalysisHWC(new_event)
        #Save results in DB
        print "Found %d coincidences"%(len(result))

        for r in result:
            dec = r[0]
            ra = r[1]
            sigmaR = r[2]
            chi2 = r[3]
            nev = r[4]
            nuEvents = r[5][1:]
            alertTime = []

            for j in nuEvents:
                alertTime.append(j[5])
            total = sum(dt.hour * 3600 + dt.minute * 60 + dt.second for dt in alertTime)
            avg = total / len(alertTime)
            minutes, seconds = divmod(int(avg),60)
            hours,minutes = divmod(minutes,60)

            new_alert = Alert(config.stream,idnum+1,config.rev)
            new_alert.dec = dec
            new_alert.RA = ra
            new_alert.sigmaR = sigmaR
            new_alert.nevents = nev  #Number of neutrinos
            ## Tranform the chi2 value from different degrees of freedom to a just probabilites.
            ## This will make a better comparison between different coincident events
            ddof = nev*2 + 6
            pvalChi2 = stats.chi2.sf(chi2,ddof)
            newchi2 = -np.log10(pvalChi2)
            new_alert.pvalue = pChi2(newchi2)
            new_alert.false_pos = np.power(10,-0.67755675*newchi2 + 5.50359854)#np.power(10,-0.08718512*chi2 + 5.8773)  #parameters from linear fit from archival data.
            new_alert.datetime = datetime(alertTime[0].year,alertTime[0].month,alertTime[0].day,hours,minutes,seconds) #datetime.now() #do an average of the IC neutrinos?
            new_alert.observing = config.stream

            if (prodMachine==True):
                new_alert.type='observation'
            else:
                new_alert.type = 'test'
            alerts.append(new_alert)
            idnum = idnum+1
            # if new alert crosses threshold send email_alerts and GCN
            fname='amon_ic-hawc_%s_%s_%s.xml'%(new_alert.stream, new_alert.id, new_alert.rev)
            filen=os.path.join(AlertDir,fname)
            f1=open(filen, 'w+')

            #Create Alert xml file
            VOAlert = Alert2VOEvent([new_alert],'gamma_nu_coinc','Gamma-Nu multimessenger coincidence')
            someparams = VOAlert.MakeDefaultParams([new_alert])
            VOAlert.WhatVOEvent(someparams)
            VOAlert.MakeWhereWhen([new_alert])
            xmlForm=VOAlert.writeXML()#alert_to_voevent([new_alert])
            f1.write(xmlForm)
            f1.close()

            content = 'Times: '
            print content
            print 'Time of Alert: ',new_alert.datetime
            print '  First IC time: ',alertTime[0]
            print '  Last IC time: ',alertTime[-1]
            print 'HAWC Rise Time: ',new_event.datetime
            #print 'HAWC Set Time: ',datetime(pd.to_datetime(new_event.datetime)) + timedelta(seconds=r[0][4])
            content = 'Alert ID: %d Position RA: %0.2f Dec: %0.2f Ang.Err.: %0.3f, P-value: %0.3e, Chi2: %0.2f, FAR: %0.3e yr^-1, NEvents: %d'%(idnum,ra,dec,
                    sigmaR,new_alert.pvalue,newchi2,new_alert.false_pos,nev)
            print content

            #if chi2 > 65.94: # ~1 per year
            #if chi2 > 53.7: # ~1 per month
            if newchi2 > 4.3:#36.9: # ~1 per day FOR TESTING
            #if chi2 > 11.0: # R TESTING
                title='AMON IC-HAWC alert'
                email_alerts.alert_email_content([new_alert],content,title)

                print "ID: %d"%new_alert.id
                print "Alert Stream: %s"%inv_alert_streams[new_alert.stream]
                #fname.write(alert_to_voevent(new_alert))
                if (prodMachine == True):
                    try:
                        cmd = ['comet-sendvo']
                        cmd.append('--file=' + filen)
                        # just for dev to prevent sending hese both from dev and pro machine
                        #print "uncoment this if used on production"
                        subprocess.check_call(cmd)
                    except subprocess.CalledProcessError as e:
                        print "Send alert failed"
                        logger.error("send_voevent failed")
                        raise e
                    else:
                        shutil.move(filen, os.path.join(AlertDir,"archive/",fname))
                else:
                    shutil.move(filen, os.path.join(AlertDir,"archive/",fname))



        #Write results to the DB
        if len(alerts) > 0:
            db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
    elif new_event.stream == streams['IC-Singlet']:

        result = []#coincAnalysisIC(new_event)
        for res in result:
            for r in res:
                pvalue = r[3]
                dec = r[0]
                ra = r[1]
                sigmaR = r[2]
                chi2 = r[4]
                nev = r[5]
                #line = "p_value: "+str(pvalue)+"; Pos: dec: "+str(dec)+" RA:"+str(ra)+" Error Radius:"+str(sigmaR)+"\n"
                #print line

                new_alert = Alert(config.stream,idnum+1,config.rev)
                new_alert.dec = dec
                new_alert.RA = ra
                new_alert.sigmaR = sigmaR
                new_alert.pvalue = pvalue
                new_alert.datetime = datetime.now()
                new_alert.observing = config.stream
                new_alert.nevents = nev
                new_alert.type = 'test'
                alerts.append(new_alert)
                idnum = idnum+1
                # if new alert crosses threshold send email_alerts
                #if chi2>=60:
                #f=open()
                #f.write(alert_to_voevent(new_alert))

            #Write results to the DB
            if len(alerts) > 0:
                db_write.write_alert(config.stream, HostFancyName, UserFancyName, PasswordFancy, DBFancyName, alerts)
    else:
        print 'Event should not be part of this analysis'



    print "###########"
