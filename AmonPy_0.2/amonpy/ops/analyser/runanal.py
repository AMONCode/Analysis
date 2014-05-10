"""@package runanal
    This is a top level task that gets initialized
    at the time that AMON server starts running.
    It receives event stream number, event number and event revision
    from the AMON server in real-time (AMON server calls task function 
    AnalRT.run every time a new events comes from the outside world)
    Upon reception of these three parameters, a new event is read from the DB
    and passed to the main analysis code using Python multiprocessing module.  

    Works with the Enthought Canopy package management, RabittMQ server as a broker
    for messages and Celery allowing from transport of messages from AMON server to 
    this worker program.

    To run (outside this directory called analizer):
    
    celery worker --app=analyser -l info

    where dbaccess.txt contans a string in dictionary format,
    containing the information required to access the database
    
    Each alert will be saved to DB, and also written to XML file (in VOEvent format) 
    to the directory /network/server_events. AMON client will send this events in the future 
    to GCN and delete each xml fiel after it has been sent.
"""
from __future__ import absolute_import
from analyser.celery import app
from celery import Task
#from celery import current_app
#from celery.contrib.methods import task_method
#from celery.contrib.methods import task
from celery.result import AsyncResult

import sys
sys.path.append('../')
sys.path.append('../..')
sys.path.append('../../tools')
sys.path.append('../../dbase')
sys.path.append('../../anal')

# AmonPy modules:
from amonpy.dbase.db_classes import Alert, AlertLine, AlertConfig, exAlertConfig, event_def, AlertConfig2
from amonpy.dbase.db_classes import Event
import amonpy.dbase.db_populate_class
import amonpy.dbase.db_read
import amonpy.dbase.db_write
import amonpy.dbase.db_delete
import amonpy.dbase.alert_to_voevent as alert_to_voevent
import amonpy.anal.analysis as analysis
#import dialog_choice
#import input_text_window

# 3rd party modules
from time import time
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
#import wx
import multiprocessing
import ast

print
print ' **** EXECUTING runanal.py ****'

# Create the most generic Event class
@app.task
def error_handler(uuid):
    myresult = AsyncResult(uuid)
    exc = myresult.get(propagate=False)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, exc, myresult.traceback))
          
class AnalRT(Task):
#class AnalRT(object):
    def __init__(self):
        self.Event = event_def()
        self.HostFancyName='localhost'
        self.UserFancyName='yourname'
        self.PasswordFancy='yourpass'
        self.DBFancyName='AMON_test2'
        self.alertDir = 'yourdirpath'

        # get the Alert Stream config
        print
        print ' USING TEST ALERT CONFIG'
        self.config = exAlertConfig()
        self.config.forprint()
        self.event_streams = [0,1,7]  # testing streams
        self.stream_num = self.config.stream
        print
        print ' STARTING ANALYSIS SERVER'
        (self.server_p,self.client_p) = multiprocessing.Pipe()
        self.anal_p = multiprocessing.Process(target=analysis.anal,
                    args=((self.server_p,self.client_p),self.config))
        self.anal_p.start()
    #@app.task(filter=task_method, name='analser.runanal.AnalRT.run')
    def run(self,evstream, evnumber,evrev):
        self.Event.stream = evstream
        self.Event.id     = evnumber
        self.Event.rev    = evrev
        
        t1 = time()
        
        events=amonpy.dbase.db_read.read_event_single(evstream,evnumber,evrev,self.HostFancyName,
                                    self.UserFancyName,self.PasswordFancy,self.DBFancyName)                                    
        t2 = time()
        print '   Read time: %.2f seconds' % float(t2-t1)
        events.forprint()
        # put events in temporal order
        #events = sorted(events,key=attrgetter('datetime'))
        # send events to the analysis process
        print '   Sending events'
        t1 = time()
        #for ev in events:
            #self.client_p.send(ev)
        if isinstance(events,Event):    
            self.client_p.send(events)
        else:
            print "NOT EVENT"
                
        t2 = time()
        print '   Analysis time: %.2f seconds' % float(t2-t1)
        # get the stored alerts
        print '   Retrieving alerts'
        t1 = time()
        self.client_p.send('get_alerts')
        alerts = self.client_p.recv()
        #print '   %d alerts'     % len(alerts)
        t2 = time()
        print '   Retrieval time: %.2f seconds' % float(t2-t1)
        
        # analysis done, close the pipe
        #server_p.close()
        #client_p.close()
        #print '   Analysis server closed'
        
        # write alerts to DB if any
        if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem'):
            # populate alertline class
            alerts[0].forprint()
            alertlines=amonpy.dbase.db_populate_class.populate_alertline(alerts)  
            print '   %d alertlines generated' % len(alertlines) 
            print ' ANALYSIS COMPLETE'
        
            print ' WRITING ANALYSIS RESULTS TO THE DATABASE'
            # modify it later to append to database, not to rewrite    
            if (self.stream_num !=0):    # don't take any action for stream zero in testing phase
                amonpy.dbase.db_write.write_alert(self.stream_num,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName,alerts)
                amonpy.dbase.db_write.write_alertline(self.HostFancyName,
                                                      self.UserFancyName,
                                                      self.PasswordFancy, 
                                                      self.DBFancyName,alertlines) 
                # write alert to the directory from where AMON client will read it and delete 
                # it after sending it to GCN in the future
                xmlForm=alert_to_voevent.alert_to_voevent(alerts) 
                fname=self.alertDir + 'amon_%s_%s_%s.xml' \
                % (alerts[0].stream, alerts[0].id, alerts[0].rev)
                f1=open(fname, 'w+')
                f1.write(xmlForm)
                f1.close()                                                              
            else:
                print '   Invalid stream number'
                print '   Only streams >= 1 allowed for testing analysis'
            return "%d alerts found" % (len(alerts),)    
        else:
            return "No alerts"
"""
# identify what to do with alerts
print
choices = ['Do not write to DB','Overwrite alert stream',
           'Make new alert stream', 'Cancel']
info = 'What would you like to do with the alerts?'
result_dialog = dialog_choice.SelectChoice(choices,info=info).result
if result_dialog==choices[0]:
    print ' QUIT: Analysis results will NOT be written to DB' 
elif result_dialog==choices[1]:
    print ' WRITING ANALYSIS RESULTS TO THE DATABASE'
    if (stream_num !=0):    # don't take any action for stream zero
        print "   Checking if arhival alerts are already in DB."
        count=db_read.alert_count(stream_num,"alert",HostFancyName,
                           UserFancyName,PasswordFancy,DBFancyName) 
        print '   Number of rows to be deleted: %d' % count                 
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
        print '   Invalid stream number'
        print '   Only streams >= 1 allowed for archival analysis'
elif result_dialog==choices[2]:
    print 'APPENDING NEW ALERT STREAM TO THE DATABASE'
    if (stream_num !=0):    # don't take any action for stream zero
        print "   Checking if arhival alerts are already in DB."
        count=db_read.alert_count(stream_num,"alert",HostFancyName,
                           UserFancyName,PasswordFancy,DBFancyName) 
        print '   Number of rows to be deleted: %d' % count                 
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
        print '   Invalid stream number'
        print '   Only streams >= 1 allowed for archival analysis'
else:
    print ' QUIT: User request'
    sys.exit(0)
    

print
print ' **** END run_archival.py ****'
"""