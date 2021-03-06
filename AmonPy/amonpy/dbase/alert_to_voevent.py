"""
alert_to_VOEvent: Sample program for use with VOEvent library.
Builds a simple VOEvent packet from alert
See the VOEvent specification for details
http://www.ivoa.net/Documents/latest/VOEvent.html
"""
from __future__ import print_function
from builtins import str
from builtins import object
import sys

from amonpy.dbase.db_classes import *

from VOEventLib.VOEvent import *
from VOEventLib.Vutil import *

class Alert2VOEvent(object):
    def __init__(self,alert,ivorn,description,gcn_stream,event_id,name="Hugo Ayala",email="hgayala@psu.edu"):
        stream = alert[0].stream
        #amon_id = alert[0].id
        rev = alert[0].rev
        self.voevent = VOEvent.VOEvent(version="2.0")
        self.voevent.set_ivorn("ivo://amon/%s#%s_%s_%s_%s"%(str(ivorn),str(gcn_stream),str(stream),str(event_id),str(rev)))
        self.voevent.set_role("%s" % alert[0].type)
        self.voevent.set_Description(str(description))
        a = Author()
        a.add_contactName(name)
        a.add_contactEmail(email)
        datenow=str(datetime.utcnow())
        d1 = datenow[0:10]+"T"+datenow[11:]
        w=Who()
        w.set_Date(d1)
        w.set_Author(a)
        self.voevent.set_Who(w)

    def WhatVOEvent(self,voeventparams):
        #CREATE FIRST THE DEFAULT AND EXTRA PARAMETERS
        w = What()
        if len(voeventparams)==0:
            print("need list of Parameters for voevent")
            return 0
        for i in voeventparams:
            w.add_Param(i)
        self.voevent.set_What(w)

    def MakeDefaultParams(self,alert):
        stream = alert[0].stream
        amon_id = alert[0].id
        rev = alert[0].rev
        paramlist = []
        # params related to the event. None are in Groups.
        p = Param(name="stream", ucd="meta.number", dataType="int", value=str(stream))
        p.set_Description(["Analysis stream identification"])
        paramlist.append(p)

        p = Param(name="amon_id", ucd="meta.number", dataType="string", value=str(amon_id))
        p.set_Description(["Alert identification"])
        paramlist.append(p)

        p = Param(name="rev", ucd="meta.number", dataType="int", value=str(rev))
        p.set_Description(["Alert revision"])
        paramlist.append(p)

        p = Param(name="nevents", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].nevents))
        p.set_Description(["Number of events in the alert"])
        paramlist.append(p)

        p = Param(name="deltaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].deltaT))
        p.set_Description(["Time window of the burst"])
        paramlist.append(p)

        p = Param(name="sigmaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(alert[0].sigmaT))
        p.set_Description(["Uncertainty of the time window"])
        paramlist.append(p)

        p = Param(name="false_pos", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].false_pos))
        p.set_Description(["False positive rate"])
        paramlist.append(p)

        p = Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].observing))
        p.set_Description(["Observatories observing given part og the sky"])
        paramlist.append(p)

        p = Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].trigger))
        p.set_Description(["Observatories triggering"])
        paramlist.append(p)

        p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
        p.set_Description(["Pvalue for the alert"])
        paramlist.append(p)

        p = Param(name="skymap", ucd="meta.code.multip", unit=" ", dataType="string",  value=str(alert[0].skymap))
        p.set_Description(["Skymap or no skymap assotiated with the alert"])
        paramlist.append(p)

        return paramlist

    def MakeParam(self,name,ucd,unit,datatype,value,description):
        p=Param(name=str(name), ucd=str(ucd), unit=str(unit), dataType=str(datatype), value=str(value))
        p.set_Description([str(description)])
        return p

    def MakeWhereWhen(self,alert):
        wwd = {'observatory':     'AMON',
               'coord_system':    'UTC-GEOD-TOPO',
               'time':            alert[0].datetime,
               'timeError':       0.000001,
               'longitude':       alert[0].RA,
               'latitude':        alert[0].dec,
               'positionalError': alert[0].sigmaR,
        }
        ww = makeWhereWhen(wwd)
        if ww: self.voevent.set_WhereWhen(wwd)  #What does this do?

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
        pos2=Position2D("deg-deg", "RA","Dec",value2, alert[0].sigmaR)
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
        self.voevent.set_WhereWhen(ww)

    def writeXML(self):
        if self.voevent is not None:
            xml = stringVOEvent(self.voevent,
                                schemaURL = "http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd")
            return xml
        else:
            print("xml not written. Need to fill the information first")



