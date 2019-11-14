"""@package amon_server
- receives events from a client using HTTP protocols in
an xml form (VOEvents),
- converts then into Event and Parameter objects
- writes them into DB using twisted adbapi connection pool that
performs DB transactions in a separate threat, thus keeping the code asynchronous
- send a message to AMON analysis code about new event (event stream, id and rev)
"""
#Twisted modules
from __future__ import absolute_import
from __future__ import print_function
from builtins import str
from builtins import range
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.enterprise import adbapi
from twisted.python import log

import traceback

import cgi, os, getopt, sys, shutil
import configparser,netrc, ast
from amonpy.tools.config import AMON_CONFIG
from datetime import datetime, timedelta
from time import time
import jsonpickle
import MySQLdb

from amonpy.dbase.db_classes import Alert, AlertLine, AlertConfig, exAlertConfig, exAlertArchivConfig, event_def, AlertConfig2
from amonpy.dbase.db_classes import Event
from amonpy.dbase import db_write, db_read, db_delete
from amonpy.dbase import voevent_to_event

from amonpy.analyses.amon_streams import streams, inv_streams,alert_streams,inv_alert_streams

#from amonpy.anal import analysis
#from amonpy.anal import alert_revision
import amonpy.dbase.email_alerts as email_alerts

from celery.result import AsyncResult
from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer, bufdur
#from amonpy.ops.server.util import DatetimeHandler
#jsonpickle.handlers.registry.register(datetime, DatetimeHandler)

import traceback

#Importing configurations for analyses
from amonpy.analyses.ICSwift import *
from amonpy.analyses.ICHAWC import *
from amonpy.analyses.ICHESE_EHE import *
from amonpy.analyses.ICOFU import *
from amonpy.analyses.ICGFU import *
from amonpy.analyses.HAWCGRB import *
from amonpy.analyses.ICGoldBronze import *

@app.task
def error_handler(uuid):
    """Function to handle possible errors with celery workers"""
    myresult = AsyncResult(uuid)
    exc = myresult.get(propagate=False)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, exc, myresult.traceback))

class ReconnectingConnectionPool(adbapi.ConnectionPool):
    """Reconnecting adbapi connection pool for MySQL.
    This class improves on the solution posted at
    http://www.gelens.org/2008/09/12/reinitializing-twisted-connectionpool/
    by checking exceptions by error code and only disconnecting the current
    connection instead of all of them.
    Also see:
    http://twistedmatrix.com/pipermail/twisted-python/2009-July/020007.html
    """
    def _runInteraction(self, interaction, *args, **kw):
        try:
            return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)
        except MySQLdb.OperationalError as e:
            if e[0] not in (2006, 2013):
                raise
            log.msg("RCP: got error %s, retrying operation" %(e))
            conn = self.connections.get(self.threadID())
            self.disconnect(conn)
            # try the interaction again
            return adbapi.ConnectionPool._runInteraction(self, interaction, *args, **kw)


