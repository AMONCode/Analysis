"""
alert_to_VOEvent: Sample program for use with VOEvent library.
Builds a simple VOEvent packet from alert
See the VOEvent specification for details
http://www.ivoa.net/Documents/latest/VOEvent.html
"""
import sys
import random
from VOEventLib.VOEvent import *
from VOEventLib.Vutil import *

from amonpy.dbase.db_classes import *
from amonpy.analyses.amon_streams import streams



def ICgoldbronze_to_voevent(alert, params):
    stream=alert[0].stream #Need to check if GCN will be the same
    amon_id = alert[0].id
    rev=alert[0].rev

    retraction = False
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
        if (params[i].name== 'retraction'):
            retraction_rev = int(params[i].value)
            retraction = True

    datenow=datetime.utcnow()
    ############ VOEvent header ############################

    v = VOEvent.VOEvent(version="2.0")
    if stream==streams['IC-Gold']:
        v.set_ivorn("ivo://amon/icecube_gold#%s" % str(stream)+'_'+str(run_id)+'_'+str(event_id)+'_'+ str(rev))
        v.set_Description("Report of IceCube Gold neutrino event.")
        if retraction:
            v.set_Citations(VOEvent.EventIVORN('retraction', "ivo://amon/icecube_gold#%s" % str(stream)+'_'+str(run_id)+'_'+str(event_id)+'_'+ str(retraction_rev)))
    elif stream==streams['IC-Bronze']:
        v.set_ivorn("ivo://amon/icecube_bronze#%s" % str(stream)+'_'+str(run_id)+'_'+str(event_id)+'_'+ str(rev))
        v.set_Description("Report of IceCube Bronze neutrino event.")
        if retraction:
            v.set_Citations(VOEvent.EventIVORN('retraction', "ivo://amon/icecube_bronze#%s" % str(stream)+'_'+str(run_id)+'_'+str(event_id)+'_'+ str(retraction_rev)))
    v.set_role("%s" % alert[0].type)

    w = Who()
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+"T"+datenow1[11:]
    w.set_Date(str(datenow2))
    a = Author()
    a.add_contactName("Icecube Realtime Committee")
    a.add_contactEmail('roc@icecube.wisc.edu')
    w.set_Author(a)
    v.set_Who(w)

    ############ What ############################
    w = What()

    # params related to the event. None are in Groups.
    p = Param(name="stream", ucd="meta.number", dataType="int", value=str(stream))
    if stream==streams['IC-Gold']:
        p.set_Description(["IceCube Gold stream identification"])
    elif stream==streams['IC-Bronze']:
        p.set_Description(["IceCube Bronze stream identification"])
    w.add_Param(p)

    p = Param(name="amon_id", ucd="meta.number",dataType="string", value=str(amon_id))
    p.set_Description(["Alert identification number"])
    w.add_Param(p)

    p = Param(name="rev", ucd="meta.number",dataType="int", value=str(rev))
    p.set_Description(["Alert revision"])
    w.add_Param(p)

    p = Param(name="event_id", ucd="meta.number",dataType="int", value=str(event_id))
    p.set_Description(["Event id within a given run"])
    w.add_Param(p)

    p = Param(name="run_id", ucd="meta.number",dataType="int", value=str(run_id))
    p.set_Description(["Run id"])
    w.add_Param(p)

    p = Param(name="signalness", ucd="stat.probability", unit="", dataType="float",  value=str(signalness))
    p.set_Description(["Probability of a neutrino event being astrophysical in origin."])
    w.add_Param(p)

    p = Param(name="far", ucd="stat.probability", unit="yr^-1", dataType="float",  value=str(far))
    p.set_Description(["False alarm rate, a value of zero means not available"])
    w.add_Param(p)

    p = Param(name="energy", ucd="phys.energy", unit="TeV", dataType="float",  value=str(energy/1000.))
    p.set_Description(["Likely neutrino energy (in TeV)."])
    w.add_Param(p)

    p = Param(name="src_error_90", ucd="stat.error.sys", unit="deg", dataType="float",  value=str(src_error_90))
    p.set_Description(["Angular error of the source (90% containment)"])
    w.add_Param(p)

    v.set_What(w)

    ############ Wherewhen ############################
    wwd = {'observatory':     'IceCube',
           'coord_system':    'UTC-GEOD-TOPO',
           'time':            alert[0].datetime,
           'timeError':       0.000001,
           'longitude':       alert[0].RA,
           'latitude':        alert[0].dec,
           'positionalError': alert[0].sigmaR,
    }

    ww = makeWhereWhen(wwd)
    if ww: v.set_WhereWhen(ww)

    if ww: v.set_WhereWhen(ww)
    obs=ObsDataLocation()
    obsloc=ObservatoryLocation()
    astro2=AstroCoordSystem("UTC-GEOD-TOPO")
    astro3=AstroCoords("UTC-GEOD-TOPO")
    obsloc.set_AstroCoordSystem(astro2)
    obsloc.set_AstroCoords(astro3)
    obs.set_ObservatoryLocation(obsloc)
    observation=ObservationLocation()
    astro4=AstroCoordSystem("UTC-ICRS-TOPO")
    astro5=AstroCoords("UTC-ICRS-TOPO")
    time2=alert[0].datetime
    if (alert[0].type=="test"):
        value2=Value2(random.uniform(0.00,359.99),random.uniform(0.00,-90.00))
    else:
        value2=Value2(alert[0].RA,alert[0].dec)
    pos2=Position2D("deg-deg", "RA","Dec",value2, src_error_50)
    astro5.set_Position2D(pos2)


    time_1=Time("s")
    time2=str(alert[0].datetime)
    time2_2=time2[0:10]+"T"+time2[11:]

    time3=TimeInstant(time2_2)
    time_1.set_TimeInstant(time3)
    astro5.set_Time(time_1)

    observation.set_AstroCoordSystem(astro4)
    observation.set_AstroCoords(astro5)
    obs.set_ObservationLocation(observation)
    ww.set_ObsDataLocation(obs)

    v.set_WhereWhen(ww)


    ############ output the event ############################

    xml = stringVOEvent(v,schemaURL = "http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd")
    #print xml
    return xml
