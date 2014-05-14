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

# Copyright 2010 Roy D. Williams and Dave Kuhlmann
# modified by g.t.

import sys
import os
import getopt
#import VOEvent
import Vutil


from datetime import datetime
#sys.path.append('../db_classes')

from db_classes import *

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def usage():
    sys.stderr.write(__doc__)
    sys.exit(1)

def make_event(source, o=sys.stdout):
    '''Generate printout that provides a display of an event.
    '''
    event=[Alert(1,1,0)]
    
    
    v = Vutil.parse(source)
   
    print>>o, 'VOEvent'
    print
    print>>o, 'IVORN %s' % v.get_ivorn()
    print
    
    streamname=str(v.get_ivorn())
    len_sname=len(streamname)
    count, count1= 0, 0
    count2=0
    count=streamname.index('#')
    streamname2=streamname[count+1:]
    count1=1+count+streamname2.index('_')
    streamname3=streamname[count1+1:]
    count2=1+count1+streamname3.index('_')
    #number_st=f
    event[0].stream = int(streamname[count+1:count1])
    event[0].id = int(streamname[count1+1:count2])
    event[0].rev = int(streamname[count2+1:])
    print "STREAM NAME %s" % event[0].stream 
    print
    event[0].anarev=event[0].stream     
    
    print>>o, '(ROLE IS %s)' % v.get_role()
    print
    event[0].type=v.get_role()

    print>>o, 'EVENT DESCRIPTION: %s\n' % v.get_Description()
    print
    
    

    r = v.get_Reference()
    if r:
        print>>o, 'Reference Name=%s, Type=%s, uri=%s' \
                    % (r.get_name(), r.get_type(), r.get_uri())
        print
        
    print>>o, 'WHO'
    print
    
       
    who = v.get_Who()
    '''
    a = who.get_Author()
    print>>o, 'Title: %s'                        % Vutil.htmlList(a.get_title())
    print>>o, 'Name: %s'                         % Vutil.htmlList(a.get_contactName())
    print>>o, 'Email: %s'                        % Vutil.htmlList(a.get_contactEmail())
    print>>o, 'Phone: %s'                        % Vutil.htmlList(a.get_contactPhone())
    print>>o, 'Contributor: %s' % Vutil.htmlList(a.get_contributor())
    '''
    print>>o, 'WHAT'
    print
    print>>o, 'PARAMS'
    print
    
    g = None
    params = v.get_What().get_Param()
    for p in params:
        #print>>o,  Vutil.htmlParam(g, p)
        print p.get_name(), p.get_value(), p.get_ucd(), p.get_unit(), p.get_dataType() 
        if p.get_name() in dir(event[0]):
                #print "YES"
                setattr(event[0],p.get_name(), p.get_value())
        print        
        print "DESCRIPTION:"        
        for d in p.get_Description(): print str(d)
        print
    
    
    print>>o, 'GROUP'
    print
    groups = v.get_What().get_Group()
    print>>o, 'NAME    VALUE     UCD    UNIT    DATATYPE '
    print
    for g in groups:
        for p in g.get_Param():
            #print>>o, Vutil.htmlParam(g, p) 
            print p.get_name(), p.get_value(), " ", p.get_ucd(), " ", \
                                p.get_unit(), " ", p.get_dataType()
            print
                        
            for d in p.get_Description(): print "DESCRIPTION" , str(d)
            

    print>>o, 'WHEREWHEN'
    print
    wwd = Vutil.whereWhenDict(v)
    if wwd:
        print>>o, 'Observatory     %s' % wwd['observatory']
        print>>o, 'Coord system %s' % wwd['coord_system']
        print>>o, 'Time             %s' % wwd['time']
        print>>o, 'Time error %s ' % wwd['timeError']
        print>>o, 'RA                %s' % wwd['longitude']
        print>>o, 'Dec %s' % wwd['latitude']
        print>>o, 'Pos error %s ' % wwd['posError']
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
        #values=values3D.get_Value3()
        #print "3D values: ", values.get_C1(), values.get_C2(), values.get_C3()
        
       
        #event[0].longitude=values.get_C1()
        #event[0].latitude=values.get_C2()
        #event[0].elevation=values.get_C3()
     
    print>>o, 'WHY'
    print
    w = v.get_Why()
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
           
    print>>o, 'Citations'
    cc = v.get_Citations()
    if cc:
        for c in cc.get_EventIVORN():
    
            print>>o, '%s with a %s' % (c.get_valueOf_(), c.get_cite())


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
        #format_to_stdout(infilename)
        event2=make_event(infilename)
        event2[0].forprint()
    if outfilename is not None:
        format_to_file(infilename, outfilename, force)
    if text:
        content = format_to_string(infilename)
        print content
    if not stdout and outfilename is None and not text:
        usage()
    
    
if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()
    #alert=

