"""
event_to_VOEvent: Sample program for use with VOEvent library.
Builds a simple VOEvent packet from event
See the VOEvent specification for details
http://www.ivoa.net/Documents/latest/VOEvent.html
"""
import sys
from datetime import datetime

#sys.path.append('../dbase')
from db_classes import *

from VOEventLib.VOEvent import *
from VOEventLib.Vutil import *

def event_to_voevent(alert):
    stream=alert[0].stream
    id = alert[0].id
    rev=alert[0].rev
    datenow=datetime.now()
    
    if (stream==0): 
        obsname="IceCube"
        aux1_value=5.545
        aux2_value=0.05
        aux3_value=22.7
        aux1_unit="TeV"
        aux2_unit=" "
        aux3_unit="deg"
        aux1_name="energy"
        aux2_name="kent_beta"
        aux3_name="kent_phi0"
        long=0.0000
        lat=-90.00
        elev=2835
        #aux1_value=parameter[0].value
        #aux1_unit=parameter[0].units
        #aux1_name=parameter[0].name
    elif (stream==1):
        obsname="ANTARES"
    elif (stream==3):
        obsname="Auger"  
    elif (stream==7):
        obsname="HAWK"
    else:
        print "No stream valid stream number"
        sys.exit(0)    
        
    ############ VOEvent header ############################

    v = VOEvent.VOEvent(version="2.0")
    v.set_ivorn("ivo://%s/test#%s" % (stream , str(id)))
    v.set_role("%s" % alert[0].type)
    v.set_Description("Report of some test event information")

    w = Who()
    #a = Author()
    w.set_AuthorIVORN("ivo://%s" % obsname)
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+"T"+datenow1[11:]
    w.set_Date(str(datenow2))
    #   a.add_contactName("Gordana Tesic, Miles Smith")
    #   a.add_contactEmail('gut10@psu.edu, mus44@psu.edu')
    #w.set_Author(a)
    v.set_Who(w)

    ############ What ############################
    w = What()

    
    p = Param(name="nevents", ucd="meta.number", unit=" ", dataType="float",  value=str(alert[0].nevents))
    p.set_Description(["Number of events"])
    w.add_Param(p)
    
    p = Param(name="deltaT", ucd="time.duration", unit="s", dataType="float",  value=str(alert[0].deltaT))
    p.set_Description(["Time window of the burst"])
    w.add_Param(p)
    
    p = Param(name="sigmaT", ucd="time", unit="s", dataType="float",  value=str(alert[0].sigmaT))
    p.set_Description(["Uncertainty of the time window"])
    w.add_Param(p)

    p = Param(name="false_pos", ucd="stat.probability", unit="s-1.sr-1 ", dataType="float",  value=str(alert[0].false_pos))
    p.set_Description(["False positive rate"])
    w.add_Param(p)
    
    p = Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(alert[0].pvalue))
    p.set_Description(["Pvalue"])
    w.add_Param(p)
    
    p = Param(name="point_RA", ucd="os.eq.ra", unit="deg", dataType="float",  value=str(alert[0].point_RA))
    p.set_Description(["Pointing RA"])
    w.add_Param(p)
    
    p = Param(name="point_dec", ucd="os.eq.dec", unit="deg", dataType="float",  value=str(alert[0].point_dec))
    p.set_Description(["Pointing Dec"])
    w.add_Param(p)
    
    p = Param(name="psf_type", ucd="meta.code.multip", unit=" ", dataType="string",  value=str(alert[0].psf_type))
    p.set_Description(["Type of psf (skymap, fisher, kent, king)"])
    w.add_Param(p)
    
    # A Group of Params
    g = Group(name="aux_params")
    p = Param(name="%s" % str(aux1_name), ucd="phys.energy", unit="%s" % str(aux1_unit), dataType="float", value="%s" % str(aux1_value))
    g.add_Param(p)
    p = Param(name="%s" % str(aux2_name), ucd="instr.det.psf", unit="%s" % str(aux2_unit), dataType="float", value="%s" % str(aux2_value))
    g.add_Param(p)
    p = Param(name="%s" % str(aux3_name), ucd="instr.det.psf", unit="%s" % str(aux3_unit), dataType="float", value="%s" % str(aux3_value))
    g.add_Param(p)
    w.add_Group(g)
    
    v.set_What(w)
    
    ############ Wherewhen ############################
    wwd = {'observatory':     obsname,
           'coord_system':    'UTC-GEOD-TOPO',
           'coord_system':    'UTC-ICRS-TOPO',
           'time':            alert[0].datetime,
           'timeError':       0.000001,
           'longitude':       alert[0].RA,
           'latitude':        alert[0].dec,
           'positionalError': alert[0].sigmaR,
    }
    
    ww = makeWhereWhen(wwd)
    
    
    if ww: v.set_WhereWhen(ww)
    #obsloc=v.ObsDataLocation().get_ObservatoryLocation()
   # v.get_WhereWhen().get_ObsDataLocation().get_ObservatoryLocation().set_ObservatoryLocation("UTC-GEOD-TOPO")
    obs=ObsDataLocation()
    obsloc=ObservatoryLocation()
    astro2=AstroCoordSystem("UTC-GEOD-TOPO")
    astro3=AstroCoords("UTC-GEOD-TOPO")
    value3=Value3(long,lat,elev)
    pos1=Position3D("deg-deg-m","longitude", "latitude", "elevation",value3)
    astro3.set_Position3D(pos1)
    obsloc.set_AstroCoordSystem(astro2)
    obsloc.set_AstroCoords(astro3)
    obs.set_ObservatoryLocation(obsloc)
    observation=ObservationLocation()
    astro4=AstroCoordSystem("UTC-ICRS-TOPO")
    astro5=AstroCoords("UTC-ICRS-TOPO")
    value2=Value2(200.0603169,45.3116578)
    pos2=Position2D("deg-deg", "RA","Dec",value2,alert[0].sigmaR)
    astro5.set_Position2D(pos2)
    #error2=Error2Radius(alert[0].sigmaR)
    #astro5.set_Error2Radius(error2)
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
    #vv=getWhereWhen(v)
    #vvv=vv.get_Observatory()
    #print vvv
    '''
    what = What()
    what.add_Param(Param(name='apple', value='123'))
    what.add_Param(Param(name='orange', value='124'))
    v.set_What(what)
    '''
    # print the XML
    #sys.stdout.write('<?xml version="1.0" ?>\n')
    #v.export(sys.stdout, 0, namespace_='voe:')
    #sys.stdout.write('\n')

    #schemaURL = "http://www.amon/VOEvent/VOEvent2-111111.xsd"

    #s = stringVOEvent(v, schemaURL)
    #print s
    ############ output the event ############################
    xml = stringVOEvent(v, 
    schemaURL = "http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd")
    #print xml
    return xml


if __name__ == "__main__":
    alert=[Event(0,1,0)]
    alert[0].type='test'
    alert[0].RA=200.0603169
    alert[0].dec=45.3116578
    alert[0].sigmaR=0.77
    alert[0].nevents   =  1    
    alert[0].deltaT    =  0.0 
    alert[0].false_pos =  0.00213
    alert[0].point_RA  =  0.0
    alert[0].point_dec  =  0.0
    alert[0].pvalue    =  0.09200 
    alert[0].psf_type    =  'fisher' 
    alert[0].sigmaT    =  0.0 
    alert[0].datetime = datetime.now() 
    alert[0].forprint()         
    
    xml1=event_to_voevent(alert)
    print xml1
    f1=open('./icecube_test.xml', 'w+')
    f1.write(xml1)
   
    
    