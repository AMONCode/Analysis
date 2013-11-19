from datetime import datetime, timedelta
import random
"""@package test_inherit
Old module for testing class inheritance. 
"""

####### Event class #######

class Event(object):

    __slots__ = ('stream','id','rev','_datetime','_RA','_dec',
                 '_sigmaR','_nevents','_deltaT','_sigmaT',
                 '_false_pos','_pvalue','_observing','_trigger',
                 '_type','_point_RA','_point_dec','_longitude',
                 '_latitude','_elevation','_skymap')
    _num_events = 0
    #_mutable = [attr for attr in __slots__ if attr[0]=='_']

    def __init__(self,stream,id,rev): 
        self.stream 	=  stream     
        self.id 	=  id       
        self.rev 	=  rev
        
        # Note the underscore (to make it "hidden")
        # Note: data attributes have no built-in "setter" method       
        self._datetime 	=  datetime(2000,1,1,0,0,0,1)
        self._RA        = -1.0                             
        self._dec 	=  0.0       
        self._sigmaR    =  0.0
        self._nevents	=  0    
        self._deltaT	=  0.0 
        self._sigmaT	=  0.0 
        self._false_pos	=  0.0
        self._pvalue    =  1.0 
        self._observing	=  0 
        self._trigger	=  0  
        self._type	= 'test'	
        self._point_RA	= -1.0
        self._point_dec	=  0.0
        self._longitude	= -1.0
        self._latitude	=  0.0
        self._elevation	=  0.0        
        self._skymap    =  False
        
        Event._num_events+=1
        
    def __del__(self):
        Event._num_events -=1

    # now we define a new (method) attribute...
    # ...which does have a built-in setter method

    @property
    def datetime(self):
        return self._datetime
    @datetime.setter
    def datetime(self,value):
        self._datetime = value
    @datetime.deleter
    def datetime(self):
        del self._datetime 

    @property
    def RA(self):
        return self._RA
    @RA.setter
    def RA(self,value):
        self._RA = value
    @RA.deleter
    def RA(self):
        del self._RA

    @property
    def dec(self):
        return self._dec
    @dec.setter
    def dec(self,value):
        self._dec = value
    @dec.deleter
    def dec(self):
        del self._dec

    @property
    def sigmaR(self):
        return self._sigmaR
    @sigmaR.setter
    def sigmaR(self,value):
        self._sigmaR = value
    @sigmaR.deleter
    def sigmaR(self):
        del self._sigmaR

    @property
    def nevents(self):
        return self._nevents
    @nevents.setter
    def nevents(self,value):
        self._nevents = value
    @nevents.deleter
    def nevents(self):
        del self._nevents

    @property
    def deltaT(self):
        return self._deltaT
    @deltaT.setter
    def deltaT(self,value):
        self._deltaT = value
    @deltaT.deleter
    def deltaT(self):
        del self._deltaT

    @property
    def sigmaT(self):
        return self._sigmaT
    @sigmaT.setter
    def sigmaT(self,value):
        self._sigmaT = value
    @sigmaT.deleter
    def sigmaT(self):
        del self._sigmaT

    @property
    def false_pos(self):
        return self._false_pos
    @false_pos.setter
    def false_pos(self,value):
        self._false_pos = value
    @false_pos.deleter
    def false_pos(self):
        del self._false_pos

    @property
    def pvalue(self):
        return self._pvalue
    @pvalue.setter
    def pvalue(self,value):
        self._pvalue = value
    @pvalue.deleter
    def pvalue(self):
        del self._pvalue    

    @property
    def observing(self):
        return self._observing
    @observing.setter
    def observing(self,value):
        self._observing = value
    @observing.deleter
    def observing(self):
        del self._observing

    @property
    def trigger(self):
        return self._trigger
    @trigger.setter
    def trigger(self,value):
        self._trigger = value
    @trigger.deleter
    def trigger(self):
        del self._trigger

    @property
    def type(self):
        return self._type
    @type.setter
    def type(self,value):
        self._type = value
    @type.deleter
    def type(self):
        del self._type

    @property
    def point_RA(self):
        return self._point_RA
    @point_RA.setter
    def point_RA(self,value):
        self._point_RA = value
    @point_RA.deleter
    def point_RA(self):
        del self._point_RA
        
    @property
    def point_dec(self):
        return self._point_dec
    @point_dec.setter
    def point_dec(self,value):
        self._point_dec = value
    @point_dec.deleter
    def point_dec(self):
        del self._point_dec

    @property
    def longitude(self):
        return self._longitude
    @longitude.setter
    def longitude(self,value):
        self._longitude = value
    @longitude.deleter
    def longitude(self):
        del self._longitude

    @property
    def latitude(self):
        return self._latitude
    @latitude.setter
    def latitude(self,value):
        self._latitude = value
    @latitude.deleter
    def latitude(self):
        del self._latitude

    @property
    def elevation(self):
        return self._elevation
    @elevation.setter
    def elevation(self,value):
        self._elevation = value
    @elevation.deleter
    def elevation(self):
        del self._elevation

    @property
    def skymap(self):
        return self._skymap
    @skymap.setter
    def skymap(self,value):
        self._skymap = value
    @skymap.deleter
    def skymap(self):
        del self._skymap

        
######### DERIVED CLASS (with simulation of some attributes) #######

class SimEvent(Event):
    def __init__(self,stream,id,rev,config):
        Event.__init__(self,stream,id,rev)

    # now decorate the setter method for datetime
    # replacing it with a function that generates random dates
    @Event.datetime.setter
    def datetime(self,value): # value is ignored
        self._datetime = config['start'] \
                       + timedelta(0.,random.uniform(0.,config['dur']))

    # The "simulate" method simply touches each unset property once
    def _simulate(self):
        self.datetime = 1


######### MAIN CODE ###############
        
print
print '*** TESTING CLASS INHERITANCE ***'
print 
print '1. Create an Event object with default datetime...'    
event = Event(1,2,3)
print 'event.datetime: ', event.datetime
print 'now set the datetime to something else...'
event.datetime = datetime(2012,1,2,3,4,5,6)
print 'event.datetime: ', event.datetime
del event

print
config = {'start':datetime(2012,1,1,0,0,0,0),
          'stop':datetime(2013,1,1,0,0,0,0),
          'dur':60**2*24*366.}
print '2. Create a derived SimEvent object with default datetime...'
print '(This is an independent object from the previous test)'
simevent = SimEvent(1,2,3,config)
print 'simevent.datetime: ', simevent.datetime

print
print '3. Now run the simulation method on the SimEvent object...'
simevent._simulate()
print 'simevent.datetime: ', simevent.datetime

print
print '4. The randomized result is unaltered by a second call...'
print 'simevent.datetime: ', simevent.datetime

print
print '5. And you can call the unhidden atributes of simevent with a loop...'
print
attrlist = [attr for attr in dir(Event) if attr[0] != '_']
for attr in attrlist:
    print attr.rjust(12,' ')+':', getattr(simevent,attr)
print

