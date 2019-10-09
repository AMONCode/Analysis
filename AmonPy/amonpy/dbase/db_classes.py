"""@package db_classes
Builds the basic classes (Event, Alert, etc), that correspond to tables
in the AMON database. Some modifications from the database format are
made to enable use of python features
"""
from __future__ import print_function

#from numpy import *
from builtins import object
from operator import itemgetter, attrgetter
from datetime import datetime, timedelta
import random
import ast

# amonpy imports
from amonpy.sim import sidereal_m as sidereal


# ******************* BEGIN event class definition **********************

# class factory for the WhereWhen base class
def wherewhen_def(*args):
    """ wherewhen_def is a class factory function
        Optional Inputs: args[0] is an object from the EventStreamConfig class
                         args[1] set to True if simulation is desired
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


# class factory for the Event class
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
                     'false_pos','pvalue','type','point_RA','point_dec',
                     'longitude','latitude','elevation','psf_type',
                     'configstream')
        _max_streams = 1010
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
                #self.point_RA  =  0.0
                #self.point_dec  =  0.0
                self.pvalue    =  1.0
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
                    print(attr.ljust(20,' '), value)
                except:
                    print(attr.ljust(20,' '), 'Empty slot')

    return Event

# create the generic version
# which can be overwritten by the parent code
Event = event_def()



# ******************* BEGIN alert class definition **********************
# create a generic alert object for AMON

class Alert(object):
    """ Creates the Alert class. Instances are created by specifying a unique
        triple of IDs (stream, id, rev). The other data attributes are set to
        defaults on init. This style may later be replaced by the class
        factory and __slots__ approach, currently adopted for the Event
        class (see above). However since Alerts are uncommon, they do not
        require the same level of optimization.
    """
    num_alerts = 0
    def __init__(self,stream,id,rev):
        self.stream 	=  stream                       # defined by input
        self.id 	=  id                           # defined by input
        self.rev 	=  rev                          # defined by input
        # remainder of data attributes are defaults
        self.datetime 	=  datetime(2000,1,1,0,0,0,1)
        self.RA		= -1.0
        self.dec 	=  0.0
        self.sigmaR     =  0.0
        self.nevents	=  0.0
        self.deltaT	=  0.0
        self.sigmaT     =  0.0
        self.false_pos	=  0.0
        self.observing	=  0
        self.trigger	=  0
        self.type	= 'test'
        self.pvalue     = 0.0
        self.skymap     = False
        self.anarev	= 0
        Alert.num_alerts +=1

    def __del__(self):
        Alert.num_alerts -=1

    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)




# *************************************************************************


class EventStreamConfig(object):
    """ Creates the EventStreamConfig class. Instances are created by
        specifying a unique double of IDs (stream, rev). We use the same
        style of class definition as the Alert class
    """
    num_configs = 0
    def __init__(self,stream,rev):
        self.stream             = stream
        self.rev                = rev
        self.observ_name        = ''
        self.validStart         = datetime(2000,1,1,0,0,0,1)
        self.validStop          = datetime(2001,1,1,0,0,0,1)
        self.observ_coord_sys   = ''
        self.astro_coord_sys    = ''
        self.point_type         = ''
        self.point              = ''
        self.param1Desc         = ''
        self.param2Desc         = ''
        self.param3Desc         = ''
        self.psf_type           = ''
        self.psf                = ''
        self.skymap_val1Desc    = ''
        self.skymap_val2Desc    = ''
        self.skymap_val3Desc    = ''
        self.sensitivity_type   = ''
        self.sensitivity        = ''
        self.fov_type           = ''
        self.fov                = ''
        self.ephemeris          = ''
        self.bckgr_type         = ''
        self.bckgr              = ''
        self.mag_rigidity       = ''
        EventStreamConfig.num_configs +=1
    def __del__(self):
        EventStreamConfig.num_configs -=1
    @property
    def duration(self):
        return timedelta.total_seconds(self.validStop - self.validStart)
    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)



def simstream(stream):
    """ Some examples of the EventStreamConfig class which are used to
        demonstrate simulations for AmonPy v0.1
    """
    rev = 0
    config = EventStreamConfig(stream,rev)

    # A toy model for IceCube
    if  (stream == 0):
        config.observ_name      = 'IceCube'
        config.validStart       = datetime(2012,1,1,0,0,0,0)
        config.validStop        = datetime(2013,1,1,0,0,0,0)
        #config.validStop        = datetime(2013,1,1,0,0,0,0)
        config.observ_coord_sys = 'UTC-GEOD-TOPO'
        config.astro_coord_sys  = 'UTC-ICRS-TOPO'
        config.point_type       = 'GEO-UPGOING'
        config.point            = ''
        config.param1Desc       = 'Energy (GeV)'
        config.param2Desc       = ''
        config.param3Desc       = ''
        config.psf_type         = 'Fisher_FixedSigma'
        config.psf              = '{"sigma":0.8}'
        config.skymap_val1Desc  = ''
        config.skymap_val2Desc  = ''
        config.skymap_val3Desc  = ''
        config.sensitivity_type = ''
        config.sensitivity      = ''
        config.fov_type         = 'circle'
        config.fov              = '{"lon":0.0,"lat":-90.0,"zencut":90.0}'
        config.ephemeris        = ''
        config.bckgr_type       = 'constant'
        config.bckgr            = '{"false_pos":0.0004438}' # s^{-1}sr^{-1}
        config.mag_rigidity     = ''

    # A toy model for ANTARES
    elif (stream == 1):
        config.observ_name      = 'ANTARES'
        config.validStart       = datetime(2012,1,1,0,0,0,0)
        config.validStop        = datetime(2013,1,1,0,0,0,0)
        config.observ_coord_sys = 'UTC-GEOD-TOPO'
        config.astro_coord_sys  = 'UTC-ICRS-TOPO'
        config.point_type       = 'GEO-UPGOING'
        config.point            = ''
        config.param1Desc       = 'Energy (GeV)'
        config.param2Desc       = ''
        config.param3Desc       = ''
        config.psf_type         = 'Fisher_FixedSigma'
        config.psf              = '{"sigma":1.4}'
        config.skymap_val1Desc  = ''
        config.skymap_val2Desc  = ''
        config.skymap_val3Desc  = ''
        config.sensitivity_type = ''
        config.sensitivity      = ''
        config.fov_type         = 'circle'
        config.fov              = '{"lon":6.17,"lat":42.8,"zencut":90.0}'
        config.ephemeris        = ''
        config.bckgr_type       = 'constant'
        config.bckgr            = '{"false_pos":0.0001463}' # s^{-1}sr^{-1}
        config.mag_rigidity     = ''

    # A toy model for Auger
    elif (stream == 3):
        config.observ_name      = 'Auger'
        config.validStart       = datetime(2012,1,1,0,0,0,0)
        config.validStop        = datetime(2013,1,1,0,0,0,0)
        config.observ_coord_sys = 'UTC-GEOD-TOPO'
        config.astro_coord_sys  = 'UTC-ICRS-TOPO'
        config.point_type       = 'GEO'
        config.point            = ''
        config.param1Desc       = 'Energy (GeV)'
        config.param2Desc       = ''
        config.param3Desc       = ''
        config.psf_type         = 'Fisher_FixedSigma'
        config.psf              = '{"sigma":1.2}'
        config.skymap_val1Desc  = ''
        config.skymap_val2Desc  = ''
        config.skymap_val3Desc  = ''
        config.sensitivity_type = ''
        config.sensitivity      = ''
        config.fov_type         = 'circle'
        config.fov              ='{"lon":-69.3114,"lat":-35.4667,"zencut":90.0}'
        config.ephemeris        = ''
        config.bckgr_type       = 'constant'
        config.bckgr            = '{"false_pos":0.0012104}' # s^{-1}sr^{-1}
        config.mag_rigidity     = ''

    # A toy model for HAWC
    elif (stream == 7):
        config.observ_name      = 'HAWC'
        config.validStart       = datetime(2012,1,1,0,0,0,0)
        config.validStop        = datetime(2013,1,1,0,0,0,0)
        config.observ_coord_sys = 'UTC-GEOD-TOPO'
        config.astro_coord_sys  = 'UTC-ICRS-TOPO'
        config.point_type       = 'GEO'
        config.point            = ''
        config.param1Desc       = 'Energy (GeV)'
        config.param2Desc       = ''
        config.param3Desc       = ''
        config.psf_type         = 'Fisher_FixedSigma'
        config.psf              = '{"sigma":1.0}'
        config.skymap_val1Desc  = ''
        config.skymap_val2Desc  = ''
        config.skymap_val3Desc  = ''
        config.sensitivity_type = ''
        config.sensitivity      = ''
        config.fov_type         = 'circle'
        config.fov              = '{"lon":-97.3,"lat":19.0,"zencut":47.0}'
        config.ephemeris        = ''
        config.bckgr_type       = 'constant'
        config.bckgr            = '{"false_pos":0.0004119}'  # s^{-1}sr^{-1}
        config.mag_rigidity     = ''

    else:
        print('')
        print('stream ID not recognized by function simstream(stream)')
        print('')

    return config



class AlertConfig(object):
    """ Creates the AlertConfig class. Instances are created by specifying
        a unique double of IDs (stream, rev). This version is retained for
        the purposes of testing database read/write of the corresponding table.
    """
    num_configs = 0
    def __init__(self,stream,rev):
        self.stream             = stream
        self.rev                = rev
        self.validStart         = datetime(2000,1,1,0,0,0,0)
        self.validStop          = datetime(2020,1,1,0,0,0,0)
        self.participating      = 0
        self.p_thresh           = 0
        self.N_thresh           = ''
        self.deltaT             = 0
        self.cluster_method     = ''
        self.sens_thresh        = ''
        self.skymap_val1Desc    = ''
        self.skymap_val2Desc    = ''
        self.skymap_val3Desc    = ''
        self.bufferT            = 0.0
        self.R_thresh           = 0.0
        self.cluster_thresh     = 0.0
        AlertConfig.num_configs +=1
    def __del__(self):
        AlCertConfig.num_configs -=1

    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)

class AlertConfig2(object):
    """ Creates the AlertConfig2 test class. Instances are created by
        specifying a unique double of IDs (stream, rev). this version is
        used for testing the analysis code in AmonPy v0.1. Eventually, the two
        version will be unified into one.
    """
    num_configs = 0
    def __init__(self,stream,rev):
        self.stream             = stream
        self.rev                = rev
        self.participating      = 0
        self.p_thresh           = 0
        self.N_thresh           = ''
        self.deltaT             = 0.0
        self.bufferT            = 0.0   # Not in orininal AlertConfig class, but DB supports it
        self.cluster_method     = ''
        self.cluster_thresh      = 0.0   # Not in original AlertConfig class, but DB supports it
        self.sens_thresh        = ''
        self.psf_paramDesc1     = ''
        self.psf_paramDesc2     = ''
        self.psf_paramDesc3     = ''
        self.skymap_val1Desc    = ''
        self.skymap_val2Desc    = ''
        self.skymap_val3Desc    = ''
        self.validStart         = datetime(2000,1,1,0,0,0,0)
        self.validStop          = datetime(2020,1,1,0,0,0,0)
        self.R_thresh           = 0.0    # added so that DB supports this class

        AlertConfig2.num_configs +=1
    def __del__(self):
        AlertConfig2.num_configs -=1

    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)


def exAlertConfig():
    """ Returns an example AlertConfig object,
        used for testing the analysis code
    """
    stream = 1
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = 2**0 + 2**1 + 2**7  # index of event streams
    config.deltaT         = 100.00 #80000.0 #100.0               # seconds
    config.bufferT        = 86400.00 #1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 2.00 #10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc= 'N/A'
    config.skymap_val2Desc= 'N/A'
    config.skymap_val3Desc= 'N/A'
    config.N_thresh       = '{0:1,1:1,7:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2013,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

def exAlertArchivConfig():
    """ Returns an example AlertConfig object,
        used for testing the analysis code
    """
    stream = 2 # archival change this after testing 0 RT, 1 archival
    rev = 0
    config = AlertConfig2(stream,rev)
    config.participating  = 2**0 + 2**1 + 2**7  # index of event streams
    config.deltaT         = 100.00 #80000.0 #100.0               # seconds
    config.bufferT        = 86400.00 #10000.00 # 86400.00 #1000.0 86400 24 h buffer             # seconds
    config.cluster_method = 'Fisher'            # function to be called
    config.cluster_thresh = 2.00 #10.0 #2.0                 # significance
    config.psf_paramDesc1 = 'deg'
    config.psf_paramDesc2 = 'N/A'
    config.psf_paramDesc3 = 'N/A'
    config.skymap_val1Desc= 'N/A'
    config.skymap_val2Desc= 'N/A'
    config.skymap_val3Desc= 'N/A'
    config.N_thresh       = '{0:1,1:1,7:1}'
    config.sens_thresh    = 'N/A'
    config.validStart     = datetime(2012,1,1,0,0,0,0)
    config.validStop      = datetime(2013,1,1,0,0,0,0)
    config.R_thresh       = 0.0
    return config

 # ******************* BEGIN alertline class definition **********************
# create a generic alertline object for AMON

class AlertLine(object):
    """ Creates the AlertLine class. Instances created by specifying a unique
        6 IDs (stream_alert, id_alert, rev_alert, stream_event, id_event, rev_event)
    """
    num_alertlines = 0
    def __init__(self,astream,aid,arev,estream,eid,erev):
        self.stream_alert =  astream                       # defined by input
        self.id_alert 	  =  aid                           # defined by input
        self.rev_alert 	  =  arev                          # defined by input
        self.stream_event =  estream                       # defined by input
        self.id_event 	  =  eid                           # defined by input
        self.rev_event 	  =  erev                          # defined by input
        AlertLine.num_alertlines +=1        # record the addition +1 event

    def __del__(self):
        AlertLine.num_alertlines -=1

    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)

# ******************* BEGIN parameter class definition **********************
# create a generic parameter object for AMON

class Parameter(object):
    """ Creates the Parameter class. Instances are created by specifying a unique
        four of IDs (name, event_eventStreaemConfig_stream, event_id, event_rev).
        The other data attributes are set to
        defaults on init. This style may later be replaced by the class
        factory and __slots__ approach, currently adopted for the Event
        class (see above).
    """
    num_param = 0
    def __init__(self,parname,stream,id,rev):
        self.name = parname
        self.event_eventStreamConfig_stream 	=  stream                       # defined by input
        self.event_id 	=  id                           # defined by input
        self.event_rev 	=  rev                          # defined by input
        # remainder of data attributes are defaults
        self.value 	=  0.
        self.units		= "nounits"

        Parameter.num_param +=1

    def __del__(self):
        Parameter.num_param -=1

    def forprint(self):
        for attr, value in self.__dict__.items():
            #print attr, value
            print(attr.ljust(20,' ')+': ', value)
