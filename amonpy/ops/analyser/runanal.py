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

    celery worker --app=analyser --concurrency=1 -l info

    where dbaccess.txt contans a string in dictionary format,
    containing the information required to access the database

    Each alert will be saved to DB, and also written to XML file (in VOEvent format)
    to the directory /network/server_events. AMON client will send this events in the future
    to GCN and delete each xml fiel after it has been sent.
"""
from __future__ import absolute_import
from amonpy.ops.analyser.celery import app
from celery import Task
#from celery import current_app
#from celery.contrib.methods import task_method
#from celery.contrib.methods import task
from celery.result import AsyncResult

import sys, shutil
import subprocess

# AmonPy modules:
from amonpy.dbase.db_classes import Alert, AlertLine, AlertConfig, exAlertConfig, exAlertArchivConfig, event_def, AlertConfig2
from amonpy.dbase.db_classes import Event
import amonpy.dbase.db_populate_class as db_populate_class
import amonpy.dbase.db_read as db_read
import amonpy.dbase.db_write as db_write
import amonpy.dbase.db_delete as db_delete
import amonpy.dbase.alert_to_voevent as alert_to_voevent
import amonpy.dbase.hesealert_to_voevent as hesealert_to_voevent
import amonpy.dbase.ehealert_to_voevent as ehealert_to_voevent
import amonpy.dbase.ofualert_to_voevent as ofualert_to_voevent
#from amonpy.anal.analysis import anal, 
from amonpy.anal import analysis
from amonpy.anal import alert_revision
#import dialog_choice
#import input_text_window
import amonpy.dbase.email_alerts as email_alerts

# 3rd party modules
from time import time
from datetime import datetime, timedelta
from operator import itemgetter, attrgetter
import ConfigParser, netrc
#import wx
import multiprocessing
import ast
import os

# print
# print ' **** EXECUTING runanal.py ****'

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
        config_fname = '/home/amon/amon_code/AmonPy/amonpy/amon.ini'
        Config = ConfigParser.ConfigParser()
        Config.read(config_fname)
        self.HostFancyName = Config.get('database', 'host_name')
        nrc_path = Config.get('dirs', 'amonpydir') + '.netrc'
        nrc = netrc.netrc(nrc_path)

        self.UserFancyName = nrc.hosts[self.HostFancyName][0]
        self.PasswordFancy = nrc.hosts[self.HostFancyName][2]
        self.DBFancyName = Config.get('database', 'realtime_dbname')
        self.alertDir = Config.get('dirs', 'alertdir')
	self.prodMachine = eval(Config.get('machine', 'prod'))

        print
        print ' USING TEST ALERT CONFIG'
        self.config = exAlertConfig()
        self.archiv_config = exAlertArchivConfig()
        self.config.forprint()
        self.event_streams = [0,1,7]  # testing streams
        self.stream_num = self.config.stream
        self.stream_num2 = self.archiv_config.stream
        self.max_id=db_read.alert_max_id(self.stream_num,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
            # sort the events!!1
        print
        print "MAX ALERT ID IN DATABASE IS"
        print self.max_id
        if (self.max_id==None):
            self.max_id=-1
        print
        # to prevent sendinf IceCube's EHE and HESE if they overlap
        #self.run_check=0
        #self.event_check=0
        #self.rev_check=0
        #self.sendAlert=True
        print ' STARTING ANALYSIS SERVER'
        (self.server_p,self.client_p) = multiprocessing.Pipe()
        self.anal_p = multiprocessing.Process(target=analysis.anal,
                    args=((self.server_p,self.client_p),self.config,self.max_id))
        self.anal_p.start()
    #@app.task(filter=task_method, name='analser.runanal.AnalRT.run')
    def run(self,evstream, evnumber,evrev):
        self.Event.stream = evstream
        self.Event.id     = evnumber
        self.Event.rev    = evrev
        eventInAlertLine = False
        eventHESE = False
        signal_t = 0.
        hese_charge=0.
        # For check if EHE and HESE are the same run num and event num
        #run_id=0
        #event_id=0
        #rev_id=0

        alertDuplicate=False # for HESE and EHE overalp

        t1 = time()

        events=db_read.read_event_single(evstream,evnumber,evrev,self.HostFancyName,
                                        self.UserFancyName,self.PasswordFancy,self.DBFancyName)
        params=db_read.read_parameters(evstream,evnumber,evrev,self.HostFancyName,
                                        self.UserFancyName,self.PasswordFancy,self.DBFancyName)

        t2 = time()
        print '   Read time: %.2f seconds' % float(t2-t1)
        print ' lenght of parameters %s' % len(params)
        if (len(params)>0):
            for i in range(len(params)):
                # if ((params[i].name=='varname') and (params[i].value=='heseEvent')):
                if (params[i].name=='signal_trackness'):
                    eventHESE=True
                    signal_t = params[i].value
                    print 'Signal trackenss %.2f' % signal_t
                if (params[i].name=='causalqtot'):
                    hese_charge=params[i].value
                if (params[i].name=='run_id'):
                    run_id=params[i].value
                if (params[i].name=='event_id'):
                    event_id=params[i].value
        # note: change signal_t to 0.1 after unblinding
        # check if EHE and HESE are duplicates of each other
        if (events.stream==10):
            events_duplicate=db_read.read_event_single(11,evnumber,evrev,self.HostFancyName,
                                        self.UserFancyName,self.PasswordFancy,self.DBFancyName)
            if events_duplicate is None:
                alertDuplicate=False
            else:
                alertDuplicate=True
            print "alert duplicate"
            print alertDuplicate
        if (events.stream==11):
            events_duplicate=db_read.read_event_single(10,evnumber,evrev,self.HostFancyName,
                                        self.UserFancyName,self.PasswordFancy,self.DBFancyName)
            if events_duplicate is None:
                alertDuplicate=False
            else:
                alertDuplicate=True
            print "alert duplicate"
            print alertDuplicate
        #if ((events.stream==10) or (events.stream==11)):
            #if ((run_id==self.run_check) and (event_id==self.event_check) and (events.rev==self.rev_check)):
            #    self.sendAlert=False
            #    self.run_check=run_id
            #    self.event_check=event_id
            #    self.rev_check=events.rev
            #else:
            #    self.sendAlert=True
        #else:
            #self.sendAlert=True

        if ((eventHESE==True) and (signal_t >= 0.1) and (hese_charge>=6000.)):
            # send HESE events directly to GCN first
            xmlForm=hesealert_to_voevent.hesealert_to_voevent([events],params,alertDuplicate)
            fname=self.alertDir + 'amon_hese_%s_%s_%s.xml' \
                % (events.stream, events.id, events.rev)
            f1=open(fname, 'w+')
            f1.write(xmlForm)
            f1.close()
            """
                        modified from
                        https://github.com/timstaley/fourpiskytools/blob/master/fourpiskytools/comet.py
                        Send a voevent to a broker using the comet-sendvo publishing tool.
                        Args:
                        host (string): IP address or hostname of VOEvent broker.
                        port (int): Port, default 8098.
                        code this up!
                        comment out code bellow if you do not have comet installed!
            """
            if (self.prodMachine==True):
                try:
                    cmd = ['comet-sendvo']
                    cmd.append('--file=' + fname)
                    # just for dev to prevent sending hese both from dev and pro machine
                    print "uncoment this if used on production"
                    subprocess.check_call(cmd)
                except subprocess.CalledProcessError as e:
                    print "Send HESE VOevent alert failed"
                    #logger.error("send_voevent failed")
                    raise e
                else:
                    shutil.move(fname, self.alertDir+"archive/")
            else:
                shutil.move(fname, self.alertDir+"archive/")
        if (eventHESE==True):
            email_alerts.alert_email([events],params)

        if (events.stream==11):
            if (events.type=="observation"):
                xmlForm=ehealert_to_voevent.ehealert_to_voevent([events],params, alertDuplicate)
                fname=self.alertDir + 'amon_icecube_ehe_%s_%s_%s.xml' \
                    % (events.stream, events.id, events.rev)
                f1=open(fname, 'w+')
                f1.write(xmlForm)
                f1.close()
                if (self.prodMachine == True):
                    try:
                        print "EHE sent to GCN"
                        cmd = ['comet-sendvo']
                        cmd.append('--file=' + fname)
                        subprocess.check_call(cmd)
                    except subprocess.CalledProcessError as e:
                        print "Send IceCube EHE VOevent alert failed"
                        #logger.error("send_voevent failed")
                        raise e
                    else:
                        shutil.move(fname, self.alertDir+"archive/")
                else:
                    shutil.move(fname, self.alerDir+"archive/")
            email_alerts.alert_email([events],params)

        if ((events.stream==12) or (events.stream==13) or (events.stream==14) or (events.stream==15)):
            if (events.type == "observation"):
                xmlForm=ofualert_to_voevent.ofualert_to_voevent([events],params)
                fname=self.alertDir + 'amon_icecube_coinc_%s_%s_%s.xml' \
                    % (events.stream, events.id, events.rev)
                f1=open(fname, 'w+')
                f1.write(xmlForm)
                f1.close()
                if (self.prodMachine == True):
                    try:
                        print "OFU created"
                        cmd = ['comet-sendvo']
                        cmd.append('--file=' + fname)
                        subprocess.check_call(cmd)
                    except subprocess.CalledProcessError as e:
                        print "Send IceCube OFU VOevent alert failed"
                        #logger.error("send_voevent failed")
                        raise e
                    else:
                        shutil.move(fname, self.alertDir+"archive/")
                else:
                    shutil.move(fname, self.alertDir+"archive/")
        #events.forprint()
        # put events in temporal order
        #events = sorted(events,key=attrgetter('datetime'))
        # send events to the analysis process
        print '   Sending events'
        t1 = time()
        #for ev in events:
            #self.client_p.send(ev)
        # do not analyse OFU for now, not approved by IceCube to use in analysis
        if (isinstance(events,Event) and (events.stream!=12) and (events.stream!=13) and (events.stream!=14) and (events.stream!=15)) :
            #self.client_p.send(events)
            print "NOT DOING ANALYSIS FOR NOW"
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
        if (len(alerts) > 0 and alerts != 'Empty' and alerts != 'Problem' and alerts[0] !=True):
            # populate alertline class
            #alerts[0].forprint()
            #alertlines=db_populate_class.populate_alertline(alerts)
            #print '   %d alertlines generated' % len(alertlines)
            print ' ANALYSIS COMPLETE'

            print ' WRITING ANALYSIS RESULTS TO THE DATABASE'
            # modify it later to append to database, not to rewrite
            if (self.stream_num !=0):    # don't take any action for stream zero in testing phase

                for alert in alerts:
                    streams=[] # for case where old alerts are with current event (just diff rev)
                    ids=[]  # for case where old alerts are with current event (just diff rev)
                    streams_old=[] # for case where old alerts are without current event
                    ids_old=[] # for case where old alerts are without current event
                    alertIdChange=False
                    # check to see if older alerts with these events existed
                    num_events=len(alert.events)
                    for j in xrange(num_events):
                        streams+=[alert.events[j].stream]
                        ids+=[alert.events[j].id]
                        if not ((alert.events[j].stream == events.stream) and
                            (alert.events[j].id == events.id) and
                            (alert.events[j].rev == events.rev)):
                             streams_old+=[alert.events[j].stream]
                             ids_old+=[alert.events[j].id]
                    lines_db=db_read.read_alertline_events2(streams,ids,
                                             self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
                    #lines_db_old=db_read.read_alertline_events2(streams_old,ids_old,
                     #                        self.HostFancyName,
                      #                       self.UserFancyName,
                       #                      self.PasswordFancy,
                        #                     self.DBFancyName)
                    if not (len(lines_db)==0): # alerts with these events were found in the past, check revisions
                        alert=alert_revision.check_old_alert_rev(lines_db, alert)
                    else:
                        # check alert number from DB
                        maxid=db_read.alert_max_id(self.stream_num,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
                        if (maxid==None):
                            maxid=-1
                        alert.id=maxid+1

                    #if not (len(lines_db_old)==0): # alerts with these events were found in the past, check revisions
                     #   alert=alert_revision.check_old_alert_rev2(lines_db_old, alert)
                    alertlines=db_populate_class.populate_alertline([alert])
                    db_write.write_alert(self.stream_num,self.HostFancyName,
                                            self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName,[alert])
                    db_write.write_alertline(self.HostFancyName,
                                                      self.UserFancyName,
                                                      self.PasswordFancy,
                                                      self.DBFancyName,alertlines)
                #alertlines=db_populate_class.populate_alertline(alerts)
                #db_write.write_alert(self.stream_num,self.HostFancyName,
                 #                            self.UserFancyName,
                  #                           self.PasswordFancy,
                   #                          self.DBFancyName,alerts)
                #db_write.write_alertline(self.HostFancyName,
                 #                                     self.UserFancyName,
                  #                                    self.PasswordFancy,
                   #                                   self.DBFancyName,alertlines)
                    # write alert to the directory from where AMON client will read it and delete
                    # it after sending it to GCN in the future
                xmlForm=alert_to_voevent.alert_to_voevent(alerts)
                fname=self.alertDir + 'amon_%s_%s_%s.xml' \
                    % (alerts[0].stream, alerts[0].id, alerts[0].rev)
                f1=open(fname, 'w+')
                f1.write(xmlForm)
                f1.close()
                """
                        modified from
                        https://github.com/timstaley/fourpiskytools/blob/master/fourpiskytools/comet.py
                        Send a voevent to a broker using the comet-sendvo publishing tool.
                        Args:
                        host (string): IP address or hostname of VOEvent broker.
                        port (int): Port, default 8098.
                        code this up!
                        comment out code bellow if you do not have comet installed!
                """
                if (self.prodMachine==True):
                    try:
                        print "alert created"
                        cmd = ['comet-sendvo']
                        cmd.append('--file=' + fname)
                        subprocess.check_call(cmd)
                    except subprocess.CalledProcessError as e:
                        print "Send VOevent alert failed"
                        #logger.error("send_voevent failed")
                        raise e
                    else:
                        shutil.move(fname, self.alertDir+"archive/")
                            #shutil.move(fname, "archive/"+fname)
                else:
                    shutil.move(fname, self.alertDir+"archive/") 
            else:
                print '   Invalid stream number'
                print '   Only streams >= 1 allowed for testing analysis'
            return "%d alerts found" % (len(alerts),)
        elif(alerts[0] ==True):
            # call archival analysis for a very late arrival event that is outside of time
            # buffer
            print "Call archival"
            #print "True or false, true is correct"
            #print alerts[0]
            #print "Event"
            #alerts[1].forprint()
            timeEvent = alerts[1].datetime
            events = []
            TimeSlice = 3.*self.config.deltaT
            TimeStart = timeEvent - timedelta(seconds=1.5*self.config.deltaT)
            TimeStart = str(TimeStart)
            events=db_read.read_event_timeslice_streams_latest(self.event_streams,
                                    TimeStart,TimeSlice,self.HostFancyName,
                                    self.UserFancyName,self.PasswordFancy,self.DBFancyName)
            # also read the highest alert number within this stream
            max_id=db_read.alert_max_id(self.stream_num2,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
            # sort the events!!1
            print "max_id is"
            print max_id
            if (max_id==None):
                max_id=-1
            # code the function bellow in module analysis
            alerts_archive = analysis.alerts_late(events,alerts[1],self.archiv_config, max_id)
            if (len(alerts_archive)!=0):
                #alertlines=db_populate_class.populate_alertline(alerts_archive)
                #print '   %d alertlines generated' % len(alertlines)
                print ' ARCHIVAL ANALYSIS COMPLETE'

                print ' WRITING ANALYSIS RESULTS TO THE DATABASE'

                if (self.stream_num2 !=0):    # don't take any action for stream zero in testing phase

                    # first check if that archival alert is already in DB
                    # this is important since out of buffer event can be analysed twice
                    # in case that another late event in coincidence gets written in DB
                    # simultaneously while we are reading a given timeslice. The second late event will be
                    # read within this time slice in same cases before an information about it
                    # being written is passed to this module via
                    # as a regular incoming event.
                    # It will be analysed 2nd time when
                    # celery delivers message to this module about it being written to DB.
                    # This never happens for real real-time events since they are not
                    # read from DB using time-slice, but passed one-by-one to this module,
                    # and read one-by-one from DB. After that they are kept in time buffer
                    # and never read as a time-slice bunch from DB.

                    #
                    try:
                        # check if late arrival event with same (id, rev, and stream) has already being analysed and contributed to alers
                        # in rare cases when it could be read from a timeslice around a previous late arrival
                        # event
                        alertlines_written=db_read.read_alertline_events([alerts[1].stream],[alerts[1].id],
                                             [alerts[1].rev],self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
                    except:
                        print "Alert line cannot be read, probably not written yet"
                        alertlines_written = []
                    # check if this out-of-buffer event was already analysed in case in close-in time arrival
                    # with another out-of-buffer event

                    if not ((len(alertlines_written)>0) and (alertlines_written[0].stream_event==alerts[1].stream) and
                             (alertlines_written[0].id_event==alerts[1].id) and
                             (alertlines_written[0].rev_event==alerts[1].rev)):
                        # the same event was not analysed, what about an event with diff. revision


                        for alert_ar in alerts_archive:
                            streams_ar=[]
                            ids_ar=[]
                            alertIdChangeAr=False
                            # check to see if older alerts with these events existed
                            num_events_ar=len(alert_ar.events)
                            for j in xrange(num_events_ar):
                                streams_ar+=[alert_ar.events[j].stream]
                                ids_ar+=[alert_ar.events[j].id]
                            lines_db_ar=db_read.read_alertline_events2(streams_ar,ids_ar,
                                                                       self.HostFancyName,
                                                                       self.UserFancyName,
                                                                       self.PasswordFancy,
                                                                       self.DBFancyName)

                            if not (len(lines_db_ar)==0): # alerts with these events were found in the past, check revisions
                                alert_ar=alert_revision.check_old_alert_rev(lines_db_ar, alert_ar)
                            else:
                                # check alert number from DB
                                maxid=db_read.alert_max_id(self.stream_num,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName)
                                if (maxid==None):
                                    maxid=-1
                                alert.id=maxid+1

                            alertlines=db_populate_class.populate_alertline([alert_ar])
                            db_write.write_alert(self.stream_num2,self.HostFancyName,
                                             self.UserFancyName,
                                             self.PasswordFancy,
                                             self.DBFancyName,[alert_ar])
                            db_write.write_alertline(self.HostFancyName,
                                                      self.UserFancyName,
                                                      self.PasswordFancy,
                                                      self.DBFancyName,alertlines)

                        # write alert to the directory from where AMON client will read it and delete
                        # it after sending it to GCN in the future
                        xmlForm=alert_to_voevent.alert_to_voevent(alerts_archive)
                        fname=self.alertDir + 'amon_%s_%s_%s.xml' \
                        % (alerts_archive[0].stream, alerts_archive[0].id, alerts_archive[0].rev)
                        f1=open(fname, 'w+')
                        f1.write(xmlForm)
                        f1.close()
                        """
                        modified from
                        https://github.com/timstaley/fourpiskytools/blob/master/fourpiskytools/comet.py
                        Send a voevent to a broker using the comet-sendvo publishing tool.
                        Args:
                        host (string): IP address or hostname of VOEvent broker.
                        port (int): Port, default 8098.
                        code this up!
                        comment out code bellow if you do not have comet installed!
                        """
                        if (self.prodMachine==True):
                            try:
                                print "AMON alert created"
                                cmd = ['comet-sendvo']
                                cmd.append('--file=' + fname)
                                subprocess.check_call(cmd)
                            except subprocess.CalledProcessError as e:
                                print "Send VOevent alert failed"
                                #logger.error("send_voevent failed")
                                raise e
                            else:
                                shutil.move(fname, self.alertDir+"archive/")
                                #shutil.move(fname, "archive/"+fname)
                        else:
                            shutl.move(fname, self.alertDir+"archive/")
                    else:
                        print "Late event already analysed"
                        alerts_archive=[]
                else:
                    print '   Invalid stream number'
                    print '   Only streams >= 1 allowed for testing analysis'
            if len(alerts_archive)!=0:
                return "%d alerts found" % (len(alerts_archive),)
            else:
                return "No alerts"

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
