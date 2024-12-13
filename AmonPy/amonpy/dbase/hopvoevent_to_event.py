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
from hop.models import VOEvent

from datetime import datetime
from amonpy.dbase.db_classes import *

from io import StringIO

def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)

def make_event(source, o=sys.stdout):
    '''Makes an instance of Event class from a given VOEvent.
    '''
    # initialize Event class to be populated from this VOEvent
    event=[Event(1,1,0)]
    if isinstance(source,VOevent):
        v = source
    else:
        v = VOEvent.load_file(source)
    event[0].configstream= 0 # change later to get revision from eventConfigTable event[0].stream
    event[0].type=v.role

    #r = v.Reference

    #who = v.Who

    # Get main parameters
    params = v.What['Param']
    for p in params:
        if p['name'] in dir(event[0]):
                if (p['name']=="stream" or p['name']=="id" or p['name']=="rev" or p['name']=="nevents"):
                    setattr(event[0],p['name'], int(float(p['value'])))
                elif  (p['name']=="deltaT" or p['name']=="sigmaT" or p['name']=="false_pos" or \
                p['name']=="pvalue" or p['name']=="point_RA" or p['name']=="point_dec" ):
                   setattr(event[0],p['name'], float(p['value']))
                else:
                    setattr(event[0],p['name'], p['value'])

    # Get parameters from individual detectors 
    groups = v.What['Group']['Param']
    evParam=[]
    for p in groups:
        evPar= Parameter(p['name'],1,1,0)
        evPar.event_eventStreamConfig_stream = event[0].stream
        evPar.event_id = event[0].id
        evPar.event_rev = event[0].rev
        evPar.value= p['value']
        try:
            evPar.units=p['unit']
        except:
            evPar.units='NA'
        evParam.append(evPar)

    wwd = v.WhereWhen['ObsDataLocation']['ObservationLocation']['AstroCoords']
    if wwd:
        event[0].sigmaR=wwd['Position2D']['Error2Radius']
        timeevent=wwd['Time']['TimeInstant']['ISOTime']
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

        event[0].RA=float(wwd['Position2D']['Value2']['C1'])
        event[0].dec=float(wwd['Position2D']['Value2']['C2'])

        coords = v.WhereWhen['ObsDataLocation']['ObservatoryLocation']['AstroCoords']
        values=coords['Position3D']['Value3']

        event[0].longitude=values['C1']
        event[0].latitude=values['C2']
        event[0].elevation=values['C3']

    #cc = v.Citations
    #if cc:
    #    for c in cc.get_EventIVORN():
    #        if c.get_cite() == 'retraction':
    #            print('Retraction of %s' % (c.get_valueOf_()))
    #            evPar = Parameter('retraction',event[0].stream, event[0].id, event[0].rev)
    #            evPar.value = int(c.get_valueOf_()[-1]) # last character should be the revision number of the notice to retract
    #            evPar.units = 'rev'
    #            evParam.append(evPar)
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
    print(infilename)
    if stdout:
        #format_to_stdout(infilename)
        event2=make_event(infilename)
        event2[0][0].forprint()
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
