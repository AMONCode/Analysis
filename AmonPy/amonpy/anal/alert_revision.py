"""@package alert_revision
A package that check for alert revision in case that some of old events arrives with a 
different revision, or for a case where a new event creates an alerts whose other member events
contributed to some old alers 
"""
from __future__ import absolute_import
import sys
sys.path.append('../')
#sys.path.append('../..')
sys.path.append('../tools')
sys.path.append('../dbase')

from amonpy.dbase.db_classes import Alert, AlertLine                        

def check_old_alert_rev(oldAlertLine,newAlert): 
    """
    Check if alert with these events already existed.
    If it existed, create a new alert with the revision
    rev_new=rev_old+1
    """
    alertIdChange=False
    lines_db=oldAlertLine
    alert=newAlert                       
    len1=len(lines_db)
    stream_tmp=lines_db[0].stream_alert
    id_tmp=lines_db[0].id_alert
    rev_max=lines_db[0].rev_alert
    for linedb in lines_db:
        if not ((linedb.stream_alert==stream_tmp) or (linedb.id_alert==id_tmp)): # or or and
            # more than one alert with this events in the past, code 
            # checking each single alert revision in the future
            alertIdChange=True    
            pass
        else:
            if (linedb.rev_alert>rev_max):
                # same old alerts but more revision check
                rev_max=linedb.rev_alert 
    if (alertIdChange==False):  
        # finally do revision, by assigning id from the old alert and rev+1            
        alert.rev=rev_max+1
        alert.id=id_tmp
    return alert    