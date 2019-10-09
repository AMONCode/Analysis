"""@package amon_server
- receives events from a client using HTTP protocols in
an xml form (VOEvents),
- converts then into Event and Parameter objects
- writes them into DB using twisted adbapi connection pool that
performs DB transactions in a separate threat, thus keeping the code asynchronous
- send a message to AMON analysis code about new event (event stream, id and rev)
"""
from __future__ import absolute_import
from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
from builtins import range
from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import Site, NOT_DONE_YET
from twisted.enterprise import adbapi
from twisted.python import log

import cgi, os, getopt, sys, shutil
import configparser,netrc, ast
from amonpy.tools.config import AMON_CONFIG
from datetime import datetime, timedelta
from time import time
import jsonpickle

from amonpy.dbase.db_classes import Alert, AlertLine, AlertConfig, exAlertConfig, exAlertArchivConfig, event_def, AlertConfig2
from amonpy.dbase.db_classes import Event
from amonpy.dbase import db_write, db_read, db_delete
from amonpy.dbase import voevent_to_event

from amonpy.analyses.amon_streams import streams

#from amonpy.anal import analysis
#from amonpy.anal import alert_revision
import amonpy.dbase.email_alerts as email_alerts

from celery.result import AsyncResult
from amonpy.ops.server.celery import app
from amonpy.ops.server.buffer import EventBuffer, bufdur
#from amonpy.ops.server.util import DatetimeHandler
#jsonpickle.handlers.registry.register(datetime, DatetimeHandler)

#importing configurations for analyses
from amonpy.analyses.ICSwift import *
from amonpy.analyses.ICHAWC import *

@app.task
def error_handler(uuid):
    myresult = AsyncResult(uuid)
    exc = myresult.get(propagate=False)
    print('Task {0} raised exception: {1!r}\n{2!r}'.format(
          uuid, exc, myresult.traceback))


