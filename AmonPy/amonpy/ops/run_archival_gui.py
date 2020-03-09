#!/usr/bin/env python
#run_archival.py

"""@package run_archival
    This is a top level script which imports
    a large timeslice of events from the database and
    executes an analysis on them to generate alerts.

    Works with the Enthought Canopy package management

    Example: > python run_archival.py dbaccess.txt

    where dbaccess.txt contans a string in dictionary format,
    containing the information required to access the database
"""
from __future__ import absolute_import
from __future__ import print_function
from builtins import str
import sys

# AmonPy modules:
from amonpy.dbase.db_classes import Alert, AlertLine, AlertConfig, exAlertConfig, event_def, AlertConfig2
from amonpy.dbase.db_classes import Event
import amonpy.dbase.db_populate_class as db_populate_class
import amonpy.dbase.db_read as db_read
import amonpy.dbase.db_write  as db_write
import amonpy.dbase.db_delete as db_delete
import amonpy.anal.analysis as analysis

import dialog_choice
import input_text_window

# 3rd party modules
from time import time
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
import wx
import multiprocessing
import ast

print()
print(' **** EXECUTING run_archival.py ****')

# Create the most generic Event class
Event = event_def()

# Get the database access information
# which should be passed as an initial argument
try:
    filename = sys.argv[1]
except:
    filename = 'dbaccess.txt'
file = open(filename)
line = file.readline()
db = ast.literal_eval(line)
file.close()
HostFancyName=db['host']
UserFancyName=db['user']
PasswordFancy=db['password']
DBFancyName=db['database']
print()
print(' USING DATABASE ACCESS FILE: %s ' %filename)
print('   hostname: '.ljust(11), db['host'])
print('   username: '.ljust(11), db['user'])
print('   password: '.ljust(11), db['password'])
print('   database: '.ljust(11), db['database'])


# get the Alert Stream cofig
print()
choices_conf=['Use test config','Get config from DB',
              'Create new config','Cancel']
info = 'Which Alert configuration?'
result_dialog_conf = dialog_choice.SelectChoice(choices_conf,info=info).result
if result_dialog_conf==choices_conf[0]:
    print(' USING TEST ALERT CONFIG')
    config = exAlertConfig()
    config.forprint()
    event_streams = [0,1,7]
if result_dialog_conf==choices_conf[1]:
    # add code that asks for analysis stream,
    # add a code that choses always the latest revision
    stream_num=1
    rev=0
    config=db_read.read_alertConfig(stream_num,rev,HostFancyName,
                          UserFancyName,PasswordFancy,DBFancyName);
    print()
    print('AlertConfig loading from the database...')
    print()
    print('...works only for stream 1 and revision 0 for now')
    config.forprint()
    event_streams = [0,1,7]
