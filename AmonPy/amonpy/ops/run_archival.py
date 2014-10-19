#!/usr/bin/env python
#run_archival_command_options.py

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
import sys
from optparse import OptionParser
from argparse import ArgumentParser
sys.path.append('../')
sys.path.append('../..')
sys.path.append('../tools')
sys.path.append('../dbase')
sys.path.append('../anal')

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
import getpass

def parse_command_line():
       #TODO Make usage part of help menu better
       parser=ArgumentParser(usage='run_archival [--host address] [--username username] [--database name] [--output-config int] [ALERT CONFIG CHOICE] [ADDITIONAL OPTIONS]')
       parser.add_argument("-v", "--verbose", action="store_true", help="Be verbose.")
       parser.add_argument("-p", "--password", metavar="password", help="Input password in plain text \
                     on command line instead of being asked for it at the start of execution")

       required_group=parser.add_argument_group("requirements")
       required_group.add_argument("-H", "--host", metavar="address", help="Database host address")
       #TODO Add feature to pull username from login information so that the username option is optional like in MySql
       required_group.add_argument("-u", "--username", metavar="username", help="Database username")
       required_group.add_argument("-d", "--database", metavar="name", help="Name of database")
       required_group.add_argument("-o", "--output-config", metavar="int", type=int, help="What to do with the alert, \
                     1=Do note write to database, 2=Overwrite alert stream, 3=Make new alert stream")


       config_group=parser.add_argument_group("alert configurations (most choose one and only one)").add_mutually_exclusive_group()
       config_group.add_argument("--use-test-config", action="store_true", default=True, help="Use the test Alert configuration [Default]")
       config_group.add_argument("--use-db-config", action="store_true", help="Get Alert configuration from database")
       config_group.add_argument("--use-new-config", action="store_true", help="Create a new Alert configuration")

       new_config_options_group=parser.add_argument_group("options required if invoking --use-new-config")
       #TODO Determine a method of handling stream config and cluster method to replace the number input method
       new_config_options_group.add_argument("-s", "--stream-config", metavar="int", type=int, 
                     help="Stream configuration, 1=IceCube only,2=ANTARES only,3=HAWC only, 4=Swift only, \
                     5=IceCube + ANTARES,6=IceCube + HAWC,7=ANTARES + HAWC,8=IceCube + Swift,9=All")
       new_config_options_group.add_argument("-P", "--pvalue", metavar="float", type=float, default=0.0, 
                     help="P-Value threshold level, 0.0 means no threshold [default: 0.0]")
       new_config_options_group.add_argument("-n", "--num-events-thresh", metavar="int", type=int, 
                     help="Number of events threshold level; each detector in stream-config needs 1 int, \
                                   and in the order listed.  e.g. if steam-config=4, to use a num thresh of\
                                   2 for IceCube and 7 for ANTARES, -n would take 2 7 as its input", nargs='*')
       #TODO Take default setting off of --cluster-method once more options are added
       new_config_options_group.add_argument("-c", "--cluster-method", metavar="int", type=int, default=1, 
                     help="Analysis cluster method, 1=Fisher (no other methods supported yet)")
       new_config_options_group.add_argument("-t", "--time-window", metavar="float", type=float, help="Search time window")
       new_config_options_group.add_argument("--cluster-threshold", metavar="float", type=float, help="Cluster threshold (# of sigma)")
       
       return parser.parse_args()

options=parse_command_line()

# Make sure all of the required arguments are entered
# FIXME There's probably a smarter way to do this
missing_requirements = {}
required_arguments = ['host','username','database','output_config']
if (options.use_db_config) or (options.use_new_config):
        options.use_test_config == False
if options.use_new_config:
       required_arguments.extend(['stream_config','time_window','num_events_thresh','cluster_threshold'])
for arg in required_arguments:
       if not eval('options.' + arg):
              missing_requirements.setdefault('missing',[]).append(arg)
if missing_requirements:
       missing_args_str = 'Missing the following required options:'
       for arg in missing_requirements['missing']:
             missing_args_str += ' --' + arg.replace('_','-') 
       missing_args_str += '; see --help for more information'
       raise RuntimeError(missing_args_str)

if (options.use_new_config) & (options.cluster_method != 1):
       print options.cluster_method
       print 'Unsupported cluster method requested\nAnalysis will use Fisher (default)'
       options.cluster_method=1
       print options.cluster_method

if not options.password:
       options.password=getpass.getpass('DB Password: ')

if options.verbose:
       print '**** EXECUTING run_archival.py ****\nhostname: ' + str(options.host) + '\nusername: ' \
                     + str(options.username) + '\npassword: <hidden>\ndatabase: ' + str(options.database)

# Create the most generic Event class
Event = event_def()

if options.use_test_config:
       if options.verbose:
              print 'USING TEST ALERT CONFIG'
       config = exAlertConfig()
       config.forprint()
       event_streams = [0,1,7]
