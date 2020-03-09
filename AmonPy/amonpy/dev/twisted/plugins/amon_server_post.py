"""@package amon_server_post
receives events from a client using HTTP protocols and saves them in 
an archive directory called server_events
"""
from __future__ import print_function
from builtins import str
from twisted.internet import reactor
from twisted.web.resource import Resource
from twisted.web.server import Site
import cgi, os, getopt, sys

path = "twisted/"	
class EventPage(Resource):
    isLeaf = True
    
    def render_POST(self, request):
        self.headers = request.getAllHeaders()
        print(self.headers)
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
       
        print(request.content.getvalue())
        fname=self.headers['content-name']
        print("filename is %s" % (fname,))
        fp = open(path+"server_events/"+fname, "w")
        fp.write(request.content.getvalue())
        fp.close()
        return request.content.read() #[::-1]

