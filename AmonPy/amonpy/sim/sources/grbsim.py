from __future__ import division
from __future__ import print_function
from builtins import range
from builtins import object
from scipy import integrate
import math
import random


############## Universe Class ################
class Universe(object):
    def __init__(self,h,omegam,omegak,omegae):
        self.h      = h
        self.omegam = omegam
        self.omegak = omegak
        self.omegae = omegae
        self.c      = 299792458.
        self.Mpc2cm = 3.08567758e24 
        self.erg2MeV= 624150.934

    # Hubble distance (constant for a given universe)
    @property         
    def D_H(self):
        H_0= self.h*100.0
        c_km_s= self.c/1000.
        return c_km_s/H_0
  
    # two useful functions of z
    def E(self,z):
        return math.sqrt(self.omegam*(1+z)**3 + self.omegak*(1+z)**2 + self.omegae)
    def g(self,z):
        return 1/self.E(z)
  
    # comoving distance as a function of z	
    def D_C(self,z):
        myint=integrate.quad(self.g,0,z)      #Comoving distance integration
        return self.D_H*myint[0] 
        
    # transverse comoving distance as a function of z
    def D_M(self,z):  
        if self.omegak>0:
            const= self.D_H*(1./math.sqrt(self.omegak))
            const2= math.sqrt(self.omegak)*(self.D_C(z)/self.D_H)
            return const*math.sinh(const2)
        elif self.omegak<0:
            #const= self.D_H*(1./math.sqrt(self.omegak))
            const2= math.sqrt(math.fabs(self.omegak))*(self.D_C(z)/self.D_H)
            return const*math.sin(const2)
        else:
            return self.D_C(z)
             
    # luminosity distance as a function of z
    def D_L(self,z):             
        return (1+z)*self.D_M(z)
        
    # angular distance as a function of z
    def D_A(self,z): 
        return self.D_M(z)/(1+z)  
    
    # differential comoving volume
    def dV_dz(self,z):
        return 4*math.pi*self.D_H*(1+z)**2/self.E(z)*self.D_A(z)**2

    
############## Population Class ################
class Population(object):    
    def __init__(self,rho0,zi,zf,z1,n1,n2,logLi,logLf,logL1,alpha,beta,U):
    
        self.U = U
    
        # parameters of the redshift distribution 
        self.rho0  = rho0 
        self.zi    = zi
        self.zf    = zf
        self.z1    = z1
        self.n1    = n1
        self.n2    = n2
        
        # parameters of the luminosity distribution
        self.logLi = logLi
        self.logLf = logLf
        self.logL1 = logL1
        self.alpha = alpha
        self.beta  = beta         
    
    # intrinsic redshift distribution (unnormalized)
    def rgrb(self,z):
        if (z <= self.z1 and z >= self.zi):
            return (1+z)**self.n1
        elif (z > self.z1 and z <= self.zf):
            return (1.+self.z1)**(self.n1-self.n2) * (1+z)**self.n2
        else:
            return 0.0
    
    # rate of GRBs after taking into account expansion of Universe
    
    def R(self,z):
        return self.rgrb(z)/(1+z)*self.U.dV_dz(z)
    
    # intrinsic luminosity distribution (unnormalized)
    def phi(self,logL):
        if (logL <= self.logL1 and logL >= self.logLi):
            return 10.**(-self.alpha*(logL-self.logL1))
        elif (logL > self.logL1 and logL <= self.logLf):
            return 10.**(-self.beta*(logL-self.logL1))
        else:
            return 0.0
            
    # normalization of phi (not needed for acceptance-rejection method)
    # should check my math before using this
    @property        
    def phi_norm(self):
        term1 = (10.**(-self.alpha*(self.logLi-self.logL1))-1.)/(self.alpha*math.log(10.))
        term2 = (1.-10.**(-self.beta*(self.logLf-self.logL1)))/(self.beta*math.log(10.))
        return term1 + term2
    
    @property     
    def phi_norm2(self):
        myint=integrate.quad(self.phi,self.logLi,self.logLf)
        return myint[0] 
        
    @property
    def R_norm(self):
        myint=integrate.quad(self.R,self.zi,self.zf)
        return myint[0]     
    