class EventManager(Resource):
    isLeaf = True

    print('Configuring AMON Databases')
    #Configure AMON databases
    #amon_config_fname = '/Users/hugo/Software/Analysis/AmonPy/amonpy/amon.ini'
    #AmonConfig = ConfigParser.ConfigParser()
    #AmonConfig.read(amon_config_fname)
    HostFancyName = AMON_CONFIG.get('database', 'host_name')#AmonConfig.get('database', 'host_name')
    #nrc_path = AMON_CONFIG.get('dirs', 'amonpydir') + '.netrc'#AmonConfig.get('dirs', 'amonpydir') + '.netrc'
    #nrc = netrc.netrc(nrc_path)
    UserFancyName=AMON_CONFIG.get('database', 'username')#nrc.hosts[HostFancyName][0]
    PasswordFancy=AMON_CONFIG.get('database','password')#nrc.hosts[HostFancyName][2]
    DBFancyName = AMON_CONFIG.get('database', 'realtime_dbname')#AmonConfig.get('database', 'realtime_dbname')
    alertDir = AMON_CONFIG.get('dirs', 'alertdir')#AmonConfig.get('dirs', 'alertdir')

    #eventlist = []
    #paramlist = []
    microsec = 0.
    counter = 1

    print("Event manager is %d" % counter)
    dbpool = adbapi.ConnectionPool("MySQLdb", db = DBFancyName,
                                            user = UserFancyName,
                                            passwd = PasswordFancy,
                                            host = HostFancyName,
                                            cp_min=1,
                                            cp_max=1,
                                            cp_reconnect=True)

    print('Configuring Analyses')
    amon_analysis_fname = '/storage/home/hza53/Software/Analysis/AmonPy/amonpy/analyses/amon_analysis.ini'
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

    def render_POST(self,request):
            path = "/storage/home/hza53/work/AMON/Test_server/"#"/Users/hugo/AMON/Test_new_server/"
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
                print('DB Stuff')
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
                #dd.addCallbacks(self.printResult, self.printError)
                #return dd

            def printError(error):
                print("Got Error: %r" % error)
                error.printTraceback

            def printResult(result):
                print('Event written to DB and buffers')
                evt = result
                date = evt[0].datetime
                print(type(evt[0].datetime))

                for i in range(len(EventManager.eventBuffers)):
                    if evt[0].stream in EventManager.eventBuffers[i].event_streams:

                        #check if event is already in buffer
                        inBuffer = False
                        #evenout = Event(-1,-1,-1)

                        if len(EventManager.eventBuffers[i].events)>0:
                            for e in EventManager.eventBuffers[i].events:
                                if((evt[0].stream == e.stream) and (evt[0].id == e.id)):
                                    if(evt[0].rev == e.rev):
                                        print("Event is already in the buffer. It will not be added to the buffer.")
                                        inBuffer = True
                                        break
                                    elif (evt[0].rev < e.rev):
                                        print("Old event revision arrived later than a newer one.")
                                        print("No analysis for this obsolete event")
                                        inBuffer = True
                                        break
                                    else:
                                        print("Old event revision in the buffer, remove it.")
                                        EventManager.eventBuffers[i].events.pop(b[i].events.index(e))
                                        #buffers[i].events.append(event)
                                        #break
                            if inBuffer is False:

                                if date < EventManager.latest[i]:
                                    print('  reordering analysis buffer due to latent event')
                                    EventManager.eventBuffers[i].events = sorted(EventManager.eventBuffers[i].events,key=attrgetter('datetime'),reverse=True)
                                else:
                                    EventManager.latest[i] = date
                                    EventManager.eventBuffers[i].events = sorted(EventManager.eventBuffers[i].events,key=attrgetter('datetime'),reverse=True)

                                # Clean the buffer according to the configuration buffer time
                                while bufdur(EventManager.eventBuffers[i].events) > EventManager.alertConfig[i].bufferT:
                                    eventout = EventManager.eventBuffers[i].events.pop()
                                    if ((eventout.stream==evt[0].stream) and (eventout.id==evt[0].id) and (eventout.rev==evt[0].rev)):
                                        print('The new event came late into the buffer. Not using it')

                                try:
                                    evt[0].datetime = evt[0].datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
                                except AttributeError:
                                    pass

                                print('Send celery task')
                                max_id = db_read.alert_max_id(EventManager.alertConfig[i].stream,HostFancyName,
                                                                   UserFancyName,
                                                                   PasswordFancy,
                                                                   DBFancyName)

                                #globals()[EventManager.analyses[i][2]].apply_async((EventManager.eventBuffers[i].toJSON(),EventManager.alertConfig[i],,EventManager.max_id[i]),
                                globals()[EventManager.analyses[i][2]].apply_async((EventManager.eventBuffers[i].toJSON(),max_id,jsonpickle.encode(evt[0])),
                                link_error=error_handler.s(),
                                queue=EventManager.analyses[i][2])

                                print("Adding event to buffer")#for stream %d"%(event[0].stream)
                                EventManager.eventBuffers[i].events.append(evt[0])
                                # try:
                                #     evt[0].datetime = evt[0].datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
                                # except AttributeError:
                                #     pass
                                #print 'Finish adding event to DB and Buffers'
                        else:
                            print('Starting buffer. Adding first event')
                            EventManager.latest[i]=date
                            try:
                                evt[0].datetime = evt[0].datetime.strftime("%Y-%m-%dT%H:%M:%S.%f")
                            except AttributeError:
                                pass

                            EventManager.eventBuffers[i].events.append(evt[0])
                            #buffers[i].addEvent(event,EventManager.alertConfig[i])
                            #print 'Send celery task'
                            #globals()[EventManager.analyses[i][2]].apply_async((EventManager.eventBuffers[i].toJSON(),EventManager.alertConfig[i],,EventManager.max_id[i]),
                            #globals()[EventManager.analyses[i][2]].apply_async((EventManager.eventBuffers[i].toJSON(),EventManager.max_id[i]),
                            #link_error=error_handler.s(),
                            #queue=EventManager.analyses[i][2])



            def Finish():
                # do not call this function in real-time settings
                EventManager.dbpool.close()

            # Start of render_POST
            # Get the file name of the VOEvent

            self.headers = request.getAllHeaders()
            #print self.headers
            try:
                postfile = cgi.FieldStorage(
                    fp = request.content,
                    headers = self.headers,

                    environ = {'REQUEST_METHOD':'POST',
                            'CONTENT_TYPE': self.headers['content-type'],
                            }
                    )
            except Exception as e:
                print('something went wrong: ' + str(e))

            #print  request.content.getvalue()
            fname=self.headers['content-name']

            fp = open(path+"server_tmp_events/"+fname, "w")
            fp.write(request.content.getvalue())
            fp.close()

            #Convert VOEvent into AMON event

            evpar = voevent_to_event.make_event(path+"server_tmp_events/"+fname)
            event  = evpar[0]
            evParam = evpar[1]
            shutil.move(path+"server_tmp_events/"+fname, path+"server_archive_events/"+fname)
            #event[0].forprint()

            #if not (evParam==[]):
                #evParam[0].forprint()


            #Write event to the DB and to the buffer(s)
            print('Write event')
            d = writeEventParam(event, evParam,EventManager.eventBuffers)

            print('Send event to celery task')
            d.addCallbacks(printResult,printError)


            request.finish()
            return NOT_DONE_YET
