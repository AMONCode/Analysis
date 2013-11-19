#amon_plot.py
"""@package amon_plot 
    This code is a collection of plotting modules
    designed for analyzing AMON data
    Imput key plot number and stream number (default 1, 0)
    key=1 : plot deltaT for the events in a given stream
    key=2 : plot a skypmap for the events in a given stream
    other keys: not supported yet
    stream=0 : IceCube
    stream=1 : ANTARES 
    stream=3 : Auger
    stream=7 : HAWC
   
    Insert your parameters in the code instead of these:
    
    HostFancyName='db.hpc.rcc.psu.edu'
    UserFancyName='username'
    PasswordFancy='password' 
    DBFancyName  ='AMON_test2'
    
"""

import sys
sys.path.append('../dbase')
import db_read
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
from time import time
from numpy import *
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap

plt.ion() # interactive mode

try:
    key = int(sys.argv[1])
    EventStream=int(sys.argv[2])
except:
    key = 1
    EventStream = 0
print key
print EventStream
# Might get these from sys.argv on a future iteration of the code
start = datetime(2012,1,1,0,0,0,0)
stop  = datetime(2013,1,1,0,0,0,0)
TimeSlice = timedelta.total_seconds(stop - start)
TimeStart = str(start)
TimeStop  = str(stop)

# set up the database connection, enter your username and password
HostFancyName='db.hpc.rcc.psu.edu'
UserFancyName='username'
PasswordFancy='password' 
DBFancyName  ='AMON_test2'

# read events from the database
t1 = time()
events=db_read.read_event_timeslice(TimeStart,TimeSlice,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
t2 = time()
print
print len(events), 'events have been read from the database' 
print 'read time (s): ', t2-t1
print

# put events in temporal order
events = sorted(events,key=attrgetter('datetime'))
Nevents = len(events)
NeventsStream=0
kk=0
if (key & 2**kk):
    print 'Creating plot type: ', kk
    #deltaT=[timedelta.total_seconds(events[ii+1].datetime \
    #        -events[ii].datetime) for ii in xrange(Nevents-1)]
    deltaT=[]
    eventSelect=[]
    count=0
    for event in events:
        if (event.stream==EventStream):
            eventSelect+=[event]
    NeventsStream=len(eventSelect)       
    deltaT=[timedelta.total_seconds(eventSelect[ii+1].datetime \
            -eventSelect[ii].datetime) for ii in xrange(NeventsStream-1)]        
            
    print 'Number of events selected:', NeventsStream
    bins = [ii for ii in xrange(1001)]
    plt.hist(deltaT,bins=bins)
    Rtot = NeventsStream/TimeSlice
    print 'Overlaying prediction (red) for rate (Hz): ', Rtot
    x = [ii for ii in xrange(1001)]
    y = [NeventsStream*(exp(-Rtot*(ii))-exp(-Rtot*(ii+1))) for ii in xrange(1001)]
    plt.plot(x,y,color='red',linewidth=2)
    plt.ylabel('Number')
    plt.xlabel('deltaT (sec)')
    plt.show()
    plt.show() # for some reason I needed to do this twice on isis
    junk= raw_input('hit any key to continue')
    print ''
    

kk=1
if (key & 2**kk):
    print 'Creating plot type: ', kk
    list_RA=[]
    list_Dec=[]
                                  
    for event in events:
        x=str(event.datetime) 
        pos=x.index(".")
        x=x[0:pos]
        t=datetime.strptime(x, "%Y-%m-%d %H:%M:%S")
        tt=t.timetuple()

        if (event.stream==EventStream):
            list_RA+=[event.RA]
            list_Dec+=[event.dec]


    # draw map with markers for float locations
    m = Basemap(projection='hammer',lon_0=180)
    x, y = m(list_RA,list_Dec)
    m.drawmapboundary(fill_color='#99ffff')
   #m.fillcontinents(color='#cc9966',lake_color='#99ffff')
    m.scatter(x,y,3,marker='o',color='k')
    plt.title('Locations of events for stream')
        
    plt.show()
    # add code here

    junk= raw_input('hit any key to continue')
    print ''    

kk=2
if (key & 2**kk):
    print 'Creating plot type: ', kk

    # add code here
    
    junk= raw_input('hit any key to continue')
    print ''

kk=3
if (key & 2**kk):
    print 'Creating plot type: ', kk

    # add code here
    
    junk= raw_input('hit any key to continue')
    print ''


kk=4
if (key & 2**kk):
    print 'Creating plot type: ', kk

    # add code here
    
    junk= raw_input('hit any key to continue')
    print ''


    
