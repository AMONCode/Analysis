"""@package cluster
Module defining analysis class objects for clustering. 
Clustring requires specific assumptions about time cuts
and the point spread function (PSF).
"""

import sys
from datetime import datetime, timedelta
from numpy import array, dot, math
from math import *
sys.path.append('../tools')
from convert_celest import *

class Fisher(object):
    """Analysis class object that uses the Fisher PSF
    In particular, the Fisher PSF is axially symmetric with
    a single parameter sigma. The small angle limit of Fisher
    gives the 2D Gaussian on the plane.

    Current version of the code only tests for clustering of
    pairs of events, but can be generalized in the future.

    Inputs: ev1, ev2 (a pair of event class objects)
    
    Instances of the Fisher class contain methods that are
    useful for interpretting the relative position on the
    two event. 
    """
    num=0
    def __init__(self,ev1,ev2):
        Fisher.num +=1
        self.ev1 = ev1
        self.ev2 = ev2
    def __del__(self):
        Fisher.num -=1

    # unit vector of first event
    @property
    def x1(self):
        return radec2vec(self.ev1.RA,self.ev1.dec)
    # unit vector of the second event
    @property 
    def x2(self):
         return radec2vec(self.ev2.RA,self.ev2.dec)
    # cosine of angle between events
    @property
    def cospsi(self):
        return dot(self.x1,self.x2)
    # angle between event
    @property
    def psi(self):
        return math.degrees(math.acos(self.cospsi))
    # Position uncertainties combined in quadrature
    @property
    def sigmaQ(self):
        return ((self.ev1.sigmaR)**2 + (self.ev2.sigmaR)**2)**0.5
    # Position uncertainties combined as they would for a weighted sum 
    @property
    def sigmaW(self):
        return ((self.ev1.sigmaR)**(-2) + (self.ev2.sigmaR)**(-2))**(-0.5)
    # Number of sigma the two events are apart (using qudrature)
    @property
    def Nsigma(self):
        #return self.psi/self.sigmaQ
        return (2.*(1.-self.cospsi))**0.5/math.radians(self.sigmaQ)
    # Best fit location for a postulated common source
    @property
    def x0(self):
        w = self.x1/self.ev1.sigmaR**2 + self.x2/self.ev2.sigmaR**2
        norm = (dot(w,w))**0.5
        return w/norm
    # RA and dec of the best fit location
    @property
    def radec0(self):
        return vec2radec(self.x0)
    @property
    def ra0(self):
        return self.radec0['ra']
    @property
    def dec0(self):
        return self.radec0['dec']
    # Angle between the best fit locaton and the first event
    @property   
    def psi1(self):
        cospsi1 = dot(self.x0,self.x1)
        return math.degrees(acos(cospsi1))
    # Angle between the best fit location and the second event
    @property  
    def psi2(self):
        cospsi2 = dot(self.x0,self.x2)
        return math.degrees(acos(cospsi2))   
    
class Fisher_tp(object):
    """Analysis class object that uses the Fisher PSF
    In particular, the Fisher PSF is axially symmetric with
    a single parameter sigma. The small angle limit of Fisher
    gives the 2D Gaussian on the plane.

    Current version of the code only tests for clustering of
    pairs of events, but can be generalized in the future.

    Inputs: ev1, ev2, ev3 (a triplet of event class objects)
    
    Instances of the Fisher class contain methods that are
    useful for interpretting the relative position on the
    two event. 
    """
    num=0
    def __init__(self,ev1,ev2, ev3):
        Fisher.num +=1
        self.ev1 = ev1
        self.ev2 = ev2
        self.ev3 = ev3
    def __del__(self):
        Fisher.num -=1

    # unit vector of first event
    @property
    def x1(self):
        return radec2vec(self.ev1.RA,self.ev1.dec)
    # unit vector of the second event
    @property 
    def x2(self):
         return radec2vec(self.ev2.RA,self.ev2.dec)
    # unit vector of the third event
    @property 
    def x3(self):
         return radec2vec(self.ev3.RA,self.ev3.dec)
    # cosine of angle between events
    @property
    def cospsi(self):
        return dot(self.x1,self.x2)
    # cosine of angle between events
    @property
    def cospsi_2(self):
        return dot(self.x1,self.x3)   
    # cosine of angle between events
    @property
    def cospsi_3(self):
        return dot(self.x2,self.x3)     
    # angle between event
    @property
    def psi(self):
        return math.degrees(math.acos(self.cospsi))
    # angle between event
    @property
    def psi_2(self):
        return math.degrees(math.acos(self.cospsi_2)) 
    # angle between event
    @property
    def psi_3(self):
        return math.degrees(math.acos(self.cospsi_3))    
    # Position uncertainties combined in quadrature
    @property
    def sigmaQ(self):
        return ((self.ev1.sigmaR)**2 + (self.ev2.sigmaR)**2 + (self.ev3.sigmaR)**2)**0.5
    # Position uncertainties combined as they would for a weighted sum 
    @property
    def sigmaW(self):
        return ((self.ev1.sigmaR)**(-2) + (self.ev2.sigmaR)**(-2) + \
               (self.ev3.sigmaR)**(-2))**(-0.5)
    # Number of sigma the two events are apart (using qudrature)
    @property
    def Nsigma(self):
        #return self.psi/self.sigmaQ
        return (2.*(1.-self.cospsi))**0.5/math.radians(self.sigmaQ)
    # Number of sigma the two events are apart (using qudrature)
    @property
    def Nsigma_2(self):
        #return self.psi/self.sigmaQ
        return (2.*(1.-self.cospsi_2))**0.5/math.radians(self.sigmaQ)
    @property
    def Nsigma_3(self):
        #return self.psi/self.sigmaQ
        return (2.*(1.-self.cospsi_3))**0.5/math.radians(self.sigmaQ)          
    # Best fit location for a postulated common source
    @property
    def x0(self):
        w = self.x1/self.ev1.sigmaR**2 + self.x2/self.ev2.sigmaR**2 + \
            self.x3/self.ev3.sigmaR**2
        norm = (dot(w,w))**0.5
        return w/norm
    # RA and dec of the best fit location
    @property
    def radec0(self):
        return vec2radec(self.x0)
    @property
    def ra0(self):
        return self.radec0['ra']
    @property
    def dec0(self):
        return self.radec0['dec']
    # Angle between the best fit locaton and the first event
    @property   
    def psi1(self):
        cospsi1 = dot(self.x0,self.x1)
        return math.degrees(acos(cospsi1))
    # Angle between the best fit location and the second event
    @property  
    def psi2(self):
        cospsi2 = dot(self.x0,self.x2)
        return math.degrees(acos(cospsi2))
    # Angle between the best fit location and the third event
    @property  
    def psi3(self):
        cospsi3 = dot(self.x0,self.x3)
        return math.degrees(acos(cospsi3))    

        