if result_dialog_conf==choices_conf[2]:
    print('User-generated AlertConfig')
    print()
    print('Checking the highest taken analysis stream number from database...')
    print()
    stream_count=db_read.stream_count_alertconfig(HostFancyName,
                          UserFancyName,PasswordFancy,DBFancyName)
    print("Latest stream number is %s" % stream_count)
    print()
    stream_num = stream_count + 1
    print("The next free stream number is %s" % stream_num)
    rev = 0
    config = AlertConfig2(stream_num, rev)
    choices_stream=['IceCube only','ANTARES only', 'HAWC only', 'IceCube + ANTARES',
                    'IceCube + HAWC', 'ANTARES + HAWC','All', 'Cancel']
    info = 'Which stream configuration?'
    result_dialog_stream = dialog_choice.SelectChoice(choices_stream,info=info).result
    event_streams = []
    if result_dialog_stream ==choices_stream[0]:
        config.participating      = 2**0
        event_streams +=[0]
    elif result_dialog_stream ==choices_stream[1]:
        config.participating      = 2**1
        event_streams +=[1]
    elif result_dialog_stream ==choices_stream[2]:
        config.participating      = 2**7
        event_streams +=[7]
    elif result_dialog_stream ==choices_stream[3]:
        config.participating      = 2**0 + 2**1
        event_streams.extend([0,1])
    elif result_dialog_stream ==choices_stream[4]:
        event_streams.extend([0,7])
        config.participating      = 2**0 + 2**7
    elif result_dialog_stream ==choices_stream[5]:
        event_streams.extend([1,7])
        config.participating      = 2**1 + 2**7
    elif result_dialog_stream ==choices_stream[6]:
        config.participating      = 2**0 + 2**1 + 2**7
        event_streams.extend([0,1,7])
    else:
        print('User requested cancelation.')
        sys.exit(0)
    #far = 0
    #info = 'Enter FAR density [sr^-1s^-1](0 means no FAR used)'
    #far= input_text_window.SelectChoice(info=info).result
    #config.false_pos = float(far)
    pvalue = 0 # p-value threshold 0, means not used
    info = 'Enter p-value threshod (not used yet)'
    pvalue= input_text_window.SelectChoice(info=info).result
    config.p_thresh = float(pvalue)
    info = 'Number threshold for events'
    if (result_dialog_stream ==choices_stream[0]) or \
       (result_dialog_stream ==choices_stream[1]) or \
       (result_dialog_stream ==choices_stream[2]):
        config.N_thresh='{' + str(event_streams[0]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + '}'
    elif (result_dialog_stream ==choices_stream[3]) or \
       (result_dialog_stream ==choices_stream[4]) or \
       (result_dialog_stream ==choices_stream[5]):
        info = 'Number threshold for 1st stream'
        thresh1='{' + str(event_streams[0]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + ', '
        info = 'Number threshold for 2nd stream'
        thresh2= str(event_streams[1]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + '}'
        config.N_thresh = thresh1 + thresh2
    else:
        info = 'Number threshold for 1st stream'
        thresh1='{' + str(event_streams[0]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + ', '
        info = 'Number threshold for 2nd stream'
        thresh2= str(event_streams[1]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + ', '
        info = 'Number threshold for 3nd stream'
        thresh3= str(event_streams[2]) + ':' + \
                         str(input_text_window.SelectChoice(info=info).result) + '}'
        config.N_thresh = thresh1 + thresh2 + thresh3
    #config.N_thresh = '{0:1,1:1,7:1}'
    info = 'Search time window'
    config.deltaT             = float(input_text_window.SelectChoice(info=info).result)
    config.bufferT            = 1000.0   # Not in orininal AlertConfig class, but DB supports it
    info = 'Analysis cluster method'
    #config.cluster_method     = 'Fisher'
    choices_clust=['Fisher','New method (not supported yet)']
    result_clust = dialog_choice.SelectChoice(choices_clust,info=info).result
    if result_clust == choices_clust[0]:
        config.cluster_method = str(result_clust)
    else:
        print()
        print('Unsupported method requested')
        print('Analysis will use Fisher (default)')
        config.cluster_method = 'Fisher'
    info = 'Cluster threshold (# of sigma)'
    config.cluster_thresh      =  float(input_text_window.SelectChoice(info=info).result)
    config.sens_thresh        = 'N/A'
    config.psf_paramDesc1     = 'N/A'
    config.psf_paramDesc2     = 'N/A'
    config.psf_paramDesc3     = 'N/A'
    config.skymap_val1Desc    = 'N/A'
    config.skymap_val2Desc    = 'N/A'
    config.skymap_val3Desc    = 'N/A'
    config.validStart         = datetime(2012,1,1,0,0,0,0)
    config.validStop          = datetime(2013,1,1,0,0,0,0)
    config.R_thresh           = 0.0

    config.forprint()
    print()
    print('Writing configuration to database')
    db_write.write_alert_config([stream_num],HostFancyName,
                           UserFancyName,PasswordFancy,DBFancyName, [config])
if result_dialog_conf==choices_conf[3]:
    print(' QUIT: User requested')
    sys.exit(0)
stream_num = config.stream


# read events from the database
TimeSlice = timedelta.total_seconds(config.validStop - config.validStart)
TimeStart = str(config.validStart)
TimeStop  = str(config.validStop)
t1 = time()
events=db_read.read_event_timeslice_streams(event_streams, TimeStart,TimeSlice,HostFancyName,
                                    UserFancyName,PasswordFancy,DBFancyName)
t2 = time()
print('   Read time: %.2f seconds' % float(t2-t1))

# put events in temporal order, oldest events first
events = sorted(events,key=attrgetter('datetime'))

# start analysis server process
print()
print(' STARTING ANALYSIS SERVER')
(server_p,client_p) = multiprocessing.Pipe()
anal_p = multiprocessing.Process(target=analysis.anal,
                    args=((server_p,client_p),config))
anal_p.start()

# send events to the analysis process, send the oldest events first
print('   Sending events')
t1 = time()
for ev in events:
    client_p.send(ev)
t2 = time()
print('   Analysis time: %.2f seconds' % float(t2-t1))
# get the stored alerts
print('   Retrieving alerts')
t1 = time()
client_p.send('get_alerts')
alerts = client_p.recv()
t2 = time()
print('   Retrieval time: %.2f seconds' % float(t2-t1))

# analysis done, close the pipe
server_p.close()
client_p.close()
print('   Analysis server closed')

if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem'):
    print('   %d alerts'     % len(alerts))
elif(alerts == 'Empty' or alerts == 'Problem'):
    print(alerts)
    print("No alerts, exiting.")
    sys.exit(0)
else:
    print(alerts)
    print("No alerts, exiting.")
    sys.exit(0)

if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem' and alerts[0] !=True):
#if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem'):
# populate alertline class
    alertlines=db_populate_class.populate_alertline(alerts)
    print('   %d alertlines generated' % len(alertlines))
    print(' ANALYSIS COMPLETE')


# identify what to do with alerts
    print()
    choices = ['Do not write to DB','Overwrite alert stream',
           'Make new alert stream', 'Cancel']
    info = 'What would you like to do with the alerts?'
    result_dialog = dialog_choice.SelectChoice(choices,info=info).result
    if result_dialog==choices[0]:
        print(' QUIT: Analysis results will NOT be written to DB')
    elif result_dialog==choices[1]:
        print(' WRITING ANALYSIS RESULTS TO THE DATABASE')
        if (stream_num !=0):    # don't take any action for stream zero
            print("   Checking if arhival alerts are already in DB.")
            count=db_read.alert_count(stream_num,"alert",HostFancyName,
                           UserFancyName,PasswordFancy,DBFancyName)
            print('   Number of rows to be deleted: %d' % count)
            if (count > 0):
                db_delete.delete_alertline_stream_by_alert(stream_num,
                   HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                db_delete.delete_alert_stream(stream_num,HostFancyName,
                UserFancyName,PasswordFancy,DBFancyName)
            db_write.write_alert(stream_num,HostFancyName,UserFancyName,
               PasswordFancy,DBFancyName,alerts)
            db_write.write_alertline(HostFancyName,UserFancyName,
                PasswordFancy, DBFancyName,alertlines)
        else:
            print('   Invalid stream number')
            print('   Only streams >= 1 allowed for archival analysis')
    elif result_dialog==choices[2]:
        print('APPENDING NEW ALERT STREAM TO THE DATABASE')
        if (stream_num !=0):    # don't take any action for stream zero
            print("   Checking if arhival alerts are already in DB.")
            count=db_read.alert_count(stream_num,"alert",HostFancyName,
                           UserFancyName,PasswordFancy,DBFancyName)
            print('   Number of rows to be deleted: %d' % count)
            if (count > 0):
                db_delete.delete_alertline_stream_by_alert(stream_num,
                   HostFancyName,UserFancyName,PasswordFancy,DBFancyName)
                db_delete.delete_alert_stream(stream_num,HostFancyName,
                    UserFancyName,PasswordFancy,DBFancyName)
            db_write.write_alert(stream_num,HostFancyName,UserFancyName,
               PasswordFancy,DBFancyName,alerts)
            db_write.write_alertline(HostFancyName,UserFancyName,
                PasswordFancy, DBFancyName,alertlines)
        else:
            print('   Invalid stream number')
            print('   Only streams >= 1 allowed for archival analysis')
    else:
        print(' QUIT: User request')
        sys.exit(0)

else:
    print("Last event")
    alerts[1].forprint()
    print("No alerts found")
    sys.exit(0)
print()
print(' **** END run_archival.py ****')
