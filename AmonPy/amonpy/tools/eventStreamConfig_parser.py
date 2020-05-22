from datetime import datetime
from amonpy.dbase import db_classes
from configparser import ConfigParser as CP

def file_parser(filename):
    detconfig = CP(allow_no_value=True)
    with open(filename) as f:
        detconfig.read_file(f)

        rev=detconfig.get('StreamConfig','revision')
        obs=detconfig.get('StreamConfig','obs_name')
        starttime=detconfig.get('StreamConfig','validStart')
        stoptime=detconfig.get('StreamConfig','validStop')
        obs_coord=detconfig.get('StreamConfig','obs_coord_sys')
        astro_coord=detconfig.get('StreamConfig','astro_coord')
        point_type=detconfig.get('StreamConfig','point_type')
        point = detconfig.get('StreamConfig','point')
        psf1 = detconfig.get('StreamConfig','psf1')
        psf2 = detconfig.get('StreamConfig','psf2')
        psf3 = detconfig.get('StreamConfig','psf3')
        psf_type = detconfig.get('StreamConfig','psf_type')
        psf = detconfig.get('StreamConfig','psf')
        s1 = detconfig.get('StreamConfig','sky_val1')
        s2 = detconfig.get('StreamConfig','sky_val2')
        s3 = detconfig.get('StreamConfig','sky_val3')
        sens_type = detconfig.get('StreamConfig','sens_type')
        sens = detconfig.get('StreamConfig','sens')
        fov_type = detconfig.get('StreamConfig','fov_type')
        fov = detconfig.get('StreamConfig','fov')
        eph = detconfig.get('StreamConfig','ephemeris')
        bkg_type = detconfig.get('StreamConfig','bkg_type')
        bkg = detconfig.get('StreamConfig','bkg')
        b_rigidity = detconfig.get('StreamConfig','b_rigidity')
    
        esc = db_classes.EventStreamConfig(0,int(rev))
        esc.observ_name = obs
        esc.validStart = starttime
        esc.validStop = stoptime
        esc.observ_coord_sys = obs_coord
        esc.astro_coord_sys = astro_coord
        esc.point_type = point_type
        esc.point = point
        esc.param1Desc = psf1
        esc.param2Desc = psf2
        esc.param3Desc = psf3
        esc.psf_type = psf_type
        esc.psf = psf 
        esc.skymap_val1Desc = s1
        esc.skymap_val2Desc = s2
        esc.skymap_val3Desc = s3
        esc.sensitivity_type = sens_type
        esc.sensitivity = sens
        esc.fov_type = fov_type
        esc.fov = fov
        esc.ephemeris = eph
        esc.bckgr_type = bkg_type
        esc.bckgr = bkg
        esc.mag_rigidity = b_rigidity
    return esc
