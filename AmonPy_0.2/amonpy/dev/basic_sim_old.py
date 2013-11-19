#basic_sim.py
"""@package basic_sim_old
Old module for running basic simulations 
for triggering observatories.
Assumptions:
1. Circular FOV
2. Constant event rate across FOV
3. Fixed error for PSF
4. Observatory is not moving 
5. No skymap is used (i.e. analytic PSF)
"""

from datetime import datetime, timedelta
from numpy import math
import random
import sidereal_m as sidereal
import ast


class SimEvent(object):
    max_streams = 100
    num_events  = [0]*max_streams
    def __init__(self,config):
        pi = math.pi
        
        psf             =  ast.literal_eval(config.psf)
        fov             =  ast.literal_eval(config.fov)           
        bckgr           =  ast.literal_eval(config.bckgr)
         
        self.stream 	=  config.stream
        self.id 		=  SimEvent.num_events[self.stream]                           
        self.rev 		=  0                          
        self.datetime 	=  config.validStart + timedelta(0.,random.uniform(0,config.duration))   
        self.nevents	=  1 
        self.deltaT		=  0.0
        self.sigmaT		=  0.0
        self.false_pos	=  bckgr['false_pos']
        self.pvalue     =  1.0
        self.observing	=  1
        self.trigger	=  1
        self.type		= 'sim'	     
        self.point_RA	=  0.   # fix this later
        self.point_dec	=  0.   # fix this later
        self.longitude	=  fov['lon']
        self.latitude	=  fov['lat']
        self.sigmaR     =  psf['sigma']
        self.elevation	=  0.       
        self.skymap     =  False	
        self.az         =  random.uniform(0., 360.)
        coszcut         =  math.cos(math.radians(fov['zencut']))
        # test to see if the observatory is looking below the horizon
        point_sign      = 1 - 2*(config.point_type == 'GEO-UPGOING') 
        self.alt        = point_sign*(90. - math.degrees(math.acos(random.uniform(coszcut,1.))))
                         
        SimEvent.num_events[self.stream] +=1 
    def __del__(self):	
        SimEvent.num_events[self.stream] -=1
    def forprint(self):
        for attr, value in self.__dict__.iteritems():
            #print attr, value
            print attr.ljust(20,' ')+': ', value
    @property
    def jday(self):
        return sidereal.JulianDate.fromDatetime(self.datetime).j
    @property
    def GST(self):
        return sidereal.SiderealTime.fromDatetime(self.datetime)
    @property
    def LST(self):
        return self.GST.lst(math.radians(self.longitude))
    @property
    def AltAz(self):
        return sidereal.AltAz(math.radians(self.alt),math.radians(self.az))
    @property
    def LatLon(self):
        return sidereal.LatLon(math.radians(self.latitude),math.radians(self.longitude))
    @property
    def raDec(self):
        return self.AltAz.raDec(self.LST,self.LatLon)
    @property
    def RA(self):
        return math.degrees(self.raDec.ra)
    @property
    def dec(self):
        return math.degrees(self.raDec.dec)          
    


    
    
    
