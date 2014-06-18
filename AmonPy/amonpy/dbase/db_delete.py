import MySQLdb as mdb
import sys
"""@package db_delete
Module to delete entries from the tables in DB.
"""

def delete_alert_stream(stream_number,host_name, user_name, passw_name, db_name):
    """Delete all alerts from a given stream"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        cur.execute("""DELETE FROM alert WHERE alertConfig_stream=%s""" %(stream_number,))
        con.commit()
        print '   This alert stream is deleted.'
        # count+=cur.rowcount
    except mdb.Error, e:
        print 'Exception %s' %e
        print '   This alert stream is not deleted.'
        con.rollback()
        
    cur.close()
    con.close()
                 
def delete_event_stream(stream_number, host_name, user_name, passw_name, db_name):
    """Delete all events from a given stream"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        print 'stream num %d' % stream_number 
        cur.execute("""DELETE FROM event WHERE eventStreamConfig_stream=%s""" %(stream_number,))
        con.commit()
        # count+=cur.rowcount
        print 'Event stream is deleted'
    except mdb.Error, e:
        print 'Exception %s' %e
        print 'This event stream is not deleted.'
        con.rollback()
        
    cur.close()
    con.close()  
    
def delete_alertline_stream_by_event(stream_number,host_name, user_name, passw_name, db_name):
    """Delete all alertlines from a given event stream"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        cur.execute("""DELETE FROM alertLine WHERE event_eventStreamConfig_stream=%s""" %(stream_number,))
        con.commit()
        print '   This alertline stream is deleted.'
       
    except mdb.Error, e:
        print 'Exception %s' %e
        print '   This alertline stream is not deleted.'
        con.rollback()
        
    cur.close()
    con.close()

def delete_alertline_stream_by_alert(stream_number,host_name, user_name, passw_name, db_name):
    """Delete all alertlines from a given alert stream"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        cur.execute("""DELETE FROM alertLine WHERE alert_alertConfig_stream=%s""" %(stream_number,))
        con.commit()
        print '   This alertline stream is deleted.'
       
    except mdb.Error, e:
        print 'Exception %s' %e
        print '   This alertline stream is not deleted.'
        con.rollback()
        
    cur.close()
    con.close() 
    
def delete_alertConfig(stream_number,host_name, user_name, passw_name, db_name):
    """Delete all alertConfig from a given alert stream"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        cur.execute("""DELETE FROM alertConfig WHERE stream=%s""" %(stream_number,))
        con.commit()
        print '   This alertConfig stream is deleted.'
       
    except mdb.Error, e:
        print 'Exception %s' %e
        print '   This alertConfig stream is not deleted.'
        con.rollback()
        
    cur.close()
    con.close()     
    
def delete_alertConfig_rev(stream_number,rev, host_name, user_name, passw_name, db_name):
    """Delete all alertConfig from a given alert stream and revision number"""
    
    con = mdb.connect(host_name, user_name, passw_name, db_name)    
    cur = con.cursor()
    
    try:
        cur.execute("""DELETE FROM alertConfig WHERE stream=%s and rev=%s""" %(stream_number, rev,))
        con.commit()
        print '   This alertConfig stream and rev is deleted.'
       
    except mdb.Error, e:
        print 'Exception %s' %e
        print '   This alertConfig stream and rev is not deleted.'
        con.rollback()
        
    cur.close()
    con.close()        
    
