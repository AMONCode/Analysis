from __future__ import division
from __future__ import print_function
from builtins import str
import numpy as np
import healpy as hp
import sys
from datetime import datetime,timedelta
from astropy.time import Time
import os, netrc
import subprocess
import MySQLdb as mdb
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
#os.chdir('/storage/home/cft114/fermicron')
from amonpy.tools.fermifunctions import distsph,spang,berring,getgridtrack,getlam,lam2prob,tsep,numul
from amonpy.tools.config import AMON_CONFIG as configs

user=configs.get('database','username')
host=configs.get('database','host_name')
password=configs.get('database','password')
dbname=configs.get('database','realtime_dbname')

#dpath=configs.get('dirs','fermidata')
dpath=configs.get('dirs','amonpydir')
AlertDir = configs.get('dirs','alertdir')

nrc_fname = os.path.join(AMON_CONFIG.get('dirs','amonpydir'), '.netrc')
nrc = netrc.netrc(nrc_fname)

#now we run the fermi analysis against icecube/antares

now=datetime.utcnow()

goback=timedelta(days=1) #want to get everything a day before now

earlydt=now-goback


db=mdb.connect(user=user,host=host,passwd=password,db=dbname)
c=db.cursor()
#stream=1 -> antares
#stream=0 -> IceCube

c.execute('''SELECT id,time,time_msec,RA,`DEC`,pvalue FROM event WHERE eventStreamConfig_stream=1 and time >= %s''', (earlydt,))

icdat=np.array(c.fetchall())

db.close()

#check to make sure neutrino event list contains data
if len(icdat)==0:
    print("no Antares events in range, we're done here")
    sys.exit()

ictime=Time(icdat[:,1],scale='utc').mjd #convert to mjd
msec=icdat[:,2].astype(int)
ictime+=(msec/(86400*1000))#reattach milliseconds to times

#now we sort icecube events by time

icdat=icdat[np.argsort(ictime)]
ictime=ictime[np.argsort(ictime)]
icid=icdat[:,0].astype(float)
icra=np.radians(icdat[:,3].astype(float))
icdec=np.radians(icdat[:,4].astype(float))
icprob=icdat[:,5].astype(float) #make sure all are of the correct type

#now we need to import the fermi events
goback=timedelta(days=1.5) #want to get everything a day before now

earlydt=now-goback

db=mdb.connect(user=user,host=host,passwd=password,db=dbname)
c=db.cursor()

c.execute('''SELECT id,time,time_msec,RA,`DEC` FROM event WHERE eventStreamConfig_stream=23 and time >= %s''', (earlydt,))

fermidat=np.array(c.fetchall())

#check if photon list has events
if len(fermidat)==0:
    print("no Fermi events in range, we're done here")
    sys.exit()

ids=fermidat[:,0].astype(int)

start=np.min(ids)

c.execute('''SELECT value,event_id FROM parameter WHERE name = 'energy' and event_eventStreamConfig_stream=23 and event_id>= %s''', (start,))

energylist=np.array(c.fetchall()) #get photon energies

c.execute('''SELECT value,event_id FROM parameter WHERE name = 'inclination' and event_eventStreamConfig_stream=23 and event_id>= %s''', (start,))

inclist=np.array(c.fetchall())  #get inclination angle

c.execute('''SELECT value,event_id FROM parameter WHERE name = 'conversion' and event_eventStreamConfig_stream=23 and event_id>= %s''', (start,))

conlist=np.array(c.fetchall()) #get photon conversion type

db.close()

#now sort the four arrays by their ID, which is time

fermidat=fermidat[np.argsort(ids)]

energylist=energylist[np.argsort(energylist[:,1])]
inclist=inclist[np.argsort(inclist[:,1])]
conlist=conlist[np.argsort(conlist[:,1])]

#now that everything is sorted, break into individual pieces

phtime=Time(fermidat[:,1],scale='utc').mjd #convert datetime to mjd
msec=fermidat[:,2].astype(int)
phtime+=(msec/(86400*1000)) #reattach millisecond to times

phra=np.radians(fermidat[:,3].astype(float))
phdec=np.radians(fermidat[:,4].astype(float))

energy=energylist[:,0].astype(float)
inc=np.radians(inclist[:,0].astype(float))
acos=np.cos(inc)
con=conlist[:,0].astype(int)

