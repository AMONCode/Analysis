from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.dbase.alert_to_voevent import alert_to_voevent
import amonpy.dbase.email_alerts as email_alerts
from amonpy.analyses.amon_streams import streams, alert_streams, inv_alert_streams
from amonpy.analyses.IC_PSF import *

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

from astropy.coordinates import SkyCoord
from astropy.time import Time

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import netrc, jsonpickle, os
from amonpy.tools.config import AMON_CONFIG

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

### Functions for the coincidence analysis
# HAWC PDF for spatial null and alternative hypotheses
hwcBkgfile = os.path.join(AmonPyDir,'analyses/hawc_bkg_intp.npy')
hwcBkg = np.load(hwcBkgfile).item()
def probBkgHAWC(dec):
    #zenith = 50.
    #A = 0.5 * (special.erf(zenith/(np.sqrt(2)*23.55)) - special.erf(-zenith/(np.sqrt(2)*23.55)))
    #The 2 pi is from the uniform distribution in RA
    #return A*exp(-(dec-18.98)**2/(2*23.55**2))/(sqrt(2*np.pi*np.deg2rad(23.55)**2) * 2*np.pi)
    if dec<-25.: return 0.00619
    if dec>64: return 0.00619
    return hwcBkg(dec)*180./(np.pi*2*np.pi)

def probSigHAWC(spc,sigma):
    #psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(np.sqrt(2*np.pi)*(np.deg2rad(sigma)))
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*(np.deg2rad(sigma)**2))
    return psf


##IC PDFs for spatial null hypotheses
## The alternative  is given by an interpolator for each event.
def probBkgIC(sinDec):
    x=sinDec
    #numbers obtained from archival data after doing a fit
    a=1.035595
    x0=-0.117645
    g1 = 0.81984
    g2 = 1.655227
    y = a*(1/np.pi) * ((g1/2)/((x-x0)**2 + (g1**2/4))) * ((x-x0)<0)
    y+= (a*g2/g1)*((1/np.pi) * ((g2/2)/((x-x0)**2 + (g2**2/4))) ) * ((x-x0)>=0)
    return y*np.pi/(180.*360.)# units of deg^2, SigPSF is given in deg^2 #/(2*np.pi)

def probSigIC(sigR,muR,lamR):
    if lamR==-1:
        psf = log_norm_func2(sigR,muR)
    else:
        psf = comb_psfs2(sigR,muR,lamR,nlog_steps=50)
    return psf #in deg^2

def probSigIC2(spc,sigma):
    #psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(np.sqrt(2*np.pi)*(np.deg2rad(sigma)))
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*sigma**2)
    return psf #in deg^2

# Probability of more than 2 neutrino given that we see one neutrino
def pNuCluster(events):
    val=1
    N=len(events)-1
    if N==1:
        return val
    else:
        lmb = 0.0066887 * events[0][4]*3600.*2*np.pi*(1-np.cos(np.deg2rad(3.5)))/(4*np.pi) #Rate=0.0066887 = 22334./ 3339043.sec
        for i in range(0,N-1) :
            val = val - np.exp(-lmb)*(lmb)**i/np.math.factorial(i)
    return val

# Calculation of the p_value of the spatial llh. Trying to avoid several calls to CDF_LLH.npz
filename = os.path.join(AmonPyDir,'analyses/newCDF_LLH_200yr.npz')
cdfLLH =  np.load(filename) #How to store it in amonpy?
#cdfLLH =  np.load('/storage/home/hza53/Software/Analysis/AmonPy/amonpy/analyses/CDF_LLH_100yr.npz')
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
# cdf_saf=[]
# data_saf = np.load('/Users/hugo/Software/Analysis/AmonPy/amonpy/analyses/CDF_SAF.npz')
# #data_saf = np.load('/storage/home/hza53/Software/Analysis/AmonPy/amonpy/analyses/CDF_SAF.npz')
# for item in data_saf.iteritems():
#     cdf_saf.append(item[1])
# n_saf = cdf_saf[0]
# b_saf = cdf_saf[1]
# b_saf_centers = b_saf[:-1] + 0.5*(b_saf[1:] - b_saf[:-1])
# f_saf = interp1d(b_saf_centers,n_saf)
# def pHEN(SAF):
#     x=np.log10(SAF)
#     if x < b_saf_centers[0]:
#         y=1.
#         print "Neutrino: WARNING x below range"
#     elif x> b_saf_centers[-1]:
#         y=1.-f_saf(b_saf_centers[-2])
#         print "Neutrino: WARNING x above range"
#     else:
#         y=1.-f_saf(x)
#     if y<0:
#         print y
#     return y
filename = os.path.join(AmonPyDir,'analyses/log10fprd_up_trunc_intp_bwp05_xf5_yf1.npy')
Rup = np.load(filename).item()
filename = os.path.join(AmonPyDir,'analyses/log10fprd_down_intp_bwp01.npy')
Rdn = np.load(filename).item()
def pHEN(sinDec,fprd):
    costh=-1*sinDec #IC's zenith is close to -90deg declination
    if costh>0.139:
        R = np.power(10,Rdn(sinDec,0.0))
    elif costh<=0.139:
        R = np.power(10,Rup(sinDec,2.0))
    if fprd==0: return 1.0
    if fprd/R > 1.0: return 1.0
    else: return fprd/R

