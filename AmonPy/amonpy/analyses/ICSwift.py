from amonpy.dbase.db_classes import *
from amonpy.dbase import db_read, db_write
from amonpy.analyses.amon_streams import streams, alert_streams

from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer

import numpy as np
import jsonpickle
from datetime import datetime, timedelta
import pandas as pd

def ic_swift_config():
    """ Returns an ICSwift AlertConfig object
    """
    stream = alert_streams['IC-Swift']
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = alert_streams['IC-Swift']
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
    config.N_thresh       = '{0:1,4:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2020,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config


def ang_sep(ra1,dec1,ra2,dec2):
    ra1 = np.radians(ra1)
    dec1 = np.radians(dec1)
    ra2 = np.radians(ra2)
    dec2 = np.radians(dec2)
    cos_sep = np.sin(dec1)*np.sin(dec2) + np.cos(dec1)*np.cos(dec2)*np.cos(ra1-ra2)
    sep = np.arccos(cos_sep)
    return np.rad2deg(sep)

def prob_den(d, sig):
    p = (1./(2.*np.pi*sig**2)*np.exp((-d**2)/(2*sig**2)))
    return p


class ic_swift_coinc(object):
    def __init__(self, bat_ev, config):
        self.bat_ev = bat_ev
        self.n_evs = 1
        self.ic_evs = []
        self.config = config
        self.t_wind = 2.*self.config.deltaT + self.bat_ev.deltaT
        self.RA = self.bat_ev.RA
        self.dec = self.bat_ev.dec
        self.bat_lh = self.bat_ev.pvalue*self.bat_ev.false_pos*self.t_wind


    def add_ic(self, ic_ev):
        self.ic_evs.append(ic_ev)
        self.n_evs += 1

    @property
    def t_beg(self):
        tbeg = min([ev.datetime for ev in (self.ic_evs + [self.bat_ev])])
        return tbeg

    @property
    def t_end(self):
        tend = max([(ev.datetime + timedelta(seconds=ev.deltaT))\
                            for ev in (self.ic_evs + [self.bat_ev])])
        return tend

    @property
    def llh(self):
        # 1 ic_event
        if self.n_evs == 2:
            asep = ang_sep(self.bat_ev.RA, self.bat_ev.dec, self.ic_evs[0].RA, self.ic_evs[0].dec)
            pden = prob_den(asep, self.ic_evs[0].sigmaR)*3282.811  # to (sr^-1)
            return np.log(pden/self.bat_lh)
        elif self.n_evs > 2:
            return 100.
        else:
            print "add events"
            return None



@app.task(ignore_result=True)
def ic_swift(new_event=None):

    config=ic_swift_config()
    max_id = db_read.alert_max_id(alert_streams['IC-Swift'],HostFancyName,
                                       UserFancyName,
                                       PasswordFancy,
                                       DBFancyName)
    if max_id is None:
        idnum = 0
    else:
        idnum = max_id
    print idnum

    new_event = jsonpickle.decode(new_event)

    coincs= []
    if new_event is None:
        # should probably have new_event
        return coincs


    if type(new_event) is list:
        new_event = new_event[0]
    new_event.datetime = pd.to_datetime(new_event.datetime)


    coinc_found = False

    print new_event.stream

    if new_event.stream == streams['IC-Singlet']:
        # IC
        # find BAT events
        t_wind_beg = new_event.datetime - timedelta(seconds=config.deltaT)
        #t_wind_end = new_event.datetime + timedelta(seconds=config.deltaT)
        max_ang = config.cluster_thresh*new_event.sigmaR

        eventList = db_read.read_event_timeslice_streams([streams['SWIFT']],t_wind_beg,2*conifg.deltaT,
                                 HostFancyName,UserFancyName,
                                 PasswordFancy,DBFancyName)

        for ev in eventList:
            if type(ev) is list:
                ev = ev[0]
            angsep = ang_sep(new_event.RA, new_event.dec, ev.RA, ev.dec)
            print "angsep: ", angsep
            if angsep <= max_ang:
                coinc = ic_swift_coinc(ev, config)
                coinc.add_ic(new_event)
                coincs.append(coinc)

        # if there were coincs check for other IC events coincident with that BAT event
        if len(coincs) > 0:
            coinc_found = True
            for coinc in coincs:
                t_wind_beg = coinc.t_beg
                t_wind_end = coinc.t_beg + timedelta(seconds=coinc.t_wind)
                for ev in eventList:
                    if type(ev) is list:
                        ev = ev[0]
                    if ev.id not in [ic_ev.id for ic_ev in coinc.ic_evs]:
                        if ev.datetime >= t_wind_beg and ev.datetime <= t_wind_end:
                            angsep = ang_sep(coinc.RA, coinc.dec, ev.RA, ev.dec)
                            if angsep <= config.cluster_thresh*ev.sigmaR:
                                coinc.add_ic(ev)


    elif new_event.stream == streams['SWIFT']:
        # BAT
        # find IC events
        t_beg = new_event.datetime
        t_end = new_event.datetime + timedelta(seconds=new_event.deltaT)
        t_wind_beg = t_beg - timedelta(seconds=config.deltaT)
        t_wind_end = t_end + timedelta(seconds=config.deltaT)
        coinc = ic_swift_coinc(new_event, config)
        eventList = db_read.read_event_timeslice_streams([streams['IC-Singlet']],t_wind_beg,2*conifg.deltaT,
                                 HostFancyName,UserFancyName,
                                 PasswordFancy,DBFancyName)
        for ev in eventList:
            if type(ev) is list:
                ev = ev[0]
            ev.datetime = pd.to_datetime(ev.datetime)
            if ev.datetime >= t_wind_beg and ev.datetime <= t_wind_end:
                angsep = ang_sep(new_event.RA, new_event.dec, ev.RA, ev.dec)
                if angsep <= config.cluster_thresh*ev.sigmaR:
                    coinc.add_ic(ev)
                    coinc_found = True
        coincs.append(coinc)

    else:
        print "bad stream num"


    if coinc_found:
        n_coincs = len(coincs)
        print "Found %d coincidences" %(n_coincs)

        for coinc in coincs:
            print "IC-Swift coincidence found"
            print "with %d IC-singlet(s)," %(coinc.n_evs-1)
            print "LLH value of %.3f" %(coinc.llh)

            # make an Alert class object
            # then use it to write to the Alert Table in the DB



    return coincs