############## Spectrum Class ################    
class Spectrum(object):
    def __init__(self,Epeak,alpha,beta):
        self.Epeak = Epeak # in source frame
        self.alpha = alpha
        self.beta  = beta 
        self.E1    = 1e-3   # MeV (top of reference band)
        self.E2    = 10.    # MeV (bottom of reference band)
        self.Eref  = 0.1    # MeV
        self.Emin  = 0.015  # MeV (bottom of BAT band)
        self.Emax  = 0.150  # MeV (top of BAT band)
        self.int1  = self.G(self.E1,self.E2)
        self.int2  = self.F(self.Emin,self.Emax)
        self.Cdet  = self.int1/self.int2
            
    @property 
    def Ebreak(self):
        return (self.alpha - self.beta)*self.Epeak/(2+self.alpha)
    
    def f(self,E):
        if (E <= self.Ebreak and E > 0.):
            return (E/self.Eref)**self.alpha*math.exp(-E*(2+self.alpha)/self.Epeak)
        elif (E > self.Epeak):
            return (E/self.Eref)**self.beta*math.exp(self.beta-self.alpha)  \
                   *(self.Ebreak/self.Eref)**(self.alpha-self.beta)
        else:
            return 0.0

    def g(self,E):
        return E*self.f(E) 
    
    def F(self,E1,E2):
        myint=integrate.quad(self.f,E1,E2) 
        return myint[0]
 
    def G(self,E1,E2):
        myint=integrate.quad(self.g,E1,E2) 
        return myint[0]       

    def k(self,z):
        return self.int2/self.F((1+z)*self.Emin,(1+z)*self.Emax)    
    
    
############## Source Class ################    
class Source(object):
    def __init__(self,z,P,spec): 
        
        self.P = P
        self.spec = spec
        
        # run a simulation for z and L
        z, ztrials    = self.zsim()       
        logL, Ltrials = self.logLsim()
        
        # store simulation results in the object
        self.z        = z
        self.logL     = logL
        self.ztrials  = ztrials
        self.Ltrials  = Ltrials
        
    # luminosity (rather than log-luminosity)
    @property
    def L(self):
        return 10.**self.logL    

    # acceptance-rejection method for simulating z
    def zsim(self):
        accept = False
        trials = 0
        while not accept:
            trials +=1
            ran1 = random.uniform(0.0,1.0)
            z = self.P.zi + ran1*(self.P.zf-self.P.zi)
            ran2 = random.uniform(0.0,1.0)
            if ran2 < self.P.R(z)/self.P.R(self.P.z1):  # assume function peaks at z1
                accept = True
        return (z, trials)   
 
    # acceptance-rejection method for simulating logL (might be slow)
    def logLsim(self):
        accept = False
        trials = 0
        while not accept:
            trials +=1
            ran1 = random.uniform(0.0,1.0)
            logL = self.P.logLi + ran1*(self.P.logLf-self.P.logLi)
            ran2 = random.uniform(0.0,1.0)
            if ran2 < self.P.phi(logL)/self.P.phi(self.P.logLi):  # assume function peak at Li
                accept = True
        return (logL,trials)   
    
    # luminosity distance for this source
    @property
    def D_L(self): 
        return self.P.U.D_L(self.z)

    # peak energy flux for this source with units erg.cm^{-2}.s^{-1}
    # totalled over all energy (so does not account for BAT energy band)
    @property
    def Eflux(self):
        return self.L/4*math.pi/(self.P.U.Mpc2cm*self.D_L)**2
        
    @property
    def Nflux(self):
        return self.P.U.erg2MeV*self.Eflux/(1+self.z)/self.spec.k(self.z)/self.spec.Cdet
                
        
############## Test code ################    
if __name__ == "__main__": 

    # make a universe
    U = Universe(0.7,0.27,0.0,0.71)
 
    # parameters of redshift distribution of the population (best fit W&P 2010)
    rho0  =  1.3   # Gpc^{-3}yr^{-1} 
    zi    =  0.0
    zf    =  10.0
    z1    =  3.1
    n1    =  2.1
    n2    = -1.4
    
    # parameters of the luminosity distribution of the population (best fit W&P 2010)
    logLi =  50.0
    logLf =  54.0
    logL1 =  52.5
    alpha =  0.2
    beta  =  1.4
    
    # make a population of GRBs
    P = Population(rho0,zi,zf,z1,n1,n2,logLi,logLf,logL1,alpha,beta,U)
    print('Normalization methods: ', P.phi_norm, P.phi_norm2, P.R_norm)
    
    # create some sources belonging to the population
    sources = []
    Nsources = 10
    Nztrials = 0
    NLtrials = 0
    print()
    # use a single example spectrum for W&P 2010
    alpha = -1.0
    beta  = -2.25
    Epeak = 0.511 # MeV
    spec = Spectrum(Epeak,alpha,beta)
    
    for kk in range(Nsources):
        src = Source(1.0,P,spec)
        print(src.z, src.L, src.Eflux, src.ztrials, src.Ltrials)
        sources +=[src]
        Nztrials += src.ztrials
        NLtrials += src.Ltrials
        
    # calculate acceptance-rejection statistics
    zeff = float(Nsources)/float(Nztrials)*100
    Leff = float(Nsources)/float(NLtrials)*100
    print()
    print('Efficiency of acceptance-rejection methd for z: ', zeff,'%')
    print('Efficiency of acceptance-rejection methd for L: ', Leff,'%')    
     
    # make list of z values and then...     
    #y = P.R(z)/P.R_norm   
    
    
    

