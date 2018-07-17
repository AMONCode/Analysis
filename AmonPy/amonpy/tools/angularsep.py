import numpy as np

#Angular separation of two angles in the sphere
#Angles given in degrees
def spcang(ra1,ra2,dec1,dec2,degree=True):
    dec1 = np.deg2rad(dec1)
    dec2 = np.deg2rad(dec2)
    DeltaRA = np.deg2rad(ra1-ra2)
    sep = np.arccos(np.cos(dec1)*np.cos(dec2)*np.cos(DeltaRA) + np.sin(dec1)*np.sin(dec2))
    if degree:
        return np.rad2deg(sep)
    else:
        return sep