def totalpHEN(events):
    val=1
    N=len(events)
    if N==2:
        return val
    else:
        for i in range(1,N):
            val*=ev[i][-1]
        return val

#Calculating the p_value of the analysis. Trying to avoid several calls to CDF_CHI2.npz
filename = os.path.join(AmonPyDir,'analyses/newCDF_Chi2_200.npz')
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

#Angular separation of two angles in the sphere
def spcang(ra1,ra2,dec1,dec2):
    dec1 = np.deg2rad(dec1)
    dec2 = np.deg2rad(dec2)
    DeltaRA = np.deg2rad(ra1-ra2)
    sep = np.arccos(np.cos(dec1)*np.cos(dec2)*np.cos(DeltaRA) + np.sin(dec1)*np.sin(dec2))
    return np.rad2deg(sep)

# Define an initial space log-likelihood for each event (dec and ra are coordinates of the source position)
#def loglh(dec1,ra1,dec,ra,sigma1,bkgterm):
def loglh(sigterm,bkgterm):
    return np.log(sigterm)-np.log(bkgterm)

# Find total log-likelihood considering multiplets: spatial and temporal terms
def tloglh_time(dec,ra,events):
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
            solution = sc.optimize.minimize(lambda x: -tloglh_time(x[0],x[1],ev),np.array([ev[0][1]+0.1,ev[0][2]+0.1]), method = 'SLSQP')
        except ValueError:
            try:
                solution = sc.optimize.minimize(lambda x: -tloglh_time(x[0],x[1],ev),np.array([ev[0][1]+0.1,ev[0][2]+0.1]), method = 'BFGS')
            except ValueError:
                print "Error in minimization"
                return coincs
        res = list(solution.x)
        stderr = 0.
        pcluster=pNuCluster(ev)
        phwc = ev[0][-1]

        if solution.success:
            for part in ev:
                #print part[0],part[1],part[2],solution.x[0],solution.x[1]

                stderr += 1./(part[3]**2)

            stderr = np.sqrt(1/stderr)
            #print stderr
            print "Number of neutrinos: %d"%(len(ev)-1)
            pspace = pSpace(-1*solution.fun)
            chi2 = -2 * np.log(pspace * phwc * pcluster) #The main quantity
            pchi2 = pChi2(chi2) #The p-value of the chi2 distribution

            coincs.append([solution.x[0],solution.x[1],stderr,pchi2,chi2,len(ev),ev])#,pcluster,hwcsigma,ev])
    return coincs

def coincAnalysisHWC(new_event):

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
            datalist.append([streams['IC-Singlet'],dec2,ra2,poserr2,psfIC,pd.to_datetime(e.datetime), probBkgIC(np.sin(np.deg2rad(dec2))),pHEN(np.sin(np.deg2rad(dec2)),fprd)])

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

        #[solution.x[0],solution.x[1],stderr,-1*solution.fun,len(ev)-1,ev])
        for r in result:
            pvalue = r[3]
            dec = r[0]
            ra = r[1]
            sigmaR = r[2]
            chi2 = r[4]
            nev = r[5]
            #print line
            nuEvents = r[6][1:]
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
            new_alert.pvalue = pvalue
            new_alert.false_pos = np.power(10,-0.08718512*chi2 + 5.8773)  #parameters from linear fit from archival data.
            new_alert.datetime = datetime(alertTime[0].year,alertTime[0].month,alertTime[0].day,hours,minutes,seconds) #datetime.now() #do an average of the IC neutrinos?
            new_alert.observing = config.stream
            new_alert.nevents = nev  #Number of neutrinos
            new_alert.type = 'test'
            alerts.append(new_alert)
            idnum = idnum+1
            # if new alert crosses threshold send email_alerts and GCN
            fname='amon_ic-hawc_%s_%s_%s.xml'%(new_alert.stream, new_alert.id, new_alert.rev)
            filen=os.path.join(AlertDir,fname)
            f1=open(filen, 'w+')
            xmlForm=alert_to_voevent([new_alert])
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
                    sigmaR,pvalue,chi2,new_alert.false_pos,nev)
            print content

            #if chi2 > 65.94: # ~1 per year
            #if chi2 > 53.7: # ~1 per month
            if chi2 > 36.9: # ~1 per day FOR TESTING
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