if options.use_db_config:
       # add code that asks for analysis stream, 
       # add a code that choses always the latest revision
       stream_num=1
       rev=0
       config=db_read.read_alertConfig(stream_num,rev,options.host,
                          options.username,options.password,options.database);
       if options.verbose:
              print 'AlertConfig loading from the database...\n...works only for stream 1 and revision 0 for now'
       config.forprint()
       event_streams = [0,1,7]
if options.use_new_config:
       if options.verbose:
              print 'User-generated AlertConfig\nChecking the highest taken analysis stream number from database...'

       stream_count=db_read.stream_count_alertconfig(options.host,
                          options.username,options.password,options.database)
       stream_num = stream_count + 1

       if options.verbose:
              print "Latest stream number is %s\n The next free stream number is %s" % (stream_count, stream_num)

       rev = 0  
       config = AlertConfig2(stream_num, rev)
       choices_stream=['IceCube only','ANTARES only', 'HAWC only', 'IceCube + ANTARES',
                    'IceCube + HAWC', 'ANTARES + HAWC','IceCube + Swift','All', 'Cancel']
       event_streams = []
       if options.stream_config == 1:
              config.participating      = 2**0
              event_streams +=[0]
       elif options.stream_config == 2:
              config.participating      = 2**1
              event_streams +=[1]
       elif options.stream_config == 3:
              config.participating      = 2**7 
              event_streams +=[7] 
       elif options.stream_config == 4:
              config.participating      = 2**4
              event_streams +=[4]
       elif options.stream_config == 5:
              event_streams.extend([0,1])
              config.participating      = 2**0 + 2**1
       elif options.stream_config == 6:
              event_streams.extend([0,7])
              config.participating      = 2**0 + 2**7
       elif options.stream_config == 7:
              config.participating      = 2**1 + 2**7
              event_streams.extend([1,7])
       elif options.stream_config == 8:
              config.participating      = 2**0 + 2**4
              event_streams.extend([0,4])
       elif options.stream_config == 9:
              config.participating      =2**0 + 2**1 + 2**7
              event_streams.extend([0,1,7])
       else:
              raise RuntimeError('Either no stream config or an invalid stream config specified, see --help for more information')
       #far = 0    
       #info = 'Enter FAR density [sr^-1s^-1](0 means no FAR used)'                           
       #far= input_text_window.SelectChoice(info=info).result 
       #config.false_pos = float(far)
       config.p_thresh = options.pvalue

       if (options.stream_config == 1) or (options.stream_config == 2) or (options.stream_config == 3) or (options.stream_config == 4):
              if len(options.num_events_thresh) > 1:
                     print 'More number thresholds input than config streams chosen, using first number in list (%d)' % \
                                   options.num_events_thresh[0]
              config.N_thresh='{' + str(event_streams[0]) + ':' + str(options.num_events_thresh[0]) + '}' 

       elif (options.stream_config == 5) or (options.stream_config == 6) or (options.stream_config == 7) or (options.stream_config == 8):
              if len(options.num_events_thresh) > 2:
                     print 'More number thresholds input than config streams chosen, using first two numbers in list \
                                   (%d and %d)' % (options.num_events_thresh[0], options.num_events_thresh[1])
              thresh1='{' + str(event_streams[0]) + ':' + \
                            str(options.num_events_thresh[0]) + ', '
              thresh2= str(event_streams[1]) + ':' + \
                            str(options.num_events_thresh[1]) + '}'
              config.N_thresh = thresh1 + thresh2
       else:
              if len(options.num_events_thresh) > 3:
                     print 'More number thresholds input than config streams chosen, using first three numbers in list \
                                   (%d, %d, and %d)' % (options.num_events_thresh[0],options.num_events_thresh[1],options.num_events_thresh[2])
              thresh1='{' + str(event_streams[0]) + ':' + \
                            str(options.num_events_thresh[0]) + ', '
              thresh2= str(event_streams[1]) + ':' + \
                            str(options.num_events_thresh[1]) + ', '
              thresh3= str(event_streams[2]) + ':' + \
                            str(options.num_events_thresh[2]) + '}'  
              config.N_thresh = thresh1 + thresh2 + thresh3                   
       #config.N_thresh = '{0:1,1:1,7:1}' 
       config.deltaT             = options.time_window
       config.bufferT            = 1000.0   # Not in orininal AlertConfig class, but DB supports it
       if options.cluster_method == 1:
              config.cluster_method = 'Fisher'
       else:
              # If this error is raised, something has gone wrong because options.cluster_method should have been set to 1 above
              raise RuntimeError('Unsupported clustering method requested')
       config.cluster_thresh      =  options.cluster_threshold
       config.sens_thresh        = 'N/A'
       config.psf_paramDesc1     = 'N/A'
       config.psf_paramDesc2     = 'N/A'
       config.psf_paramDesc3     = 'N/A'
       config.skymap_val1Desc    = 'N/A'                
       config.skymap_val2Desc    = 'N/A'
       config.skymap_val3Desc    = 'N/A'
       config.validStart         = datetime(2008,6,4,9,20,13,0)
       config.validStop          = datetime(2009,5,20,3,12,53,0)
       config.R_thresh           = 0.0    
                               
       config.forprint() 
       print 
       print 'Writing configuration to database'
       db_write.write_alert_config([stream_num],options.host,
                     options.username,options.password,options.database, [config])   
