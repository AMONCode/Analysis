"""
Functions to post alerts on OpenAMON app for outreach and trigger a notification or on AMONalerts for physicists.
"""
from math import cos, pi, degrees, radians
from amonpy.monitoring.monitor_funcs import send_email
from amonpy.analyses.amon_streams import streams
import pandas as pd
from datetime import datetime

def post_on_OpenAMON(post, particle):

    site_email = ["kaya338hene@post.wordpress.com"] # email linked to the psu wordpress website OpenAMON
    notif_email = ["tmg5746@gmail.com"] # email used to trigger app notifications
    me = "amon.psu@gmail.com"
    pwd = "amonpassword"
    object_post = "%s alert!"  % (particle)
    object_notif_trig = "%s_alert" % (particle)# ! Do not change that without changing the Zapier settings
    
    send_email(site_email,me,pwd,object_post,post) # Sends the post
    send_email(notif_email,me,pwd,object_notif_trig,"") # Sends a notification (arrives within 5 min)


def post_on_AMONalerts(post, post_title):
    
    site_email = ["gefi453buqe@post.wordpress.com"] # email linked to the psu wordpress website AMONalerts
    me = "amon.psu@gmail.com"
    pwd = "amonpassword"
    object_post = post_title
    
    send_email(site_email,me,pwd,object_post,post) # Sends the post


def ICgoldbronze_to_OpenAMON(event, params):

    for i in range(len(params)):
        #if (params[i].name== 'qtot'):
        if (params[i].name== 'event_id'):
            event_id=int(params[i].value)
        if (params[i].name== 'run_id'):
            run_id=int(params[i].value)
        if (params[i].name== 'signalness'):
            signalness=params[i].value
        if (params[i].name== 'energy'):
            energy=params[i].value # GeV
        if (params[i].name== 'src_error'):
            src_error_50=params[i].value # GeV
        if (params[i].name== 'src_error90'):
            src_error_90=params[i].value # GeV
        if (params[i].name== 'far'):
            far=params[i].value

    datenow=datetime.utcnow()

    # TODO add an image?
    # TODO add the stellarium thing # <a href="https://stellarium-web.org/skysource/Vega?fov=120.00&amp;date=2019-06-15T01:30:13Z&amp;lat=39.86&amp;lng=-74.17&amp;elev=0">in the direction of Vega</a>[1. This is a broad direction, see the complete set of information for a precise one]!"
    # TODO change "degree" into real degree sign (make it python 2 and 3 compatible)
    # TODO change the 1.0e+3 to correct (utf8) notation with multiplication sign and power of ten.

    ############ Post template ############################
    moon_solid_angle=6.67e-5 # steradians
    src_error_90_solid_angle=(1.-cos(radians(src_error_90)))*2.*pi # steradians
    src_error_50_solid_angle=(1.-cos(radians(src_error_50)))*2.*pi # steradians

    
    post="""## An intriguing event has just been detected by the IceCube neutrino telescope!

This event has a %.1f%% chance to be a neutrino of astrophysical origin. The background noise fluctuation should produce a similar event every %d days in average.

Its energy is estimated to be around %d TeV [1. %d times the average energy released in nuclear fission of one Uranium-235 atom] and its source has a 90%% probability to be located within a zone of %.2f square deg [2. %d times smaller than the moon angular coverage].

Is it the result of a blazar, a supernovae...? This alert has been sent to astronomers around the world so they can point their telescopes toward the source of this event. An other signal from a different messenger could allow to understand the mechanisms involved.

### Complete set of information:
This event has been detected on %s UTC (Coordinated Universal Time).
The algorithm estimates its source location to be around the following coordinates: right ascension = %.4f degrees, declination = %.4f degrees with a 90%% probability to be within a disk of radius %.1f arcmin and a 50%% probability to be within a disk of %.1f arcmin radius.
The uncertainty in the location of the event is based on statistical uncertainty only, not accounting for the systematic error which should be smaller.
The estimated energy is %.5e TeV.
The background noise should produce an event at least as significant %.2f times per year which leads to a probability of %.2f%% that this event is a track-like neutrino of astrophysical origin.
[category alert]""" % (signalness*100., (1./far)*365.25, energy/1000., energy/0.2, src_error_90_solid_angle*(180./pi)**2,
src_error_90_solid_angle/moon_solid_angle, str(event.datetime), float(event.RA), float(event.dec), degrees(src_error_90)*60.,
degrees(src_error_50)*60., energy/1000., far, signalness*100.)

    post_on_OpenAMON(post, "Neutrino")


