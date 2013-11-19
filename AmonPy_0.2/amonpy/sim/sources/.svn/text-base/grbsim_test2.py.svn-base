from grbsim import Universe, Population, Source, Spectrum
import matplotlib.pyplot as plt

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
    print 'Normalization methods: ', P.phi_norm, P.phi_norm2, P.R_norm
    
    # use a single example spectrum for W&P 2010
    alpha = -1.0
    beta  = -2.25
    Epeak = 0.511 # MeV
    spec = Spectrum(Epeak,alpha,beta)
    
    # create some sources belonging to the population
    sources = []
    Nsources = 10000
    Nztrials = 0
    NLtrials = 0
    print
    for kk in xrange(Nsources):
        src = Source(1.0,P,spec)
        #print src.z, src.L, src.Eflux, src.Nflux
        sources +=[src]
        Nztrials += src.ztrials
        NLtrials += src.Ltrials
        
    # calculate acceptance-rejection statistics
    zeff = float(Nsources)/float(Nztrials)*100
    Leff = float(Nsources)/float(NLtrials)*100
    print
    print 'Efficiency of acceptance-rejection methd for z: ', zeff,'%'
    print 'Efficiency of acceptance-rejection methd for L: ', Leff,'%'
    

    #Redshift for the sources
    S_Z = [sources[ii].z for ii in xrange(Nsources)]
    
    Npoints = 100    # for the theoretical line
    Nbins = 50       # for the histogram
    step1 = (P.zf - P.zi)/float(Npoints)
    step2 = (P.zf - P.zi)/float(Nbins)
    
    
    #Theorical line
    x = [ii*step1 for ii in xrange(Npoints+1)]
    Norm = P.R_norm    # much faster if we just calculate this once
    y = [Nsources*P.R(xi)/Norm*step2 for xi in x]
        
    # histogram    
    plt.hist(S_Z,Nbins)
    plt.plot(x,y, 'DarkOrange')
    plt.ylabel('Number of expected sources')
    plt.xlabel('Redshift')
    plt.title('Distribution of Observed GRBs')
    plt.legend(['Theoretical', 'Simulation'], loc='upper right')
    plt.grid(True)
    plt.show()      