if (not options.use_test_config) & (not options.use_db_config) & (not options.use_new_config):
       raise RuntimeError('No Alert configuration specified, see --help for more information')

stream_num = config.stream

# read events from the database
TimeSlice = timedelta.total_seconds(config.validStop - config.validStart)
TimeStart = str(config.validStart)
TimeStop  = str(config.validStop)
t1 = time()
events=db_read.read_event_timeslice_streams(event_streams, TimeStart,TimeSlice,options.host,
                                    options.username,options.password,options.database)
t2 = time()
print '   Read time: %.2f seconds' % float(t2-t1)

# put events in temporal order, oldest events first
events = sorted(events,key=attrgetter('datetime'))

# start analysis server process
print
print ' STARTING ANALYSIS SERVER'
(server_p,client_p) = multiprocessing.Pipe()
anal_p = multiprocessing.Process(target=analysis.anal,
                    args=((server_p,client_p),config))
anal_p.start()

# send events to the analysis process, send the oldest events first
print '   Sending events'
t1 = time()
for ev in events:
    client_p.send(ev)
t2 = time()
print '   Analysis time: %.2f seconds' % float(t2-t1)
# get the stored alerts
print '   Retrieving alerts'
t1 = time()
client_p.send('get_alerts')
alerts = client_p.recv()
t2 = time()
print '   Retrieval time: %.2f seconds' % float(t2-t1)

# analysis done, close the pipe
server_p.close()
client_p.close()
print '   Analysis server closed'

if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem'):
    print '   %d alerts'     % len(alerts)
elif(alerts == 'Empty' or alerts == 'Problem'):
    print alerts
    print "No alerts, exiting."
    sys.exit(0)
else:
    print alerts
    print "No alerts, exiting."
    sys.exit(0)  

if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem' and alerts[0] !=True):
#if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem'):
# populate alertline class
    alertlines=db_populate_class.populate_alertline(alerts)  
    print '   %d alertlines generated' % len(alertlines) 
    print ' ANALYSIS COMPLETE'


# identify what to do with alerts
    if options.output_config==1:
        print ' QUIT: Analysis results will NOT be written to DB' 
    elif options.output_config==2:
        print ' WRITING ANALYSIS RESULTS TO THE DATABASE'
        if (stream_num !=0):    # don't take any action for stream zero
            print "   Checking if arhival alerts are already in DB."
            count=db_read.alert_count(stream_num,"alert",options.host,
                           options.username,options.password,options.database) 
            print '   Number of rows to be deleted: %d' % count                 
            if (count > 0):
                db_delete.delete_alertline_stream_by_alert(stream_num,
                   options.host,options.username,options.password,options.database)  
                db_delete.delete_alert_stream(stream_num,options.host,
                options.username,options.password,options.database)
            db_write.write_alert(stream_num,options.host,options.username,
               options.password,options.database,alerts)
            db_write.write_alertline(options.host,options.username,
                options.password, options.database,alertlines)                         
        else:
            print '   Invalid stream number'
            print '   Only streams >= 1 allowed for archival analysis'
    elif options.output_config==3:
        print 'APPENDING NEW ALERT STREAM TO THE DATABASE'
        if (stream_num !=0):    # don't take any action for stream zero
            print "   Checking if arhival alerts are already in DB."
            count=db_read.alert_count(stream_num,"alert",options.host,
                           options.username,options.password,options.database) 
            print '   Number of rows to be deleted: %d' % count                 
            if (count > 0):
                db_delete.delete_alertline_stream_by_alert(stream_num,
                   options.host,options.username,options.password,options.database)  
                db_delete.delete_alert_stream(stream_num,options.host,
                    options.username,options.password,options.database)
            db_write.write_alert(stream_num,options.host,options.username,
               options.password,options.database,alerts)
            db_write.write_alertline(options.host,options.username,
                options.password, options.database,alertlines)                         
        else:
            print '   Invalid stream number'
            print '   Only streams >= 1 allowed for archival analysis'
    else:
       raise RuntimeError("Not sure what to do with alerts, see --help for more details")
    
else:
    print "Last event"
    alerts[1].forprint()
    print "No alerts found"
    sys.exit(0)
print
print ' **** END run_archival.py ****'
