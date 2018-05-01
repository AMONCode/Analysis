import sys, os

from amonpy.dbase.db_classes import *
from amonpy.tools.config import AMON_CONFIG
from amonpy.analyses.amon_streams import streams, alert_streams

import smtplib
from email.mime.text import MIMEText
import netrc, ConfigParser
#import yowsup_run as yowsup_run

def alert_email(alert, params):
    #config_fname = '../amon.ini'
    #Config = ConfigParser.ConfigParser()
    #Config.read(config_fname)
    ehe_hese_emails = AMON_CONFIG.get('mailing_list','ehe_hese') #eval(Config.get('mailing_list', 'ehe_hese'))
    sub_emails = AMON_CONFIG.get('mailing_list','sub_ehe_hese')
    sub_cut_emails = AMON_CONFIG.get('mailing_list','sub_cut_ehe_hese')
    nrc_fname = os.path.join(AMON_CONFIG.get('dirs','amonpydir'), '.netrc')
    prodMachine = AMON_CONFIG.get('machine','prod')
    nrc = netrc.netrc(nrc_fname)
    stream = alert[0].stream

    if (stream==streams['IC-HESE']):
        for i in range(len(params)):
            if (params[i].name== 'event_id'):
                event_id=int(params[i].value)
            if (params[i].name== 'run_id'):
                run_id=int(params[i].value)
            if (params[i].name== 'causalqtot'):
                charge=params[i].value
            if (params[i].name== 'signal_trackness'):
                signal_trackness=params[i].value
            if (params[i].name== 'src_error90'):
                src_error_90=params[i].value
            if (params[i].name== 'src_error'):
                src_error_50=params[i].value

        time2=str(alert[0].datetime)
        dateutc=time2[0:10]+"T"+time2[11:]

        ra = alert[0].RA
        dec = alert[0].dec
        content = 'HESE_charge = '+str(charge)+'\n'+'HESE_signal_trackness = '+str(signal_trackness)+'\n'+'HESE_ra = '+str(ra)+'\n'+'HESE_dec = '+str(dec)+'\n'+'HESE_event_time = '+str(dateutc)+'\n'+'HESE_run_id = '+str(run_id)+'\n'+'HESE_event_id = '+str(event_id)+'\n'+'HESE_angular_error_50 = '+str(src_error_50)+'\n'+'HESE_angular_error_90 = '+str(src_error_90)+'\n'

        if prodMachine==True:
            title_msg = 'HESE event'
        else:
            title_msg = 'Test from Dev machine: HESE'
        if ((charge>=6000.0) and (signal_trackness>=0.1)):
            FROM = nrc.hosts['hese_ehe_gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['hese_ehe_gmail'][2]
            TO = ehe_hese_emails
        elif charge>=3000.0:
            FROM = nrc.hosts['gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['gmail'][2]
            TO = sub_cut_emails
        else:
            FROM = nrc.hosts['gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['gmail'][2]
            TO = sub_emails
    if (stream==streams['IC-EHE']):
        for i in range(len(params)):
            if (params[i].name== 'event_id'):
                event_id=int(params[i].value)
            if (params[i].name== 'run_id'):
                run_id=int(params[i].value)
            if (params[i].name== 'signalness'):
                signalness=params[i].value
            if (params[i].name== 'src_error'):
                src_error_50=params[i].value

        time2=str(alert[0].datetime)
        dateutc=time2[0:10]+"T"+time2[11:]

        ra = alert[0].RA
        dec = alert[0].dec
        content = 'EHE_signalness = '+str(signalness)+'\n'+'EHE_ra = '+str(ra)+'\n'+'EHE_dec = '+str(dec)+'\n'+'EHE_event_time = '+str(dateutc)+'\n'+'EHE_run_id = '+str(run_id)+'\n'+'EHE_event_id = '+str(event_id)+'\n'+'EHE_angular_error_50 = '+str(src_error_50)+'\n'

        if prodMachine==True:
            title_msg = 'EHE event'
        else:
            title_msg = 'Test from Dev machine: EHE'
        if alert[0].type=="observation":
            FROM = nrc.hosts['hese_ehe_gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['hese_ehe_gmail'][2]
            TO = ehe_hese_emails
        elif signalness >= .001:
            FROM = nrc.hosts['gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['gmail'][2]
            TO = sub_cut_emails
        else:
            FROM = nrc.hosts['gmail'][0] + '@gmail.com'
            PASS = nrc.hosts['gmail'][2]
            TO = sub_emails

    SERVER = 'smtp.gmail.com'
    PORT = 587
    msg = MIMEText(content)
    msg['Subject'] = title_msg
    msg['From'] = FROM
    msg['To'] = ", ".join(TO)
    message = msg.as_string()

    server = smtplib.SMTP(SERVER, PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(FROM, PASS)
    server.sendmail(FROM, TO, message)
    server.quit()

    #content_whatsapp = 'HESE_event_time = '+str(dateutc)+'; HESE_event_id = '+str(event_id)+'; HESE_charge = '+str(charge)+'; HESE_ra = '+str(ra)+'; HESE_dec = '+str(dec)+'; HESE_signal_trackness = '+str(signal_trackness)+'; HESE_angular_error_50 = 1.6 deg (50% containment)'+'; HESE_angular_error_90 = 8.9 deg (90% containment)'
    #yowsup_run.send_message("18143804192",content)
    #yowsup_run.send_message("18147699477",content)

def alert_email_content(alert,content,title_msg):
    nrc_fname = os.path.join(AMON_CONFIG.get('dirs','amonpydir'), '.netrc')
    nrc = netrc.netrc(nrc_fname)

    if alert[0].type == "observation":
        FROM = nrc.hosts['gmail'][0] + '@gmail.com'
        PASS = nrc.hosts['gmail'][2]
        TO = emails
    else:
        FROM = nrc.hosts['gmail'][0] + '@gmail.com'
        PASS = nrc.hosts['gmail'][2]
        TO = ['hgayala@psu.edu']

    SERVER = 'smtp.gmail.com'
    PORT = 587
    msg = MIMEText(content)
    msg['Subject'] = title_msg
    msg['From'] = FROM
    msg['To'] = ", ".join(TO)
    message = msg.as_string()

    server = smtplib.SMTP(SERVER, PORT)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(FROM, PASS)
    server.sendmail(FROM, TO, message)
    server.quit()
