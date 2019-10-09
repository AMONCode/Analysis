#run_amon_archive.py
"""@package run_write_amon_archival
Old module for running archival clustering analysis and writing it into database.
"""
from __future__ import print_function
from builtins import range
import sys
sys.path.append('../')
sys.path.append('../tools')
sys.path.append('../dbase')
sys.path.append('../anal')
from time import time
import db_read
import cluster
from db_classes import Alert, AlertLine
import db_write
import db_delete
import run_amon_archival
import db_populate_class
import wx
import dialog_choice

from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
from numpy import array, where, math

HostFancyName='localhost' #'db.hpc.rcc.psu.edu'
UserFancyName='yourname' 
PasswordFancy='yourpass' 
DBFancyName='AMON_test2'

stream_num=0
alerts=[]
alertlines=[]
new_alertline=[]
num_alerts=0
num_events=0  # num
i=0
j=0
id=0 # dummy

choices = ['Do not write to DB', 'Overwrite alert stream', 'Make new alert stream', 'Cancel']
result_dialog=''

# select an option how to run this script 
result_dialog = dialog_choice.SelectChoice(choices).result
if result_dialog==choices[0]:
    print('Archival analysis will not be written to DB') 
    stream_num, alerts=run_amon_archival.amon_archival()
elif result_dialog==choices[1]:
    print('Archival analysis will be written to DB')
    stream_num, alerts=run_amon_archival.amon_archival()
elif result_dialog==choices[2]:
    print('Archival analysis will be appended as new alert stream in  DB')
    print('This option is not supported yet, terminating.')
    sys.exit(0)
    # need to:
    # 1. Identify the lowest unused alert stream number in the database
    # 2. Duplicate the alertStreamConfig into the new stream
    # 3. Call the archival run script with the new config
    # 4. Write the results to the database
else:
    print('Terminating.')
    sys.exit(0)

num_alerts=len(alerts)
print('There is %d alert to be written' % num_alerts)

# populate alertline class
alertlines=db_populate_class.populate_alertline(alerts)  
num_alertlines=0
num_alertlines=len(alertlines)
for i in range(num_alertlines):
    print("Alert line %d" % i)
    print()
    alertlines[i].forprint() 


#if (stream_num ==1):
if (stream_num !=0):    # don't take any action for stream zero
    if result_dialog==choices[1]:
        
        print("Checking if arhival alerts are already in DB. \
               They will be deleted,before new alerts are written.")
        count=0
        count=db_read.alert_count(stream_num,"alert",HostFancyName, UserFancyName, 
                     PasswordFancy,DBFancyName) 
        print('Number of rows to be deleted %d' % count)                 
        if (count > 0):
            "Alert table is not empty. Deleting this stream."
       
            db_delete.delete_alertline_stream(stream_num,HostFancyName,UserFancyName,
                                     PasswordFancy,DBFancyName)  
            db_delete.delete_alert_stream(stream_num,HostFancyName,UserFancyName,
                                     PasswordFancy,DBFancyName)                                                         
                                                           
        db_write.write_alert(stream_num,HostFancyName,UserFancyName,PasswordFancy, 
                         DBFancyName,alerts)
                     
        db_write.write_alertline(HostFancyName,UserFancyName,PasswordFancy, 
                             DBFancyName,alertlines)
    elif result_dialog==choices[0]:
        print('Analysis results will not be written')  
    elif result_dialog==choices[2]:
        print('This option is not supported yet. Results are not appended.')  
    else: 
        print('Pass.')                          
else:
    print('Invalid stream number. Only streams >= 1 allowed for archival analysis.')
