from __future__ import division
import urllib2
import numpy as np
import pyfits as pf
import sys
from datetime import datetime,timedelta
from astropy.time import Time
import os
import MySQLdb as mdb

from amonpy.tools.fermifunctions import geterr
from amonpy.tools.config import AMON_CONFIG as configs


user=configs.get('database','username')
host=configs.get('database','host_name')
password=configs.get('database','password')
dbname=configs.get('database','realtime_dbname')

#dpath=configs.get('dirs','fermidata')
dpath=configs.get('dirs','amonpydir')


def downloader(url,name):
    u=urllib2.urlopen(url)
    f=open(name,'wb')
    f.write(u.read())
    f.close()

def fermiwrite(user,password,host,time,flagid,ra,dec,energy,inc,con,start,stop,raz,decz,lat,lon,alt):
    '''needed parameters for amon table:
    eventstreamconfig (look up number for fermi)
    id (fermi second x100000, rounded to integer)
    time (datetime)
    msecs (miliseconds to datetime)
    declination
    right ascension
    sigmar (error in position, use 1sigma (39% containment)
    nevents (hardset to 1)
    deltat (hardset to 0)
    sigmat (time uncertainty, fermi is accurate to 10 microseconds, hardset to 0.00001)
    false pos (?) (currently set as zero)
    pval (?) (currently hardset to zero)
    type (hardset to 'observation')
    pointra (ra of lat z+ axis)
    pointdec (dec of lat z+ axis)
    longitude (spacecraft longitude in degrees)
    latitude (spacecraft latitude in degrees)
    elevation (spacecraft altitude in meters)
    psf type (hardset to 'king')
    eventstreamconfigrev (hardset to 1)

    aux parameter table (three total per event)
    first three columns are unique on each file
    name=energy     name=inclination        name=conversion
    values taken from file
    units=MeV       units=degrees       units=boolean
    eventstreamconfig
    id
    rev=1
'''

    base=datetime(2015,04,06,7,59,57) #second 450000000 in fermi system
    n=0
    events=[]
    param=[]
    m=0
    while n<len(time): #set up loop through photon events
        ts=time[n] #time of current photon event

        while ts>stop[m]: #increments window if we are too early
            m+=1

        if start[m]<ts<stop[m]:
            #continue if event is in window

            #satellite position information
            slat=lat[m]
            slon=lon[m]
            salt=alt[m]
            scra=raz[m]
            scdec=decz[m]

            totality=timedelta(seconds=(ts-450000000))+base #convert fermi seconds to datetime
            lessec=totality.replace(microsecond=0) #rounded to nearest second
            msec=int(1000*(totality-lessec).total_seconds()) #miliseconds in integer form



            #follows order shown in comment above
            events.append(
            [23,flagid[n],1,lessec,msec,dec[n],ra[n],err[n],1,0,0.00001, #last entry: sigmat
             0,0,'observation',scra,scdec,slon,slat,salt,'king',0]
            )


            param.append(['energy',energy[n],'MeV',23,flagid[n],1])
            param.append(['inclination',inc[n],'degrees',23,flagid[n],1])
            param.append(['conversion',con[n],'boolean',23,flagid[n],1])

        n+=1


    #connect to db and put these into database

    db=mdb.connect(user=user,host=host,passwd=password,db=dbname)
    c=db.cursor()

    c.executemany("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s,%s)""", events)
    db.commit()

    c.executemany("""INSERT INTO parameter VALUES(%s,%s,%s,%s,%s,%s)""",param)
    db.commit()

    db.close()


    return events


#get current fermi week
base=datetime(2016,01,28) #date/time of start of week 400
now=datetime.utcnow() #current time in utc
weekfloat=((now-base).total_seconds())/(60*60*24*7)+400
week=int(np.floor(weekfloat)) #the current fermi week

#first check the two most recent lat weekly files to see if they have been modified since last time


phurl='ftp://legacy.gsfc.nasa.gov/fermi/data/lat/weekly/photon/'
scurl='ftp://legacy.gsfc.nasa.gov/fermi/data/lat/weekly/spacecraft/'

phname1='lat_photon_weekly_w' + str(week) + '_p302_v001.fits'
phname0='lat_photon_weekly_w' + str(week-1) + '_p302_v001.fits'

scname1='lat_spacecraft_weekly_w' + str(week) + '_p202_v001.fits'
scname0='lat_spacecraft_weekly_w' + str(week-1) + '_p202_v001.fits'


try:
    #safety just in case file one of the files has not been created
    u0=urllib2.urlopen(phurl+phname0)
    u1=urllib2.urlopen(phurl+phname1)
except urllib2.URLError:
    #self terminate if file is not there
    print 'photon file does not exist'
    sys.exit()


i0=int(u0.info().values()[0]) #size of last week's photon file
i1=int(u1.info().values()[0]) #size of this week's photon file

#define file name for downloaded files

ph0=os.path.join(dpath,'data/fermi_lat','latphoton0.fits')
ph1=os.path.join(dpath,'data/fermi_lat','latphoton1.fits')
sc0=os.path.join(dpath,'data/fermi_lat','latsc0.fits')
sc1=os.path.join(dpath,'data/fermi_lat','latsc1.fits')

