from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import numpy as np
import math as m
import os, sys
import MySQLdb
import time
from amonpy.analyses.amon_streams import streams, inv_streams
from amonpy.tools.config import AMON_CONFIG
from amonpy.monitoring.monitor_funcs import get_times, send_error_email, send_email, get_events, get_event_Streams

prodMachine = eval(AMON_CONFIG.get('machine','prod'))

def main():
    to = ['hgayala@psu.edu','delauj2@gmail.com']
    me = 'amon.psu@gmail.com'
    pwd= '***REMOVED***'
    now = datetime.utcnow()
    before = now - timedelta(hours=24)
    numstreams = get_event_Streams()
    if prodMachine:
        msg = "Event report from Prod Machine. \n"
    else:
        msg = "Event report from Dev Machine.\n"
    msg += "Time period: %s - %s\n"%(before.strftime("%Y-%m-%d %H:%M:%S"),now.strftime("%Y-%m-%d %H:%M:%S"))
    msg += "\n"
    for stream in numstreams:
        if 'OFU' in inv_streams[stream]:
            continue
        if 'SF' in inv_streams[stream]:
            continue
        events = get_events(stream,time=now)
        msg = msg+"%s events: %d\n"%(inv_streams[stream],len(events))

    send_email(to,me,pwd,"Event Report",msg)



if __name__ == "__main__":
    try:
        main()
    except Exception as inst:
        body = str(type(inst)) + '\n' + str(inst.args) + '\n' + str(inst)
        subject = 'no_events_inawhile_email.py error'
        to = ['hgayala@psu.edu']
        me = 'amon.psu@gmail.com'
        pwd= '***REMOVED***'
        send_error_email(to,me,pwd,subject, body)