class EventManager(Resource):
    """
    Class to handle upcoming events from twisted server application
    """
    isLeaf = True

    print('Configuring AMON Databases')
    #Configure AMON databases

    HostFancyName = AMON_CONFIG.get('database', 'host_name')#AmonConfig.get('database', 'host_name')
    UserFancyName=AMON_CONFIG.get('database', 'username')#nrc.hosts[HostFancyName][0]
    PasswordFancy=AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
    DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#AmonConfig.get('database', 'realtime_dbname')
    alertDir = AMON_CONFIG.get('dirs', 'alertdir')#AmonConfig.get('dirs', 'alertdir')
    AmonPyDir = AMON_CONFIG.get('dirs','amonpydir')

    #eventlist = []
    #paramlist = []
    microsec = 0.
    counter = 1

    print("Event manager is %d" % counter)
    # dbpool = adbapi.ConnectionPool("MySQLdb", db = DBFancyName,
    #                                         user = UserFancyName,
    #                                         passwd = PasswordFancy,
    #                                         host = HostFancyName,
    #                                         cp_min=1,
    #                                         cp_max=1,
    #                                         cp_reconnect=True)

    dbpool = ReconnectingConnectionPool("MySQLdb", db = DBFancyName,
                                            user = UserFancyName,
                                            passwd = PasswordFancy,
                                            host = HostFancyName,
                                            cp_min=1,
                                            cp_max=1,
                                            cp_reconnect=True)



    print('Configuring Analyses')
    amon_analysis_fname = os.path.join(AmonPyDir,'analyses/amon_analysis.ini')
    AmonAnalysis=configparser.ConfigParser()
    AmonAnalysis.read(amon_analysis_fname)
    analyses = ast.literal_eval(AmonAnalysis.get('active_analysis','analyses'))

    alertConfig = []
    archiveConfig = []
    eventBuffers = []
    latest=[]

    for i in range(len(analyses)):
        print('Analysis: %d'%(i+1))
        #func.append(globals()[analyses[i][2]])
        alertConfig.append(globals()[analyses[i][-1]+"_config"]())
        eventBuffers.append(EventBuffer())
        for j in range(len(analyses[i])-1):
            print('   %s '%(analyses[i][j]))
            eventBuffers[i].addStream(streams[analyses[i][j]])
        print(eventBuffers[i].event_streams)
        latest.append(datetime(1900,1,1,0,0,0,0))

    path = AMON_CONFIG.get('dirs','serverdir')
    tmp_path = os.path.join(path, 'server_tmp_events')
    archive_path = os.path.join(path, 'server_archive_events')
    if not os.path.isdir(tmp_path):
        os.makedirs(tmp_path)
    if not os.path.isdir(archive_path):
        os.makedirs(archive_path)

    def render_POST(self,request):
            """ Main function where events are written to DB, then send to celery workers."""

            path = AMON_CONFIG.get('dirs','serverdir')

            def _writeEventParam(transaction, event, evparam,buffers):
                # this will run in a separate thread, allowing us to use series of queries
                # without blocking the rest of the code
                # take microsecond part from datetime because of the older versions of mysql

                if '.' in str(event[0].datetime):
                    microsec=int(float('.'+str(event[0].datetime).split('.')[1])*1000000)
                        #print 'microseconds %d' % microsec
                else:
                    microsec=0.0
                #Save in DB
                event_timefull=event[0].datetime
                event_time = event_timefull.replace(microsecond=0)
                transaction.execute("""INSERT INTO event VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                %s,%s,%s,%s,%s,%s,%s,%s,%s)""",(event[0].stream,
                                event[0].id,
                                event[0].rev,
                                event_time,
                                microsec,
                                event[0].dec,
                                event[0].RA,
                                event[0].sigmaR,
                                event[0].nevents,
                                event[0].deltaT,
                                event[0].sigmaT,
                                event[0].false_pos,
                                event[0].pvalue,
                                event[0].type,
                                event[0].point_RA,
                                event[0].point_dec,
                                event[0].longitude,
                                event[0].latitude,
                                event[0].elevation,
                                event[0].psf_type,
                                0))
                plenght=len(evparam)

                for i in range(plenght):
                    transaction.execute("""INSERT INTO parameter VALUES (%s,%s,%s,%s,%s,%s)""",
                               (evparam[i].name,
                                evparam[i].value,
                                evparam[i].units,
                                evparam[i].event_eventStreamConfig_stream,
                                evparam[i].event_id,evparam[i].event_rev))

                return event#, buffers

            def writeEventParam(event, evparam,buffers):
                return EventManager.dbpool.runInteraction(_writeEventParam, event, evparam,buffers)

            def printError(error):
                print("Got Error: %r" % error)
                error.printTraceback

            def printResult(result):
                evt = result

                print('Event stream: ',inv_streams[evt[0].stream])
                for i in range(len(EventManager.eventBuffers)):
                    if evt[0].stream in EventManager.eventBuffers[i].event_streams:

                        #Checking the datetime format so that it can be jsonpickled
                        try:
                            evt[0].datetime = evt[0].datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
                        except AttributeError:
                            print('Something bad happened')
                            pass

                        print('Sending to celery task')
                        globals()[EventManager.analyses[i][-1]].apply_async((jsonpickle.encode(evt[0]),),
                        link_error=error_handler.s(),
                        queue=EventManager.analyses[i][-1])


            def Finish():
                # do not call this function in real-time settings
                EventManager.dbpool.close()

            # Start of render_POST
            # Get the file name of the VOEvent

            headers_b = request.getAllHeaders() # getAllHeaders gives byte strings...
            #self.headers = { key.decode('latin1'): headers_b.get(key).decode('latin1') for key in headers_b.keys() } # ...we decode them to have text strings
            self.headers = request.getAllHeaders()

            try:
                postfile = cgi.FieldStorage(
                    fp = request.content,
                    headers = self.headers,

                    environ = {'REQUEST_METHOD':'POST',
                            'CONTENT_TYPE': str(self.headers[b'content-type']),
                            }
                    )
            except Exception as e:
                print('something went wrong: ' + str(e))
                print(traceback.print_exc())

            fname=self.headers[b'content-name'].decode('latin1')
            print("")
            print("Received file : {}".format(fname))

            fp = open(os.path.join(path,"server_tmp_events",fname),"w")
            fp.write(request.content.getvalue().decode('latin1'))
            #fp.write(request.content.getvalue())
            fp.close()

            #Convert VOEvent into AMON event and move VOEvent file to the archive directory

            evpar = voevent_to_event.make_event(os.path.join(path,"server_tmp_events",fname))
            event  = evpar[0]
            evParam = evpar[1]
            fname_new = os.path.join(path,"server_archive_events",fname)
            if os.path.exists(fname_new):
                fname2 = fname.split('.')[0] + "_" +\
                        datetime.utcnow().strftime("%Y_%m_%d_%H_%M") + '.xml'
                fname_new = os.path.join(path,"server_archive_events", fname2)
            shutil.move(os.path.join(path,"server_tmp_events",fname), fname_new)

            #Write event to the DB and to the buffer(s)
            #print('Write event')
            d = writeEventParam(event, evParam,EventManager.eventBuffers)
            print('Event written to DB')

            print('Send event to celery tasks')
            d.addCallbacks(printResult,printError)


            request.finish()
            print('Event processed')

            return NOT_DONE_YET
