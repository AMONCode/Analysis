"""
alert_to_VOEvent: Sample program for use with VOEvent library.
Builds a simple VOEvent packet from alert
See the VOEvent specification for details
http://www.ivoa.net/Documents/latest/VOEvent.html
"""
from __future__ import print_function
from builtins import str
from builtins import range
import sys
import random

from amonpy.dbase.db_classes import *

from VOEventLib.VOEvent import *
from VOEventLib.Vutil import *

def ofualert_to_voevent(alert, params):
    alert_stream=0
    amon_id = alert[0].id
    rev=alert[0].rev
    substream = alert[0].stream

    for i in range(len(params)):
        if (params[i].name== 'src_error'):
            src_error_50=params[i].value
        if (params[i].name== 'src_error90'):
            src_error_90=params[i].value

    datenow=datetime.utcnow()
    ############ VOEvent header ############################

    v = VOEvent.VOEvent(version="2.0")
    #v.set_ivorn("ivo://amon/icecube_hese#%s" % str(stream)+'_'+str(id)+'_' + str(rev))
    if (substream==12):
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev))
    elif (substream==13):
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+1))
    elif (substream==14):
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+2))
    elif (substream==15):
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+3))
    else:
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev))
    v.set_role("%s" % alert[0].type)
    if (alert[0].type=='observation'):
        v.set_Description("Report of IceCube coincidence neutrino alert")
    else:
        v.set_Description("Report of IceCube coincidence test alert")

    w = Who()
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+"T"+datenow1[11:]
    w.set_Date(str(datenow2))
    a = Author()
    a.add_contactName("James DeLaunay, Hugo Ayala")
    a.add_contactEmail('jjd330@psu.edu,hgayala@psu.edu')
    w.set_Author(a)
    v.set_Who(w)

    ############ What ############################
    w = What()

    # params related to the event. None are in Groups.
    p = Param(name="stream", ucd="meta.number", dataType="int", value=str(alert_stream))
    p.set_Description(["IceCube coincidence stream identification"])
    w.add_Param(p)

    p = Param(name="substream", ucd="meta.number", dataType="int", value=str(substream))
    p.set_Description(["IceCube coincidence recipient substream identification"])
    w.add_Param(p)

    p = Param(name="amon_id", ucd="meta.number",dataType="int", value=str(amon_id))
    p.set_Description(["Alert identification, combination of run_id and event_id"])
    w.add_Param(p)
    """
    p = Param(name="event_id", ucd="meta.number",dataType="int", value=str(event_id))
    p.set_Description(["Event id within a given run"])
    w.add_Param(p)

    p = Param(name="run_id", ucd="meta.number",dataType="int", value=str(run_id))
    p.set_Description(["Run id"])
    w.add_Param(p)
    """
    p = Param(name="rev", ucd="meta.number",dataType="int", value=str(rev))
    p.set_Description(["Alert revision"])
    w.add_Param(p)

    p = Param(name="nevents", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].nevents))
    #p = Param(name="nevents", ucd="meta.number", unit=" ", dataType="int",  value=str(1))
    p.set_Description(["Number of events in the alert"])
    w.add_Param(p)

    p = Param(name="deltaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].deltaT))
    p.set_Description(["Time window of the burst"])
    w.add_Param(p)

    p = Param(name="sigmaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].sigmaT))
    p.set_Description(["Uncertainty of the time window"])
    w.add_Param(p)
    """
    if ((signal_trackness>=0.1) and (charge>=6000.)):
        p = Param(name="charge", ucd="phys.charge", unit="pe", dataType="float",  value=str(charge))
    else:
        p = Param(name="charge", ucd="phys.charge", unit="pe", dataType="float",  value=str(1510))
    p.set_Description(["Total neutrino event charge in units of photoelectrons (pe)"])
    w.add_Param(p)

    if ((signal_trackness>=0.1) and (charge>=6000.)):
        p = Param(name="signal_trackness", ucd="stat.probability", unit=" ", dataType="float",  value=str(signal_trackness))
    else:
        p = Param(name="signal_trackness", ucd="stat.probability", unit=" ", dataType="float",  value=str(0.01))
    p.set_Description(["Probability of an astrophysical neutrino event being a track-like event. If >=0.1, a given event is a signal track-like event, if <0.1 event could be either track-like or shower-like."])
    w.add_Param(p)
    """
    #p = Param(name="hesetype", ucd="", unit=" ", dataType="string",  value=str(hesetype))
    #p = Param(name="hesetype", ucd="", unit=" ", dataType="string",  value=str(0))
    #p.set_Description(["Track-like or cascade-like HESE neutrino"])
    #w.add_Param(p)
    """
    if ((signal_trackness>=0.1) and (charge>=6000.)):
        p = Param(name="src_error_90", ucd="stat.error.sys", unit="deg", dataType="float",  value=str(src_error_90))
    else:
        p = Param(name="src_error_90", ucd="stat.error.sys", unit="deg", dataType="float",  value=str(5.))
    p.set_Description(["Angular error of the source (90% containment)"])
    w.add_Param(p)
    """
    #p = Param(name="false_pos", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].false_pos))
    p = Param(name="src_error_90", ucd="stat.error.sys", unit="deg", dataType="float",  value=str(src_error_90))
    p.set_Description(["Angular error of the source (90% containment)"])
    w.add_Param(p)

    p = Param(name="false_pos", ucd="stat.probability", unit=" ", dataType="float",  value=str(0))
    p.set_Description(["False positive rate, a value of zero means not available"])
    w.add_Param(p)

    #p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
    p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(0))
    p.set_Description(["Pvalue for the alert, a value of zero means not available"])
    w.add_Param(p)

    p = Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(0))
    #p = Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].observing))
    p.set_Description(["Observatories observing given part og the sky: 0 means IceCube"])
    w.add_Param(p)

    p = Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(1))
    #p = Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].trigger))
    p.set_Description(["Observatories triggering: 1 means IceCube triggered"])
    w.add_Param(p)

    #p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
    #p.set_Description(["Pvalue for the alert"])
    #w.add_Param(p)

    #p = Param(name="skymap", ucd="meta.code.multip", unit=" ", dataType="string",  value="False")
    #p = Param(name="skymap", ucd="meta.code.multip", unit=" ", dataType="string",  value=str(alert[0].skymap))
    #p.set_Description(["Skymap or no skymap assotiated with the alert"])
    #w.add_Param(p)

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
    #obsloc=v.ObsDataLocation().get_ObservatoryLocation()
    # v.get_WhereWhen().get_ObsDataLocation().get_ObservatoryLocation().set_ObservatoryLocation("UTC-GEOD-TOPO")
    obs=ObsDataLocation()
    obsloc=ObservatoryLocation()
    astro2=AstroCoordSystem("UTC-GEOD-TOPO")
    astro3=AstroCoords("UTC-GEOD-TOPO")
    #value3=Value3(0.0000,-90.00,0)
    #pos1=Position3D("deg-deg-m","longitude", "latitude", "elevation",value3)
    #astro3.set_Position3D(pos1)
    obsloc.set_AstroCoordSystem(astro2)
    obsloc.set_AstroCoords(astro3)
    obs.set_ObservatoryLocation(obsloc)
    observation=ObservationLocation()
    astro4=AstroCoordSystem("UTC-ICRS-TOPO")
    astro5=AstroCoords("UTC-ICRS-TOPO")
    time2=alert[0].datetime
    #value2=Value2(alert[0].RA,alert[0].dec)
    #value2=Value2(alert[0].RA,-5.00)

    value2=Value2(alert[0].RA,alert[0].dec)
    #pos2=Position2D("deg-deg", "RA","Dec",value2, alert[0].sigmaR)
    pos2=Position2D("deg-deg", "RA","Dec",value2, src_error_50)
    astro5.set_Position2D(pos2)
    #error2=Error2Radius(alert[0].sigmaR)
    #astro5.set_Error2Radius()


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
    #ww.add_TimeInstant(time3)
    v.set_WhereWhen(ww)


    ############ output the event ############################

    xml = stringVOEvent(v,
    schemaURL = "http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd")
    #print xml
    return xml

if __name__ == "__main__":
    alert=[Alert(1,0,0)]
    xml1=alert_to_voevent(alert)
    print(xml1)
    f1=open('./test_alert.xml', 'w+')
    f1.write(xml1)
