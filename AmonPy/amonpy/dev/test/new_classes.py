from numpy import *
pi = math.pi
from operator import itemgetter, attrgetter
from datetime import datetime, timedelta
from sys import path
path.append("../dbase/")
path.append("../sim/")
from db_classes import simstream
from time import time
import random
import ast
import sidereal_m as sidereal


def wherewhen_def(*args):
    """ wherewhen_def is a class factory function
        Optional Inputs: args[0] is an object from the EventStreamConfig class
                         args[1] set to True if simulaiton is desired
        Output: returns the WhereWhen class
    """

    # identify if a configuration will be used to define defaults
    # and if simulation is requested
    try:
        config = args[0]
    except:
        config = None
    try:
        sim = args[1]
        if (sim != True): sim = False
    except:
        sim = False

    # unpack the pieces needed from config
    if (config != None):
        psf             = ast.literal_eval(config.psf)
        fov             = ast.literal_eval(config.fov)           
        stream          = config.stream
        start           = config.validStart
        dur             = config.duration
        zencut          = fov['zencut']
        point_type      = config.point_type
        coszcut         =  math.cos(math.radians(fov['zencut']))
        point_sign      = 1 - 2*(config.point_type == 'GEO-UPGOING')

    # define the WhereWhen class
    class WhereWhen(object):
        __slots__ = ('datetime','RA','dec','sigmaR','sigmaT','point_RA',
                     'point_dec','longitude','latitude','elevation')
        
        _numobj = 0
        def __init__(self):
            
            if (config != None):
                
                # define fixed data attributes
                self.sigmaR     =  psf['sigma']# const value for now
                self.sigmaT     =  0.          # dummy value for now
                self.point_RA	= -1.0         # dummy value for now
                self.point_dec	=  0.0         # dummy value for now
                self.longitude	=  fov['lon']  
                self.latitude	=  fov['lat']
                self.elevation  =  0.0         # dummy value for now
                
                # simulate datetime,RA,dec or use defualt values
                if (sim == True):
                    self.datetime =  start+timedelta(0.,random.uniform(0.,dur))
                    self.RA       =  math.degrees(self._raDec.ra)
                    self.dec      =  math.degrees(self._raDec.dec)
                else:
                    self.datetime =  datetime(2000,1,1,0,0,0)
                    self.RA       = -1.0
                    self.dec      =  0.0

            # if no config is given, just define a class with no defaults  
            else:
                pass
            
            WhereWhen._numobj +=1

        def __del__(self):
            WhereWhen._numobj -=1

        if (sim == True):
            # randomly generate azimuth and altitude
            @property
            def _az(self):
                return random.uniform(0., 360.)
            @property
            def _alt(self):
                return point_sign*(90. - math.degrees( \
                       math.acos(random.uniform(coszcut,1.))))
            # supporting calculaitons for RA and dec
            @property
            def _jday(self):
                return sidereal.JulianDate.fromDatetime(self.datetime).j
            @property
            def _GST(self):
                return sidereal.SiderealTime.fromDatetime(self.datetime)
            @property
            def _LST(self):
                return self._GST.lst(math.radians(self.longitude))
            @property
            def _AltAz(self):
                return sidereal.AltAz(math.radians(self._alt),
                                      math.radians(self._az))
            @property
            def _LatLon(self):
                return sidereal.LatLon(math.radians(self.latitude),
                                       math.radians(self.longitude))
            @property
            def _raDec(self):
                return self._AltAz.raDec(self._LST,self._LatLon)

    return WhereWhen


def event_def(*args):
    """ event_def is a class factory function
        Optional Inputs: args[0] is an object from the EventStreamConfig class
                         args[1] set to True if simulaiton is desired
        Output: returns the Event class
    """
    
    # identify if a configuration will be used to define defaults
    # and if simulation is requested
    # create the WhereWhen class accordingly 
    try:
        config = args[0]
        WhereWhen = wherewhen_def(config)
    except:
        config = None
        WhereWhen = wherewhen_def()    
    try:
        sim = args[1]
        if (sim == True):
            WhereWhen = wherewhen_def(config,True)
    except:
        sim = False

    # unpack the pieces needed from config
    if (config != None):
        bckgr     = ast.literal_eval(config.bckgr)
        false_pos = bckgr['false_pos']

    # define the Event class
    class Event(WhereWhen):
        __slots__ = ('stream','id','rev','datetime','RA','dec',
                     'sigmaR','nevents','deltaT','sigmaT',
                     'false_pos','pvalue','observing','trigger',
                     'type','point_RA','point_dec','longitude',
                     'latitude','elevation','psf_type', 'configstream')
        #_num_events = 0
        _max_streams = 100
        _num_events  = [0]*_max_streams

        def __init__(self,stream,id,rev):

            WhereWhen.__init__(self)            
            if (config != None):
                self.stream    =  config.stream
                self.id        =  Event._num_events[self.stream]
                self.rev       =  rev
                self.nevents   =  1    
                self.deltaT    =  0.0 
                self.false_pos =  false_pos
                self.pvalue    =  1.0 
                self.observing =  1 
                self.trigger   =  1
                if sim:
                    self.type  = 'sim'
                else:
                    self.type  = 'test'	      
                self.psf_type    =  'fisher' 
                self.configstream= 0.0
            else:
                self.stream    =  stream     
                self.id        =  id       
                self.rev       =  rev

            Event._num_events[self.stream]+=1
        
        def __del__(self):
            Event._num_events[self.stream] -=1

        def forprint(self):
            exattr = ['forprint']
            atlist = [attr for attr in dir(self) \
                  if not (attr.startswith('_') or attr in exattr)]
            for attr in atlist:            
                try:
                    value = getattr(self,attr)
                    print attr.ljust(20,' '), value
                except:
                    print attr.ljust(20,' '), 'Empty slot'

    return Event


# test code
if __name__ == "__main__":

    print
    print '********************TEST 1**************************'
    print 'Event class defined by Event = event_def()'
    print 'Gives empty slots for populating from the database'
    print 'stream, id, rev determined by user'
    print 
    Event  = event_def()
    event1 = Event(1,2,3)
    event1.forprint()
    #print Event._num_events
    print '**************************************************'
    print 
    
    print
    print '**********************TEST 2***********************'   
    print 'Now define Event = event_def(config)'
    print 'stream # taken from config, id from cumulative number of events,'
    print 'rev given by user, and config populates the many defaults'
    print 
    config = simstream(0) 
    Event  = event_def(config)
    event2 = Event(45,25,0)    # stream and id will be overridden
    event2.forprint()
    print
    event3 = Event(45,25,0)    # stream and id will be overridden
    event3.forprint()
    print
    print 'Note that the number of events was reset to 0 when the Event '\
          + 'class was reinitiated '
    #print Event._num_events
    print '**************************************************'      
    print

    print
    print '*************************TEST 3********************'
    print 'Fianlly, define Event = event_def(config,True)'
    print 'Which will switch on the simulation'
    print
    Event = event_def(config,True)
    event4 = Event(45,25,0)    # stream and id will be overridden
    event4.forprint()
    #print Event._num_events
    print '**************************************************'      
    print
