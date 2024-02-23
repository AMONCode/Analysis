#!/usr/bin/env python
"""
Synopsis:
    Sample program demonstrating use of VOEvent library and Vutil.py.

    Reads a VOEvent file and produces basic HTML rendering.
    See the VOEvent specification for details 
    http://www.ivoa.net/Documents/latest/VOEvent.html
Usage:
    python format_to_html.py [options] input_event_file.xml
Options:
    -h, --help      Display this help message.
    -s, --stdout    Send output to stdout.
    -o FILENAME, --outfile=FILENAME
                    Send output to file.
    -t, --text-string
                    Capture output as a text string, then write to stdout.
    -f, --force     Force: over-write output file without asking.
Examples:
    python format_to_html.py --stdout input_event_file.xml
    python format_to_html.py --file=outfile1.html input_event_file.xml
    python format_to_html.py -s -o outfile2.html input_event_file.xml

"""
from __future__ import print_function

# Copyright 2010 Roy D. Williams and Dave Kuhlmann
# modified by g.t.

from builtins import str
import sys
import os
import getopt
import VOEventLib.Vutil as Vutil

from datetime import datetime

from amonpy.dbase.db_classes import *

from io import StringIO

def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)

def make_event(source, o=sys.stdout):
    '''Generate printout that provides a display of an event.
    '''
    event=[Alert(1,1,0)]
    
    
    v = Vutil.parse(source)
   
    print('VOEvent', file=o)
    print()
    print('IVORN %s' % v.get_ivorn(), file=o)
    print()
    
    streamname=str(v.get_ivorn())
    len_sname=len(streamname)
    count, count1= 0, 0
    count2=0
    count=streamname.index('#')
    streamname2=streamname[count+1:]
    count1=1+count+streamname2.index('_')
    streamname3=streamname[count1+1:]
    count2=1+count1+streamname3.index('_')
    event[0].stream = int(streamname[count+1:count1])
    event[0].id = int(streamname[count1+1:count2])
    event[0].rev = int(streamname[count2+1:])
    print("STREAM NAME %s" % event[0].stream) 
    print()
    event[0].anarev=event[0].stream     
    
    print('(ROLE IS %s)' % v.get_role(), file=o)
    print()
    event[0].type=v.get_role()

    print('EVENT DESCRIPTION: %s\n' % v.get_Description(), file=o)
    print()
    
    

    r = v.get_Reference()
    if r:
        print('Reference Name=%s, Type=%s, uri=%s' \
                    % (r.get_name(), r.get_type(), r.get_uri()), file=o)
        print()
        
    print('WHO', file=o)
    print()
    
       
    who = v.get_Who()
    print('WHAT', file=o)
    print()
    print('PARAMS', file=o)
    print()
    
    params = v.get_What().get_Param()
    for p in params:
        print(p.get_name(), p.get_value(), p.get_ucd(), p.get_unit(), p.get_dataType()) 
        if p.get_name() in dir(event[0]):
                setattr(event[0],p.get_name(), p.get_value())
        print()        
        print("DESCRIPTION:")        
        for d in p.get_Description(): print(str(d))
        print()
    
    
    print('GROUP', file=o)
    print()
    groups = v.get_What().get_Group()
    print('NAME    VALUE     UCD    UNIT    DATATYPE ', file=o)
    print()
    for g in groups:
        for p in g.get_Param():
            print(p.get_name(), p.get_value(), " ", p.get_ucd(), " ", \
                                p.get_unit(), " ", p.get_dataType())
            print()
                        
            for d in p.get_Description(): print("DESCRIPTION" , str(d))
            

    print('WHEREWHEN', file=o)
    print()
    wwd = Vutil.whereWhenDict(v)
    if wwd:
        print('Observatory     %s' % wwd['observatory'], file=o)
        print('Coord system %s' % wwd['coord_system'], file=o)
        print('Time             %s' % wwd['time'], file=o)
        print('Time error %s ' % wwd['timeError'], file=o)
        print('RA                %s' % wwd['longitude'], file=o)
        print('Dec %s' % wwd['latitude'], file=o)
        print('Pos error %s ' % wwd['posError'], file=o)
        event[0].sigmaR=wwd['posError']
        timeevent=wwd['time']
        year=int(timeevent[0:4])
        month=int(timeevent[5:7])
        day=int(timeevent[8:10])
        hour=int(timeevent[11:13])
        minute=int(timeevent[14:16])
        second=int(timeevent[17:19])
        milisec=int(timeevent[20:])
        
        event[0].datetime=datetime(year,month,day,hour,minute,second,milisec)
        event[0].RA=wwd['longitude']
        event[0].dec=wwd['latitude']
        
        ww=v.get_WhereWhen()
        obloc=ww.get_ObsDataLocation()
        observ=obloc.get_ObservatoryLocation()
        coord=observ.get_AstroCoords()
        values3D=coord.get_Position3D()
     
    print('WHY', file=o)
    print()
    w = v.get_Why()
    if w:
        if w.get_Concept():
            print("Concept: %s" % Vutil.htmlList(w.get_Concept()), file=o)
        if w.get_Name():
            print("Name: %s"        % Vutil.htmlList(w.get_Name()), file=o)

        print('Inferences', file=o)
        inferences = w.get_Inference()
        for i in inferences:
            print('probability %s' % i.get_probability(), file=o)
            print('relation %s' % i.get_relation(), file=o)
            print('Concept %s' % Vutil.htmlList(i.get_Concept()), file=o)
            print('Description %s' % Vutil.htmlList(i.get_Description()), file=o)
            print('Name %s ' % Vutil.htmlList(i.get_Name()), file=o)
            print('Reference %s' % str(i.get_Reference()), file=o)
           
    print('Citations', file=o)
    cc = v.get_Citations()
    if cc:
        for c in cc.get_EventIVORN():
    
            print('%s with a %s' % (c.get_valueOf_(), c.get_cite()), file=o)


    return event




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