#now check cached photon files to see if the size has changed

#create flag to determine when analysis should proceed
cflag=False

ex0=os.path.isfile(ph0) #check if last week's file exists
if ex0==True: #if file exists

    temp0=os.path.getsize(ph0) # length of cached photon file

    if temp0!=i0: #if length of last week has changed
        downloader(phurl+phname0,ph0)
        downloader(scurl+scname0,sc0)
        cflag=True #set flag to true so we know to write later

else: # if last week's file does not exist
    downloader(phurl+phname0,ph0)
    downloader(scurl+scname0,sc0)
    cflag=True

ex1=os.path.isfile(ph1) #check if this week's file exists
if ex1==True: #if file exists

    temp1=os.path.getsize(ph1) # length of cached photon file

    if temp1!=i1: #if length of this week has changed
        downloader(phurl+phname1,ph1)
        downloader(scurl+scname1,sc1)
        cflag=True #set flag to true so we know to write later

else: # if this week's file does not exist
    downloader(phurl+phname1,ph1)
    downloader(scurl+scname1,sc1)
    cflag=True


#now double check to make sure all files exist

if os.path.isfile(ph0)==0: #nonexistance condition
    downloader(phurl+phname0,ph0) #if it does not exist, download it

if os.path.isfile(ph1)==0: #nonexistance condition
    downloader(phurl+phname1,ph1)

if os.path.isfile(sc0)==0: #nonexistance condition
    downloader(scurl+scname0,sc0)

if os.path.isfile(sc1)==0: #nonexistance condition
    downloader(scurl+scname1,sc1)


if cflag==False: #if no new files were downloaded, script should exit here
    print "nothing new, we're done here"
    sys.exit()

#now we open the fermi data and filter it by energy, zenith, time, etc

raw=pf.open(ph0)
data0=raw[1].data
raw.close()
raw=pf.open(ph1)
data1=raw[1].data

data=np.concatenate((data0,data1))

data=data[np.where(data['ZENITH_ANGLE']<90)] #filter by zenith angle
data=data[np.where(data['ENERGY']>100)] #low energy cut
data=data[np.where(data['ENERGY']<300000)] #high energy cut

data=data[np.argsort(data['TIME'])] #force data to be time-sorted
time=data['TIME']
flagid=(time*10**6).astype(int) #this number will become the database index number for the fermi photos
ra=data['RA']
dec=data['DEC']
energy=data['ENERGY'].astype(float)
inc=data['THETA'].astype(float)
acos=np.cos(inc)
con=data['CONVERSION_TYPE'].astype(int)
#get error from psf calculationn script
err=np.degrees(geterr(energy,acos,con))

#open satellite file to get satellite position information
raw=pf.open(sc0)
scdat0=raw[1].data
raw.close()
raw=pf.open(sc1)
scdat1=raw[1].data
raw.close()

scdat=np.concatenate((scdat0,scdat1))

del raw

#get parameters from sc file
start=scdat['START']
stop=scdat['STOP']
lat=scdat['LAT_GEO']
lon=scdat['LON_GEO']
alt=scdat['RAD_GEO']
raz=scdat['RA_SCZ']
decz=scdat['DEC_SCZ']


#get datetime of first processed event
base=datetime(2015,04,06,7,59,57) #datetime of fermi second
early=time[0]-10 #10 seconds before first event
earlydt=timedelta(seconds=(early-450000000))+base #converted to datetime

#filter ids so there are no duplicates
n=1
while n<len(flagid):
    if flagid[n-1]==flagid[n]:
        flagid[n]+=1
        print 'inc',n
    n+=1

db=mdb.connect(user=user,host=host, passwd=password,db=dbname)
c=db.cursor()

c.execute('''SELECT id,RA,time_msec FROM event WHERE eventStreamConfig_stream=23 and time >= %s''', (earlydt,))

ids=np.array(c.fetchall())

db.close()



#filter find events not already in database
#need a safety in case this call returns nothing
if len(ids)==0:
    news=np.invert(np.in1d(flagid,ids))

else:
    news=np.invert(np.in1d(flagid,ids[:,0])) #this is an inverse mask
#it will select only the relevant items from the necessary array

#now apply antimask to the relevant arrays
time=time[news]
flagid=flagid[news]
ra=ra[news]
dec=dec[news]
energy=energy[news]
inc=inc[news]
con=con[news]
err=err[news]

#check to make sure these are not empty
if len(time)==0:
    print "nothing new to write, we're done here"
    sys.exit()



#now we call the function to write all of these new events into DB


#if there are more than 10000 events to write, write them in chunks of 10000

n=0
dn=10000
while n+dn<len(time):
    np=n+dn
    block=fermiwrite(user,password,host,time[n:np],flagid[n:np],ra[n:np],dec[n:np],energy[n:np],inc[n:np],con[n:np],start,stop,raz,decz,lat,lon,alt)
    n+=dn
    print n
#now write the last chunk (or only chunk if fewer than 10000 events)
block=fermiwrite(user,password,host,time[n:],flagid[n:],ra[n:],dec[n:],energy[n:],inc[n:],con[n:],start,stop,raz,decz,lat,lon,alt)