#import photon background map
phbkg=np.zeros((2,3,786432))

fitsfile = os.path.join(dpath,"data/fermi_lat",'scaledbackground.fits')
temp=np.array(hp.read_map(fitsfile,field=(0,1,2)))

phbkg[1,:,:]=temp*3.3026

fitsfile = os.path.join(dpath,"data/fermi_lat",'scaledbackgroundinc.fits')
temp=np.array(hp.read_map(fitsfile,field=(0,1,2)))

phbkg[0,:,:]=temp*3.3026

base=np.zeros((len(phtime)*2,2),dtype=int) #create empty array to fill with time pairs
evil=tsep(ictime,phtime,base,1/86.4) #fill it with pairs
#now check to make sure pairs actually exist

if len(evil)==0:
    print("no nu/ph coincidences in time, we're done here")
    sys.exit()


#evil contains all nu/ph pairs within 100 secs, from presorted lists created before loopinng
#now we calculate angular separation
dsts=distsph(phra[evil[:,0]],phdec[evil[:,0]],icra[evil[:,1]],icdec[evil[:,1]])
#and cut on separation above 5 degrees
good=evil[np.where(dsts<np.radians(5))] #array of nu/ph pairs within 100 secs and 5 degrees

if len(good)==0:
    print("no nu/ph coincidences in space, we're done here")
    sys.exit()

msep=dsts[np.where(dsts<np.radians(5))] #distances of pairs
#define psf calculation process

unu,nuind=np.unique(good[:,1],return_index=True)
#unu: index of each unique neutrino
#nucount: number of  photons associated with each unique neutrino


counter=0 #start loop to process each event

lambdas=np.zeros((len(ictime)*10,10))
primarycount=0

while counter<len(unu):
    nu=unu[counter] #index of neutrino
    b=np.argwhere(good[:,1]==nu) # list of photons associated with neutrino
    inds=good[b[:,0],0] #index of photons associated with the neutrino
    ra=phra[inds] #ra of photons
    dec=phdec[inds] #dec of photons
    e=energy[inds] #energy of photons
    ac=acos[inds] #cos of inclination of photons
    c=con[inds] #convertion type of photons
    time=phtime[inds] #arrival time of photons

    nuid=icid[[nu]]
    nura=icra[[nu]] #neutrino ra
    nudec=icdec[[nu]] #neutrino dec
    nutime=ictime[[nu]] #neutrion arrival time
    nuprob=icprob[[nu]]

    #now set up condition for multiplet search

    #define locally flat coordinate system with neutrino at origin
    ang,dst=spang(nura,nudec,ra,dec) #polar coords of each photon
    x=dst*np.sin(ang)
    y=dst*np.cos(ang)
    #cartesian grid of each photon

    #get basic grid of psfs for multiplet
    xg0,yg0,rholderph0,rholdernu0,zholderph0,zholdernu0=getgridtrack(0,0,np.radians(5),40,[0],[0],x,y,e,ac,c)
    #get back array of nu and photon psfs
    #create single grid of the product

    gridfinalph=np.sum(rholderph0,axis=0) #sum of photon grid
    gridfinalnu=np.sum(rholdernu0,axis=0) #sum of neutrino grid
    gridfinal=gridfinalph+gridfinalnu

    mx=np.argmax(gridfinal) #max of product
    i1=mx//len(gridfinal)
    i2=mx%len(gridfinal) #convert flat index to grid index
    cx=xg0[0,i2]
    cy=yg0[i1,0] #center coordinates

    #now get a better grid of smaller region
    xg1,yg1,rholderph1,rholdernu1,zholderph1,zholdernu1=getgridtrack(cx,cy,np.radians(1),70,[0],[0],x,y,e,ac,c)

    #find lambda of overall multiplet
    lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,nura,nudec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)

    #now get rid of worst photon, one at a time
    #initialize a list to hold original lambda and other parameters

    bestline=np.array([lam,tcenter,deltat,sigmat,ra,dec,coincerr,len(vals),len(nutime),nuid])

    while len(vals)>1:
        bs=np.argmin(vals) #index of worst photon
        rholderph1=np.delete(rholderph1,bs,0) #cut off worst slice
        e=np.delete(e,bs)
        ac=np.delete(ac,bs)
        c=np.delete(c,bs)
        time=np.delete(time,bs)
        x=np.delete(x,bs)
        y=np.delete(y,bs)

        #now calculate new lambda with worst photon cut off
        lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,nura,nudec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)
        #check if best position is near the edge of the grid
        if edge==1: #if so, remake grid over new center
            print('lets fix that')
            xg1,yg1,rholderph1,rholdernu1,zholderph1,zholdernu1=getgridtrack(cx,cy,np.radians(1),70,[0],[0],x,y,e,ac,c)
            #then recalculate lambda
            lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,nura,nudec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)
        if lam>bestline[0]: #if it new is better, replace old
            bestline=np.array([lam,tcenter,deltat,sigmat,ra,dec,coincerr,len(vals),len(nutime),nuid])

    lambdas[primarycount]=bestline

    primarycount+=1
    counter+=1