def ICgoldbronze_to_AMONalerts(event, params):
    """
    Write the post of an IC gold/bronze alert and send it to the AMONalerts website (https://sites.psu.edu/amonalerts/) 
    """

    for i in range(len(params)):
        #if (params[i].name== 'qtot'):
        if (params[i].name== 'event_id'):
            event_id=int(params[i].value)
        if (params[i].name== 'run_id'):
            run_id=int(params[i].value)
        if (params[i].name== 'signalness'):
            signalness=params[i].value
        if (params[i].name== 'energy'):
            energy=params[i].value # GeV
        if (params[i].name== 'src_error'):
            src_error_50=params[i].value # GeV
        if (params[i].name== 'src_error90'):
            src_error_90=params[i].value # GeV
        if (params[i].name== 'far'):
            far=params[i].value
    
    if event.stream == streams['IC-Gold']:
        notice_type = 'IceCube Gold'
    elif event.stream == streams['IC-Bronze']:
        notice_type = 'IceCube Bronze'
    
    event_datetime=str(pd.to_datetime(event.datetime))
    tag=event_datetime[2:4]+event_datetime[5:7]+event_datetime[8:10]

    post = """
NOTICE_TYPE: %s
EVENT_TIME: %s
STREAM: %s
RUN_NUM: %s
EVENT_NUM: %s
SRC_RA: %0.4f [deg]
SRC_DEC: %0.4f [deg]
SRC_ERROR_90: %0.2f [arcmin radius, stat-only, 90%% containment]
SRC_ERROR_50: %0.2f [arcmin radius, stat-only, 50%% containment]
REVISION: %s
ENERGY:  %.4e [TeV]
SIGNALNESS: %.4f [dn]
FAR: %.4f [yr^-1]
COMMENTS: %s event.
COMMENTS: The position error is statistical only, there is no systematic added.
[category %s]
[tags IceCube-%s]""" % (notice_type, event_datetime, str(event.stream), str(run_id),
    str(event_id), event.RA, event.dec, src_error_90, src_error_50, str(event.rev), energy/1000.,
    signalness, far, notice_type, notice_type, tag)

    post_title = "%s alert %s" % (notice_type, tag)

    post_on_AMONalerts(post, post_title)


def HAWCGRB_to_AMONalerts(event):
    """
    Write the post of an HAWC Burst Monitor alert and send it to the AMONalerts website (https://sites.psu.edu/amonalerts/) 
    """

    run_id = str(event.id)[:-8]
    event_id = str(event.id)[-4:]
    tag=str(event.datetime)[2:4]+str(event.datetime)[5:7]+str(event.datetime)[8:10]

    post = """ 
NOTICE_TYPE: %s 
EVENT_TIME: %s 
STREAM: %s 
RUN_NUM: %s 
EVENT_NUM: %s 
SRC_RA: %0.4f [deg] 
SRC_DEC: %0.4f [deg] 
SRC_ERROR: %0.2f [arcmin radius, stat+sys, 90%% containment]
REVISION: %s 
FAR: %0.3e [yr^-1] 
Pvalue: %0.3e [0.0 - 1.0] 
delta_T: %s [sec] 
COMMENTS: HAWC burst monitor event.
[category HAWC Burst Monitor]
[tags HAWC-%s]""" % ("HAWC Burst Monitor", str(event.datetime), str(event.stream), str(run_id), str(event_id),
    event.RA, event.dec, event.sigmaR, str(event.rev), event.false_pos, event.pvalue, str(event.deltaT), tag) 
     
    post_title = "HAWC Burst Monitor alert %s" % (tag)

    post_on_AMONalerts(post, post_title)
