"""
alert_to_VOEvent: Sample program for use with VOEvent library.
Builds a simple VOEvent packet from alert
See the VOEvent specification for details
http://www.ivoa.net/Documents/latest/VOEvent.html
"""
import sys
import random

from amonpy.dbase.db_classes import *

from VOEventLib.VOEvent import *
from VOEventLib.Vutil import *

def gfualert_to_voevent(alert, params):
    alert_stream=0
    amon_id = alert[0].id
    rev=alert[0].rev
    substream = alert[0].stream

    for i in range(len(params)):
        if (params[i].name== 'src_name'):
            src_name=params[i].value
        if (params[i].name== 'src_error90'):
            src_error_90=params[i].value
        if (params[i].name== 'src_error'):
            src_error_50=params[i].value

    datenow=datetime.utcnow()

    ############ VOEvent header ############################

    v = VOEvent.VOEvent(version="2.0")
    if (substream==16):
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev))
    elif (substream==17):
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+1))
    elif (substream==18):
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+2))
    elif (substream==19):
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+3))
    elif (substream==20):
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev+4))
    else:
        v.set_ivorn("ivo://amon/icecube_source_flare#%s" % str(alert_stream)+'_'+str(amon_id)+'_' + str(rev))
    v.set_role("%s" % alert[0].type)

    if (alert[0].type=='observation'):
        v.set_Description("Report of IceCube source flare neutrino alert")
    else:
        v.set_Description("Report of IceCube source flare test alert")

    w = Who()
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+"T"+datenow1[11:]
    w.set_Date(str(datenow2))
    a = Author()
    a.add_contactName("Azadeh Keivani, Hugo Ayala, Jimmy DeLaunay")
    a.add_contactEmail('keivani@psu.edu, hza53@psu.edu, jjd330@psu.edu')
    w.set_Author(a)
    v.set_Who(w)

    ############ What ############################
    w = What()

    # params related to the event. None are in Groups.
    p = Param(name="stream", ucd="meta.number", dataType="int", value=str(alert_stream))
    p.set_Description(["IceCube source flare stream identification"])
    w.add_Param(p)

    p = Param(name="substream", ucd="meta.number", dataType="int", value=str(substream))
    p.set_Description(["IceCube source flare recipient substream identification"])
    w.add_Param(p)

    p = Param(name="amon_id", ucd="meta.number",dataType="int", value=str(amon_id))
    p.set_Description(["Alert identification, combination of run_id and event_id"])
    w.add_Param(p)

    p = Param(name="rev", ucd="meta.number",dataType="int", value=str(rev))
    p.set_Description(["Alert revision"])
    w.add_Param(p)

    p = Param(name="nevents", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].nevents))
    p.set_Description(["Number of events in the alert"])
    w.add_Param(p)

    p = Param(name="deltaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].deltaT))
    p.set_Description(["Time window of the burst"])
    w.add_Param(p)

    p = Param(name="sigmaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].sigmaT))
    p.set_Description(["Uncertainty of the time window"])
    w.add_Param(p)

    p = Param(name="false_pos", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].false_pos))
    p.set_Description(["False positive rate, a value of zero means not available"])
    w.add_Param(p)

    p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
    p.set_Description(["Pvalue for the alert, a value of zero means not available"])
    w.add_Param(p)

    p = Param(name="src_name", ucd="phys.src_name", unit="NA", dataType="str",  value=str(src_name))
    p.set_Description(["Source name, e.g. Mrk 421"])
    w.add_Param(p)

    p = Param(name="src_error_90", ucd="stat.error.sys", unit="deg", dataType="float",  value=str(src_error_90))
    p.set_Description(["Angular error of the source (90% containment)"])
    w.add_Param(p)

    p = Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(0))
    p.set_Description(["Observatories observing given part of the sky: 0 means IceCube"])
    w.add_Param(p)

    p = Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(1))
    p.set_Description(["Observatories triggering: 1 means IceCube triggered"])
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

    value2=Value2(alert[0].RA,alert[0].dec)
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
    print xml1
    f1=open('./test_alert.xml', 'w+')
    f1.write(xml1)
