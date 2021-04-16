import numpy as np

from amonpy.tools.angularsep import spcang

from scipy import optimize, stats
from scipy.interpolate import interp1d

from astropy.coordinates import SkyCoord
from astropy import units as u

import os

# HAWC PDF for spatial null and alternative hypotheses
hwcBkgfile = os.path.join(AmonPyDir,'data/hawc/hawc_bkg_intp.npy')
hwcBkg = np.load(hwcBkgfile, encoding = 'latin1',allow_pickle=True).item()
def probBkgHAWC(dec):
    """Spatial Bkg PDF for a HAWC hotspot. Based on data """
    if dec<-25.: return 0.00619
    if dec>64: return 0.00619
    return hwcBkg(dec)*180./(np.pi*2*np.pi)

def probSigHAWC(spc,sigma):
    """Spatial Signal PDF for a HAWC hotspot. Assumes a gaussian function over the sphere. """
    psf = np.exp(-np.deg2rad(spc)**2/(2*(np.deg2rad(sigma))**2))/(2*np.pi*(np.deg2rad(sigma)**2))
    return psf

### Functions for the coincidence analysis
def insideHAWCBrightSources(dec,ra):
    CrabDec, CrabRA = 22.03,83.623
    Mrk421Dec, Mrk421RA = 38.15,166.15
    Mrk501Dec, Mrk501RA = 39.15,235.45
    G1Dec,G1RA = 17.9, 98.0
    G2Dec,G2RA = 15.0, 105.1
    c = SkyCoord(ra=ra*u.degree, dec=dec*u.degree, frame='icrs')
    lon, lat = c.galactic.l.value, c.galactic.b.value
    if spcang(ra,CrabRA,dec,CrabDec)<=1.3:
        return True
    elif spcang(ra,Mrk421RA,dec,Mrk421Dec)<=1.:
        return True
    elif spcang(ra,Mrk501RA,dec,Mrk501Dec)<=1.:
        return True
    elif spcang(ra,G1RA,dec,G1Dec)<=3.:
        return True
    elif spcang(ra,G2RA,dec,G2Dec)<=3.:
        return True
    elif lat<3.0 and lat>-3.0:
        if lon<90.0 and lon>0:
            return True
    return False