def alert_to_voevent(alert):
    stream=alert[0].stream
    amon_id = alert[0].id
    rev=alert[0].rev

    datenow=datetime.now()
    ############ VOEvent header ############################

    v = VOEvent.VOEvent(version="2.0")
    if (alert[0].trigger==2):
        v.set_ivorn("ivo://amon/icecube_coinc#%s" % str(stream)+'_'+str(amon_id)+'_' + str(rev))
    else:
        v.set_ivorn("ivo://amon/multi_mesg#%s" % str(stream)+'_'+str(amon_id)+'_' + str(rev))

    v.set_role("%s" % alert[0].type)
    if (alert[0].trigger==2):
        v.set_Description("Report of the IceCube neutrino multiplet")
    else:
        v.set_Description("Report of the multimessenger multiplets")


    w = Who()
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+"T"+datenow1[11:]
    w.set_Date(str(datenow2))
    a = Author()
    a.add_contactName("Hugo Ayala")
    a.add_contactEmail('hgayala@psu.edu')
    w.set_Author(a)
    v.set_Who(w)

    ############ What ############################
    w = What()

    # params related to the event. None are in Groups.
    p = Param(name="stream", ucd="meta.number", dataType="int", value=str(stream))
    p.set_Description(["Analysis stream identification"])
    w.add_Param(p)

    p = Param(name="amon_id", ucd="meta.number", dataType="int", value=str(amon_id))
    p.set_Description(["Alert identification"])
    w.add_Param(p)

    p = Param(name="rev", ucd="meta.number", dataType="int", value=str(rev))
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
    p.set_Description(["False positive rate"])
    w.add_Param(p)

    p = Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].observing))
    p.set_Description(["Observatories observing given part og the sky"])
    w.add_Param(p)

    p = Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(alert[0].trigger))
    p.set_Description(["Observatories triggering"])
    w.add_Param(p)

    p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
    p.set_Description(["Pvalue for the alert"])
    w.add_Param(p)

    p = Param(name="skymap", ucd="meta.code.multip", unit=" ", dataType="string",  value=str(alert[0].skymap))
    p.set_Description(["Skymap or no skymap assotiated with the alert"])
    w.add_Param(p)


    v.set_What(w)

    ############ Wherewhen ############################
    wwd = {'observatory':     'AMON',
           'coord_system':    'UTC-GEOD-TOPO',
           'time':            alert[0].datetime,
           'timeError':       0.000001,
           'longitude':       alert[0].RA,
           'latitude':        alert[0].dec,
           'positionalError': alert[0].sigmaR,
    }

    ww = makeWhereWhen(wwd)
    if ww: v.set_WhereWhen(ww)

    #if ww: v.set_WhereWhen(ww)
    #obsloc=v.ObsDataLocation().get_ObservatoryLocation()
   # v.get_WhereWhen().get_ObsDataLocation().get_ObservatoryLocation().set_ObservatoryLocation("UTC-GEOD-TOPO")
    obs=ObsDataLocation()
    obsloc=ObservatoryLocation()
    astro2=AstroCoordSystem("UTC-GEOD-TOPO")
    astro3=AstroCoords("UTC-GEOD-TOPO")
    #value3=Value3(0.0000,-90.00,2835)
    #pos1=Position3D("deg-deg-m","longitude", "latitude", "elevation",value3)
    #astro3.set_Position3D(pos1)
    obsloc.set_AstroCoordSystem(astro2)
    obsloc.set_AstroCoords(astro3)
    obs.set_ObservatoryLocation(obsloc)
    observation=ObservationLocation()
    astro4=AstroCoordSystem("UTC-ICRS-TOPO")
    astro5=AstroCoords("UTC-ICRS-TOPO")
    time2=alert[0].datetime
    value2=Value2(alert[0].RA,alert[0].dec)
    pos2=Position2D("deg-deg", "RA","Dec",value2, alert[0].sigmaR)
    astro5.set_Position2D(pos2)
    #error2=Error2Radius(alert[0].sigmaR)
    #astro5.set_Error2Radius()


    time_1=Time("s")
    time2=str(alert[0].datetime)
    time2_2=time2[0:10]+"T"+time2[11:]

    #time2_2=time2[0:10]+"T"+time2[11:]
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
