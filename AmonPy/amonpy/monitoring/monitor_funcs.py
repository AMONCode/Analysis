from datetime import datetime, timedelta
import numpy as np
import math as m
import MySQLdb
import os
from matplotlib.dates import date2num, DateFormatter
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging

from amonpy.tools.config import AMON_CONFIG
from amonpy.analyses.amon_streams import streams, inv_streams

from slackclient import SlackClient

class StreamToLogger(object):
    """
    Fake file-like stream object that redirects writes to a logger instance.
    """
    def __init__(self, logger, log_level=logging.DEBUG):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
           self.logger.log(self.log_level, line.rstrip())

def connection():
    conn = MySQLdb.connect(host = AMON_CONFIG.get('database', 'host_name'),\
                    user = AMON_CONFIG.get('database','username'),\
                    passwd = AMON_CONFIG.get('database','password'),\
                    db = AMON_CONFIG.get('database','realtime_dbname'))
    c = conn.cursor()
    return conn, c

def get_event_Streams():
    '''
        Gets the list of stream numbers in the database
    '''
    streamnums = []
    db, cursor = connection()
    sql = "SELECT stream FROM eventStreamConfig;"
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for row in results:
            streamnums.append(row[0])
    except Exception as inst:
        print type(inst)
        print inst.args
    db.close()
    return streamnums

def get_times(stream, low_time = datetime(2010,1,1,0,0,0), limit = 999999):
    db, cursor = connection()
    low_time_string = low_time.strftime("%Y-%m-%d %H:%M:%S")
    sql = "SELECT time FROM event WHERE time >= '%s' and rev=0 and eventStreamConfig_stream = %d ORDER BY time DESC LIMIT %d;" %(low_time_string, stream, limit)
    dates_list = []
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for dates in results:
            dates_list.append(dates)
    except Exception as inst:
        print type(inst)
        print inst.args
    db.close()
    return dates_list

def get_events(stream, time = datetime(2010,1,1,0,0,0),limit = 99999):
    db, cursor = connection()
    if stream == streams['HAWC-DM']:
        # Need to take into accout the transit time
        low_time = time-timedelta(hours=31)
    else:
        low_time = time-timedelta(hours=24)
    time_string = time.strftime("%Y-%m-%d %H:%M:%S")
    low_time_string = low_time.strftime("%Y-%m-%d %H:%M:%S")
    #sql = "SELECT time FROM event WHERE time >= '%s' and rev=0 and eventStreamConfig_stream=%d ORDER BY time ASC;"%(low_time_string,stream)
    sql = "SELECT time FROM event WHERE time >= '%s' and eventStreamConfig_stream=%d ORDER BY time DESC;"%(low_time_string,stream)
    events=[]
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        for dates in results:
            events.append(dates)
    except Exception as inst:
        print type(inst)
        print inst.args
    db.close()
    return events

def send_error_email(to_list,sender,passwd,subject, body):
    to = to_list
    me = sender
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(to)
    pas = passwd
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    #s.login(usrnm,pas)
    s.login(me, pas)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def send_email(to_list,sender,passwd,subject, body):
    to = to_list
    me = sender
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(to)
    pas = passwd
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    #s.login(usrnm,pas)
    s.login(me, pas)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def send_email_attach(to_list,sender,passwd,subject, body, attachment):
    to = to_list
    me = sender
    msg = MIMEMultipart(body)
    msg['Subject'] = subject
    msg['From'] = me
    msg['To'] = ", ".join(to)
    pas = passwd
    
    part = MIMEBase('application', "octet-stream")
    part.set_payload(open(attachment, "rb").read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', 'attachment', filename=attachment)
    msg.attach(part)
    
    s = smtplib.SMTP('smtp.gmail.com:587')
    s.ehlo()
    s.starttls()
    s.ehlo()
    #s.login(usrnm,pas)
    s.login(me, pas)
    s.sendmail(me, to, msg.as_string())
    s.quit()

def pois_prob(mu,nev,dt):
    ''' calculates the prob that nev events will arrive in time
    interval dt with an avg rate of mu, mu and dt need to be in
    the same units
    '''
    p=1.
    for k in range(nev):
        p -= np.exp(-mu*dt)*((mu*dt)**k)/(m.factorial(k))
    return p

def slack_message(message,channel,prodMachine,attachment=None,token=None):
    try:
        sc = SlackClient(token)
    except Exception as e:
        print(e)
    if prodMachine:
        user = "AMON-PROD"
    else:
        user = "AMON-DEV"
    sc.api_call('chat.postMessage',channel=channel,text=message,username=user,icon_emoji=":amon:")
    if attachment is not None:
        try:
            with open(attachment,'rb') as f:
                sc.api_call('files.upload',channels=channel, file=f, filename=attachment,username=user,icon_emoji=":amon:")
        except Exception as e:
            print(e)
