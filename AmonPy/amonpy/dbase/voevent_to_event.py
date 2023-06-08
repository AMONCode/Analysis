#!/usr/bin/env python
"""
A module to create an instance of Event from VOEvent
Call function make_event from your program in order to use it.

Options:
    -h, --help      Display this help message.
    -s, --stdout    Send output to stdout.
    -o FILENAME, --outfile=FILENAME
                    Send output to file.
    -t, --text-string
                    Capture output as a text string, then write to stdout.
    -f, --force     Force: over-write output file without asking

"""
from __future__ import print_function

# Modified by G.T.from format_to_html.py by Roy D. Williams and Dave Kuhlmann
#

from builtins import str
import sys
import os
import getopt
#import VOEvent
#import Vutil
import VOEventLib.Vutil as Vutil

from datetime import datetime
from amonpy.dbase.db_classes import *

from io import StringIO

def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)

def make_event(source, o=sys.stdout):
    '''Makes an instance of Event class from a given VOEvent.
    '''
    # initialize Event and Parameter classes to be populated from this VOEvent
    event=[Event(1,1,0)]
    #evParam=[Parameter("energy",1,1,0)]

    v = Vutil.parse(source)
    """
    print>>o, 'VOEvent'
    print
    print>>o, 'IVORN %s' % v.get_ivorn()
    print
    """
    streamname=str(v.get_ivorn())
    len_sname=len(streamname)
    count, count1= 0, 0
    count2=0
    #count=streamname.index('/')
    #streamname2=streamname[count+1:]
    #count1=1+count+streamname2.index('/')
    #streamname3=streamname[count1+1:]
    #count2=1+count1+streamname3.index('/')
    #event[0].stream = int(streamname[count1+1:count2])
    #print "STREAM NAME %s" % event[0].stream
    #print
    event[0].configstream= 0 # change later to get revision from eventConfigTable event[0].stream

    #print>>o, '(ROLE IS %s)' % v.get_role()
    #print
    event[0].type=v.get_role()

    #print>>o, 'EVENT DESCRIPTION: %s\n' % v.get_Description()
    #print

    r = v.get_Reference()
    """
    if r:
        print>>o, 'Reference Name=%s, Type=%s, uri=%s' \
                    % (r.get_name(), r.get_type(), r.get_uri())
        print

    print>>o, 'WHO'
    print
    """

    who = v.get_Who()
    '''
    a = who.get_Author()
    print>>o, 'Title: %s'                        % Vutil.htmlList(a.get_title())
    print>>o, 'Name: %s'                         % Vutil.htmlList(a.get_contactName())
    print>>o, 'Email: %s'                        % Vutil.htmlList(a.get_contactEmail())
    print>>o, 'Phone: %s'                        % Vutil.htmlList(a.get_contactPhone())
    print>>o, 'Contributor: %s' % Vutil.htmlList(a.get_contributor())
    '''
    """
    print>>o, 'WHAT'
    print
    print>>o, 'PARAMS'
    print
    """
    g = None
    params = v.get_What().get_Param()
    for p in params:
        #print>>o,  Vutil.htmlParam(g, p)
        #print p.get_name(), p.get_value(), p.get_ucd(), p.get_unit(), p.get_dataType()
        if p.get_name() in dir(event[0]):
                if (p.get_name()=="stream" or p.get_name()=="id" or p.get_name()=="rev" or p.get_name()=="nevents"):
                    setattr(event[0],p.get_name(), int(float(p.get_value())))
                elif  (p.get_name()=="deltaT" or p.get_name()=="sigmaT" or p.get_name()=="false_pos" or \
                p.get_name()=="pvalue" or p.get_name()=="point_RA" or p.get_name()=="point_dec" ):
                   setattr(event[0],p.get_name(), float(p.get_value()))
                else:
                    setattr(event[0],p.get_name(), p.get_value())
        """
        print
        print "DESCRIPTION:"
        for d in p.get_Description(): print str(d)
        print
        """

    #print>>o, 'GROUP'
    #print
    groups = v.get_What().get_Group()
    #print>>o, 'NAME    VALUE     UCD    UNIT    DATATYPE '
    print()
    #evParam[0].event_eventStreamConfig_stream = event[0].stream
    #evParam[0].event_id = event[0].id
    #evParam[0].event_rev = event[0].rev
    # parameter class (array)
    evParam=[]
    for g in groups:
        for p in g.get_Param():
            #evParam=[Parameter("energy",1,1,0)]
            #print>>o, Vutil.htmlParam(g, p)
            #print p.get_name(), p.get_value(), " ", p.get_ucd(), " ", \
                                #p.get_unit(), " ", p.get_dataType()
            evPar= Parameter(p.get_name(),1,1,0)
            evPar.event_eventStreamConfig_stream = event[0].stream
            evPar.event_id = event[0].id
            evPar.event_rev = event[0].rev
            #print

            #for d in p.get_Description(): print "DESCRIPTION" , str(d)
            #if p.get_name() in dir(evParam[0]):
            #if (p.get_name()=="stream" or p.get_name()=="id" or p.get_name()=="rev" or p.get_name()=="nevents"):
             #   setattr(evPar,p.get_name(), int(p.get_value()))
                    #evPar.value=p.get_value()
                    #evPar.units=p.get_unit()
            #elif  (p.get_name()=="value"):
             #   setattr(evPar,p.get_name(), float(p.get_value()))
            #elif  (p.get_name()=="unit"):
             #   evPar.units=p.get_value()
                #setattr(evPar,p.get_name(), float(p.get_value()))
            #else:
             #   setattr(evPar,p.get_name(), p.get_value())
            evPar.value= p.get_value()
            evPar.units=p.get_unit()
            #evPar.forprint()
            evParam.append(evPar)
    #print "PARAMETER"
    #evParam[0].forprint()

    #print>>o, 'WHEREWHEN'
    #print
    wwd = Vutil.getWhereWhen(v)
    if wwd:
        """
        print>>o, 'Observatory  %s' % wwd['observatory']
        print>>o, 'Coord system %s' % wwd['coord_system']
        print>>o, 'Time       %s' % wwd['time']
        print>>o, 'Time error %s' % wwd['timeError']
        print>>o, 'RA         %s' % wwd['longitude']
        print>>o, 'Dec        %s' % wwd['latitude']
        #print>>o, 'Pos error %s ' % wwd['posError']
        """
        event[0].sigmaR=wwd['positionalError']
        timeevent=wwd['time']
        year=int(timeevent[0:4])
        month=int(timeevent[5:7])
        day=int(timeevent[8:10])
        hour=int(timeevent[11:13])
        minute=int(timeevent[14:16])
        second=int(timeevent[17:19])
        try:
            milisec=int(timeevent[20:])
        except ValueError:
            milisec=0

        event[0].datetime=datetime(year,month,day,hour,minute,second,milisec)

        event[0].RA=wwd['longitude']
        event[0].dec=wwd['latitude']

        ww=v.get_WhereWhen()
        obloc=ww.get_ObsDataLocation()
        observ=obloc.get_ObservatoryLocation()
        coord=observ.get_AstroCoords()
        values3D=coord.get_Position3D()
        values=values3D.get_Value3()
        #print "3D values: ", values.get_C1(), values.get_C2(), values.get_C3()


        event[0].longitude=values.get_C1()
        event[0].latitude=values.get_C2()
        event[0].elevation=values.get_C3()

    #print>>o, 'WHY'
    #print
    w = v.get_Why()
    """
    if w:
        if w.get_Concept():
            print>>o, "Concept: %s" % Vutil.htmlList(w.get_Concept())
        if w.get_Name():
            print>>o, "Name: %s"        % Vutil.htmlList(w.get_Name())

        print>>o, 'Inferences'
        inferences = w.get_Inference()
        for i in inferences:
            print>>o, 'probability %s' % i.get_probability()
            print>>o, 'relation %s' % i.get_relation()
            print>>o, 'Concept %s' % Vutil.htmlList(i.get_Concept())
            print>>o, 'Description %s' % Vutil.htmlList(i.get_Description())
            print>>o, 'Name %s ' % Vutil.htmlList(i.get_Name())
            print>>o, 'Reference %s' % str(i.get_Reference())
    """
    """
    print>>o, 'Citations'
    cc = v.get_Citations()
    if cc:
        for c in cc.get_EventIVORN():

            print>>o, '%s with a %s' % (c.get_valueOf_(), c.get_cite())
    #event[0].forprint()
    print "Number of events: %s " % Event._num_events
    """
    cc = v.get_Citations()
    if cc:
        for c in cc.get_EventIVORN():
            if c.get_cite() == 'retraction':
                print('Retraction of %s' % (c.get_valueOf_()))
                evPar = Parameter('retraction',event[0].stream, event[0].id, event[0].rev)
                evPar.value = int(c.get_valueOf_()[-1]) # last character should be the revision number of the notice to retract
                evPar.units = 'rev'
                evParam.append(evPar)
    return (event, evParam)

def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.getopt(args, 'hso:tf', ['help',
            'stdout', 'outfile=', 'text', 'force' ])
    except:
        usage()
    outfilename = None
    stdout = False
    force = False
    text = False
    for opt, val in opts:
        if opt in ('-h', '--help'):
            usage()
        elif opt in ('-o', '--outfile'):
            outfilename = val
        elif opt in ('-s', '--stdout'):
            stdout = True
        elif opt in ('-t', '--text'):
            text = True
        elif opt in ('-f', '--force'):
            force = True

    if len(args) != 1:
        usage()
    infilename = args[0]
    if stdout:
        #format_to_stdout(infilename)
        event2=make_event(infilename)
        event2[0].forprint()
    if outfilename is not None:
        format_to_file(infilename, outfilename, force)
    if text:
        content = format_to_string(infilename)
        print(content)
    if not stdout and outfilename is None and not text:
        usage()


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
    #alert=