nulist=numul(ictime,icra,icdec)
cra=np.zeros(len(nulist)) #hold the ra of the center
cdec=np.zeros(len(nulist)) #hold dec of center
ctime=np.zeros(len(nulist)) #hold the time


lcount=0
while lcount<len(nulist):
    nutime=ictime[nulist[lcount]]
    nura=icra[nulist[lcount]]
    nudec=icdec[nulist[lcount]]
    nuprob=icprob[nulist[lcount]]
    nuid=icid[nulist[lcount]]

    ctime[lcount]=np.average(nutime) #average coincidence time
    #due to working on a globe, taking a direct average is inaccurate near the poles,
    #so we first get an approximate position the cartesian way,
    #then make a grid centered at that point in flat space to find the true center

    tempra=np.average(nura,)    #temporary center ra, weighted average position
    tempdec=np.average(nudec) #temporary center dec

    nang,ndst=spang(tempra,tempdec,nura,nudec)

    tempx=ndst*np.sin(nang)
    tempy=ndst*np.cos(nang) #temporary cartesian coordinates

    centx=np.average(tempx)
    centy=np.average(tempy)

    tempdst=np.hypot(centx,centy) #distance to true center
    tempang=np.arctan2(centx,centy) #angle to true center

    cra[lcount],cdec[lcount]=berring(tempra,tempdec,tempdst,tempang) #use false center to get true center

    #cra,cdec,ctime for this multiplet are the desired results of this loop
    lcount+=1

#now we can find photons (if any) associated with each neutrino

base=np.zeros((len(phtime),2),dtype=int)
pairs=np.array(tsep(ctime,phtime,base,1/86.4))

dst=distsph(phra[pairs[:,0]],phdec[pairs[:,0]],cra[pairs[:,1]],cdec[pairs[:,1]])

good=pairs[np.where(dst<np.radians(5))]

unu,nuind=np.unique(good[:,1],return_index=True)

