from datatime import datetime
from amonpy.dbase import db_classes
from configparser import ConfigParser as CP

def file_parser(filename):
    alertconfig  = CP(allow_no_value=True)
    with open(filename) as f:
        alertconfig.read_file(f)

        stream = alertconfig.get('AlertConfig','stream')
        rev = alertconfig.get('AlertConfig','rev')
        validStart = alertconfig.get('AlertConfig','validStart')
        validStop = alertconfig.get('AlertConfig','validStop')
        participating = alertconfig.get('AlertConfig','participating')
        p_thresh = alertconfig.get('AlertConfig','p_thresh')
        N_thresh = alertconfig.get('AlertConfig','N_thresh')
        deltaT = alertconfig.get('AlertConfig','deltaT')
        cluster_method = alertconfig.get('AlertConfig','cluster_method')
        sens_thresh = alertconfig.get('AlertConfig','sens_thresh')
        skymap_val1Desc = alertconfig.get('AlertConfig','sky_val1')
        skymap_val2Desc = alertconfig.get('AlertConfig','sky_val2')
        skymap_val3Desc = alertconfig.get('AlertConfig','sky_val3')
        bufferT = alertconfig.get('AlertConfig','bufferT')
        R_thresh = alertconfig.get('AlertConfig','R_thresh')
        cluster_thresh = alertconfig.get('AlertConfig','cluster_thresh')

        ac = db_classes.AlertConfig(int(stream),int(rev))
        ac.stream             = stream
        ac.rev                = rev
        ac.validStart         = validStart
        ac.validStop          = validStop 
        ac.participating      = participating
        ac.p_thresh           = p_thresh
        ac.N_thresh           = N_thresh
        ac.deltaT             = deltaT
        ac.cluster_method     = cluster_method
        ac.sens_thresh        = sens_thresh
        ac.skymap_val1Desc    = skymap_val1Desc
        ac.skymap_val2Desc    = skymap_val2Desc
        ac.skymap_val3Desc    = skymap_val3Desc
        ac.bufferT            = bufferT
        ac.R_thresh           = R_thresh
        ac.cluster_thresh     = cluster_thresh
        
    return ac
