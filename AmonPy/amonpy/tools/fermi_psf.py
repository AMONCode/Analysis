# -*- coding: utf-8 -*-
"""@package fermi_psf
    Module with Fermi specific function:
        -calculates angular resolution of Fermi data 
"""

#Author:Michael Toomey <mwt5345.psu.edu> 2/18/15
#PSF script based of of lastest PSF from Fermi Collaboration's Latest Article:
#..., M. Ackermann, M. Ajello, A. Allafort, K. Asano, WB Atwood, 
#L. Baldini, et al. 2013. DETERMINATION OF THE POINT-SPREAD 
#FUNCTION FOR THE FERMI LARGE AREA TELESCOPE FROM ON-ORBIT DATA 
#AND LIMITS ON PAIR HALOS OF ACTIVE GALACTIC NUCLEI. ASTROPHYSICAL JOURNAL 765, (1): 54.

def fermi_psf(E):
    """
        Calculates Fermi Angular Resolution
    """
    var_17 = E/100 #Energy(MeV) from Fermi divded by 100MeV
    var_18 = var_17**(-0.8) #β sets the scaling of the multiple scattering with energy; β ≈ 0.8
    var_19 = var_18 * 3.5 #c0 is the normalization of the multiple scattering term; c0 = 3.5◦
    var_20 = var_19**2
    var_21 = (0.15)**2 #c1 is instrument-pitch uncertainty; c1 = 0.15◦
    var_22 = var_20 + var_21
    var_23 = var_22**0.5
    return var_23