mcounter=0
while mcounter<len(unu):
    nu=unu[mcounter] #index of coincidence
    b=np.argwhere(good[:,1]==nu)
    inds=good[b[:,0],0] #index of phtons associated with neutrino
    ra=phra[inds]
    dec=phdec[inds] #dec of photons
    e=energy[inds] #energy of photons
    ac=acos[inds] #cos of inclination of photons
    c=con[inds] #convertion type of photons
    time=phtime[inds] #arrival time of photons

    nura=icra[nulist[nu]] #neutrino parameters for the multiplet
    nudec=icdec[nulist[nu]]
    nutime=ictime[nulist[nu]]
    nuprob=icprob[nulist[nu]]

    #now the center parameters
    centra=cra[nu]
    centdec=cdec[nu]

    #now get cartesian coordinates of neutrinos and photons
    phang,phdst=spang(centra,centdec,ra,dec)
    phx=phdst*np.sin(phang)
    phy=phdst*np.cos(phang)

    nuang,nudst=spang(centra,centdec,nura,nudec)
    nux=nudst*np.sin(nuang)
    nuy=nudst*np.sin(nuang)

    #get basic grid of psf for coincidence
    xg0,yg0,rholderph0,rholdernu0,zholderph0,zholdernu0=getgridtrack(0,0,np.radians(5),40,nux,nuy,phx,phy,e,ac,c)

    gridfinalph=np.sum(rholderph0,axis=0) #sum of photon grid
    gridfinalnu=np.sum(rholdernu0,axis=0) #sum of neutrino grid
    gridfinal=gridfinalph+gridfinalnu #sum of the two grids together

    mx=np.argmax(gridfinal)
    i1=mx//len(gridfinal)
    i2=mx%len(gridfinal) #convert flat index to grid index
    cx=xg0[0,i2]
    cy=yg0[i1,0] #center coordinates

    #now get a better grid of smaller region
    xg1,yg1,rholderph1,rholdernu1,zholderph1,zholdernu1=getgridtrack(cx,cy,np.radians(1),70,nux,nuy,phx,phy,e,ac,c)

    #find lambda of overall multiplet
    lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,centra,centdec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)

    #now get rid of worst photon, one at a time
    #initialize a list to hold original lambda and other parameters

    bestline=np.array([lam,tcenter,deltat,sigmat,ra,dec,coincerr,len(vals),len(nutime),nuid])

    while len(vals)>1:
        bs=np.argmin(vals) #index of worst photon
        rholderph1=np.delete(rholderph1,bs,0) #cut off worst slice
        e=np.delete(e,bs)
        ac=np.delete(ac,bs)
        c=np.delete(c,bs)
        time=np.delete(time,bs)
        phx=np.delete(phx,bs)
        phy=np.delete(phy,bs)

        #now calculate new lambda with worst photon cut off
        lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,centra,centdec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)
        #check if best position is near the edge of the grid
        if edge==1: #if so, remake grid over new center
            print('lets fix that')
            xg1,yg1,rholderph1,rholdernu1,zholderph1,zholdernu1=getgridtrack(cx,cy,np.radians(1),70,[0],[0],phx,phy,e,ac,c)
            #then recalculate lambda
            lam,vals,ra,dec,coincerr,tcenter,deltat,sigmat,edge,cx,cy=getlam(rholderph1,rholdernu1,centra,centdec,nutime,nuprob,time,xg1,yg1,e,ac,phbkg)
        if lam>bestline[0]: #if it new is better, replace old
            bestline=np.array([lam,tcenter,deltat,sigmat,ra,dec,coincerr,len(vals),len(nutime),nuid])
    #now compare newly generated lambda to each single-neutrino version
    flagid=nulist
    n=0
    perfection=1
    indexholder=np.zeros(len(flagid))
    nmark=0
    while n<len(flagid): #compare to all singlets
        index=np.argwhere(lambdas[:,-1]==flagid[n])
        if len(index)>0:
            indexholder[nmark]=index[0,0]
            lamholder=lambdas[index,0]
            if lam<lamholder:
                perfection=0
        else:
            indexholder=np.delete(indexholder,nmark)
            nmark-=1
        nmark+=1
        n+=1

    if perfection==1:
        #print 'attached'
        lambdas=np.delete(lambdas,indexholder,0) #delete the old
        primarycount-=len(indexholder)
        #print indexholder
        lambdas[primarycount]=bestline
        primarycount+=1


    mcounter+=1


lambdas=lambdas[0:primarycount,:]


