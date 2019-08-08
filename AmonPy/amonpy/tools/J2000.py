import numpy as np
from astropy.time import Time

def J2000(time,ra,dec,degrees=True):
    """
        Convert celestial coordinates in current epoch to J2000 epoch.
        Receives time in UTC, and cooridnates in degrees as default
    """
    try:
        t = Time(time,format='isot',scale='utc')
    except ValueError:
        t = Time(time,format='iso',scale='utc')
    JD = t.jd #Julian day
    JC = (JD - 2451545.0)/36525.0 #Julian Century

    zeta   = (0.6406161 + (0.0000839 + 0.0000050*JC)*JC)*JC
    z      = (0.6406161 + (0.0003041 + 0.0000051*JC)*JC)*JC
    theta  = (0.5567530 - (0.0001185 + 0.0000116*JC)*JC)*JC

    zeta = np.deg2rad(zeta)
    z = np.deg2rad(z)
    theta = np.deg2rad(theta)

    cosTheta= np.cos(theta)
    sinTheta = np.sin(theta)

    if degrees:
        ra = np.deg2rad(ra)
        dec = np.deg2rad(dec)

    sinDec = np.sin(dec)
    cosDec = np.cos(dec)
    cosRA = np.cos(ra-z)

    dec2000 = -cosRA * sinTheta * cosDec + cosTheta * sinDec
    dec2000 = np.arcsin(dec2000)
    dec2000 = np.rad2deg(dec2000)

    ra2000 = 0.0
    if dec2000 == 90.0:
        return ra2000, dec2000

    s1 = np.sin(ra-z)*cosDec
    c2 = cosRA * cosTheta * cosDec + sinTheta * sinDec
    ra2000 = np.arctan2(s1,c2) - zeta
    ra2000 = np.rad2deg(ra2000)

    if ra2000<0:
        ra2000 += 360.

    return ra2000, dec2000
