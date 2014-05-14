#convert_celest.py
"""@package convert_celest
converts between celestial angles (RA,dec)
given in degrees and unit vector on the sphere
"""

from numpy import math, array

def radec2vec(ra,dec):
    phi = math.radians(ra)
    theta = math.radians(90.-dec)
    return array([math.sin(theta)*math.cos(phi),
                  math.sin(theta)*math.sin(phi),
                  math.cos(theta)])

def vec2radec(v):
    tol = 1e-20
    
    ns=1.*(v[2]>0.)-1.*(v[2]<0.)       # north or south hemisphere
    fb=(1.*(v[0]>0.)-1.*(v[0]<0.))     # front or back  hemisphere
    lr=(1.*(v[1]>0.)-1.*(v[1]<0.))     # left  or right hemisphere
    
    if (abs(v[2]-1.)<tol):
        theta = 0.
        phi = 0.
    elif (abs(v[2]+1.)<tol):
        theta = math.pi
        phi = 0.
    else:
        theta = math.acos(v[2])
        if (abs(v[0]/math.cos(theta)) < tol):
            phi = lr*math.pi/2.
        else:
            phi= math.atan(v[1]/v[0]) + (1.-fb)/2.*math.pi
    ra = (math.degrees(phi)+360.)%360.
    dec = 90.-math.degrees(theta)
    return {'ra':ra,'dec':dec}