def writeevents(user,host,passwd,lam,tcenter,deltat,sigmat,ra,dec,coincerr,nnu,nph,flagid):
    #write coincidence to table
    #input lambda value generated, coincidence time, time spread, time uncertainty, ra, dec, coincidence error radius
    #number of neutrinos, number of photons, and coincidence ID
    coinctime=Time(tcenter,format='mjd').datetime #coincidence time in datetime format
    lessec=coinctime.replace(microsecond=0) #round to nearest second
    msec=int(1000*(coinctime-lessec).total_seconds()) #miliseconds in integer form
    ntot=int(nnu+nph)

    fpos=lam2prob(lam) #how often we get this lambda or higher, in units of Hz

    written=0 #flag to see if the event gets written, preset to 0

    db=mdb.connect(user=user,host=host,passwd=passwd,db=dbname)
    c=db.cursor()

    c.execute("""SELECT id,false_pos,rev FROM alert WHERE alertConfig_stream=8 and id=%s""",(int(flagid),))
    previous=np.array(c.fetchall())
    if len(previous)==0: #if coincidence has not been previously written
        print('writing a new one')
        event=[8,int(flagid),0,lessec,msec,dec,ra,coincerr,ntot,deltat,sigmat,fpos,0,0,'observation',1,0,0]
        c.execute("""INSERT INTO alert VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",event)
        db.commit()
        written=1 #turn to 1 if it gets written

    else:
        print(np.shape(previous))
        oldprob=previous[-1,1]
        if fpos<(oldprob*0.99): #check to make sure we don't re-write due to round-off errors
            #only re-write if smaller by at least 1%
            oldrev=previous[-1,2]
            print('it got better')
            event=[8,int(flagid),oldrev+1,lessec,msec,dec,ra,coincerr,ntot,deltat,sigmat,fpos,0,0,'observation',1,0,0]
            c.execute("""INSERT INTO alert VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",event)
            db.commit()
            written=1
        else:
            oldrev=previous[-1,2]
            event=[8,int(flagid),oldrev,lessec,msec,dec,ra,coincerr,ntot,deltat,sigmat,fpos,0,0,'observation',1,0,0]


    return event,written


import VOEventLib.VOEvent as ve
import VOEventLib.Vutil as vu

def makevoevent(event):

    stream=event[0] #number of fermi-antares alert stream
    amon_id=event[1]
    datenow=datetime.now()
    rev=event[2]
    lessec=event[3]
    msec=event[4]

    fulltime=lessec+timedelta(milliseconds=msec)

    dec=event[5]
    ra=event[6]
    coincerr=event[7]
    ntot=event[8]
    deltat=event[9]
    sigmat=event[10]
    fpos=event[11]



    #VOEvent header

    v=ve.VOEvent(version='2.0')
    v.set_ivorn("ivo://amon/antares_fermilat_coinc#%s" % str(stream)+'_'+str(amon_id)+'_' + str(rev))

    v.set_role('test')
    v.set_Description('Fermi-ANTARES coincidence')

    w=ve.Who()
    datenow1=str(datenow)
    datenow2=datenow1[0:10]+'T'+datenow1[11:]
    w.set_Date(str(datenow2))
    a=ve.Author()
    a.add_contactName('Colin Turley')
    a.add_contactEmail('cft114@psu.edu')
    w.set_Author(a)
    v.set_Who(w)

    #define What

    w=ve.What()

    p=ve.Param(name='stream',ucd='meta.number',dataType='int',value=str(stream))
    p.set_Description(['Analysis Stream Identification'])
    w.add_Param(p)

    p = ve.Param(name="amon_id", ucd="meta.number", dataType="int", value=str(amon_id))
    p.set_Description(["Alert Identification"])
    w.add_Param(p)

    p = ve.Param(name="rev", ucd="meta.number", dataType="int", value=str(rev))
    p.set_Description(["Alert Revision"])
    w.add_Param(p)

    p = ve.Param(name="nevents", ucd="meta.number", unit=" ", dataType="int",  value=str(ntot))
    p.set_Description(["Number of events in the alert"])
    w.add_Param(p)

    p = ve.Param(name="deltaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(deltat))
    p.set_Description(["Time window of the burst"])
    w.add_Param(p)

    p = ve.Param(name="sigmaT", ucd="time.timeduration", unit="s", dataType="float",  value=str(sigmat))
    p.set_Description(["Uncertainty of the time window"])
    w.add_Param(p)

    p = ve.Param(name="false_pos", ucd="stat.probability", unit=" ", dataType="float",  value=str(fpos))
    p.set_Description(["False positive rate"])
    w.add_Param(p)

    p = ve.Param(name="observing", ucd="meta.number", unit=" ", dataType="int",  value=str(2))
    p.set_Description(["Observatories observing given part og the sky"])
    w.add_Param(p)

    p = ve.Param(name="trigger", ucd="meta.number", unit=" ", dataType="int",  value=str(2))
    p.set_Description(["Observatories triggering"])
    w.add_Param(p)

    p = ve.Param(name="pvalue", ucd="stat.probability", unit=" ", dataType="float",  value=str(1))
    p.set_Description(["Pvalue for the alert"])
    w.add_Param(p)

    p = ve.Param(name="skymap", ucd="meta.code.multip", unit=" ", dataType="string",  value=str(0))
    p.set_Description(["Skymap or no skymap assotiated with the alert"])
    w.add_Param(p)


    v.set_What(w)

    #define WhereWhen

    wwd = {'observatory':     'AMON',
           'coord_system':    'UTC-GEOD-TOPO',
           'time':            fulltime,
           'timeError':       0.000001,
           'longitude':       ra,
           'latitude':        dec,
           'positionalError': coincerr,
    }

    ww=vu.makeWhereWhen(wwd)

    if ww: v.set_WhereWhen(ww)

    if ww: v.set_WhereWhen(ww)

    obs=ve.ObsDataLocation()
    obsloc=ve.ObservatoryLocation()
    astro2=ve.AstroCoordSystem("UTC-GEOD-TOPO")
    astro3=ve.AstroCoords("UTC-GEOD-TOPO")
    obsloc.set_AstroCoordSystem(astro2)
    obsloc.set_AstroCoords(astro3)
    obs.set_ObservatoryLocation(obsloc)
    observation=ve.ObservationLocation()
    astro4=ve.AstroCoordSystem("UTC-ICRS-TOPO")
    astro5=ve.AstroCoords("UTC-ICRS-TOPO")
    time2=fulltime
    value2=ve.Value2(ra,dec)
    pos2=ve.Position2D("deg-deg", "RA","Dec",value2, coincerr)
    astro5.set_Position2D(pos2)

    time_1=ve.Time('s')
    time2=str(time2)
    time2_2=time2[0:10]+'T'+time2[11:]

    time3=ve.TimeInstant(time2_2)
    time_1.set_TimeInstant(time3)
    astro5.set_Time(time_1)

    observation.set_AstroCoordSystem(astro4)
    observation.set_AstroCoords(astro5)
    obs.set_ObservationLocation(observation)
    ww.set_ObsDataLocation(obs)
    v.set_WhereWhen(ww)

    ############ output the event ############################

    xml = vu.stringVOEvent(v,
    schemaURL = "http://www.ivoa.net/xml/VOEvent/VOEvent-v2.0.xsd")
    #print xml
    return xml

def send_email(subject, body, to):
    me = nrc.hosts['gmail'][0] + '@gmail.com'
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(to)
    pas = nrc.hosts['gmail'][2]
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(me, pas)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def send_email_attach(subject, body, to, attachment):
    me = nrc.hosts['gmail'][0] + '@gmail.com'
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(to)
    msg.attach(MIMEText(body))
    pas = nrc.hosts['gmail'][2]
    
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(attachment, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=attachment)
    msg.attach(part)
    
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    s.login(me, pas)
    s.sendmail(me, to, msg.as_string())
    s.quit()

    

n=0
xmlpathholder=[] #list to hold all new xml file names
lamlist=[]
while n<len(lambdas):
    line=lambdas[n]
    lam=line[0]
    tcenter=line[1]
    deltat=line[2]*86400 #convert to seconds, not days
    sigmat=line[3]*86400
    ra=np.degrees(line[4])
    dec=np.degrees(line[5])
    coincerr=np.degrees(line[6])
    nnu=line[7]
    nph=line[8]
    flagid=line[9]
    a,b=writeevents(user,host,password,lam,tcenter,deltat,sigmat,ra,dec,coincerr,nnu,nph,flagid)
    if lam>1.45 and b==1: #lambda of 1.45 is the 4/year threshold, b is a flag to see if the event was newly written
        lamlist.append(lam)
        xml=makevoevent(a)
        print(xml)
        fname = 'fermi-antares_coinc'+str(int(flagid))+'.xml'
        filen=os.path.join(AlertDir,fname)
        xmlpathholder.append(filen) #put name into list
        f1=open(filen,'w+')
        f1.write(xml)
        f1.close()
    print(n,a)
    n+=1

if len(lambdas)>5:
    #if we see too many lambdas generated in this stretch
    print('Too Many Events')
    subject='Too many Events'
    body='Detected %d events. That is too many. They will not be sent to GCN \n   Good Luck' % (n)
    send_email(subject,body,['cft114@psu.edu'])
    sys.exit()
    

n=0
while n<len(xmlpathholder):
    #if  we do not trigger an error, send all new events to GCN
    print('sending email %d' % (n,))
    subject='New Fermi-ANTARES Alert'
    body='New Fermi-ANTARES alert detected with a lambda of %f. XML sent to GCN is attached \n  Enjoy' % (lamlist[n])
    send_email_attach(subject,body,['cft114@psu.edu'],xmlpathholder[n])
    
    cmd=['/home/ubuntu/Software/miniconda3/bin/comet-sendvo']
    cmd.append('--file=' + xmlpathholder[n])
    subprocess.check_call(cmd)
    
    n+=1
    










