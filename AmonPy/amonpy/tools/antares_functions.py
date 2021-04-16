import numpy as np
import os


antBkgfile = os.path.join(AmonPyDir,'data/antares/antares_bkg1_intp.npy')
antBkg = np.load(antBkgfile, encoding = 'latin1',allow_pickle=True).item()

def probBkgANTARES(dec):
    """Spatial Bkg PDF for a Antares hotspot. Based on data """
    #return antBkg(dec)*180./(np.pi*2*np.pi)
    return antBkg(np.sin(np.deg2rad(dec)))*180./(np.pi*2*np.pi)

def probSigANTARES(spc,sigma=0.69):
    """Spatial Signal PDF for a Antares hotspot. Assumes a gaussian function over the sphere. """
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*(np.deg2rad(sigma)**2))
    return psf

def pNuCluster(events,rate=1.686e-5):
    """
    Function to calculate the probabiliyt of observing 2 or more neutrinos
    after one is already observed. Returns 1 if there's only one neutrino in
    the list.
    """
    val=1
    N=len(events)-1
    if N==1:
        return val
    else:
        lmb = 1.686e-5 * events[0][4]*2*np.pi*(1-np.cos(np.deg2rad(3.5)))/(4*np.pi) #totalRate=1.686e-5, estimated from RealTime
        val = stats.poisson.sf(N-2,lmb)
    return val

def totalpHEN(events):
    """
    Function that combines the p-values of all neutrino events.
    """
    val=1
    N=len(events)
    if N==2:
        return val*events[1][-3]
    else:
        for i in range(1,N):
            val*=events[i][-3]
        return val


