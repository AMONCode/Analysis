import sys
sys.path.append('../')
sys.path.append('../../tools')

import db_read
import unittest
"""@package test_db_read
Unit tests for db_read module.
"""
class TestDBRead(unittest.TestCase):
    """
       Unit tests for db_read module.
    """
    def setUp(self):
# insert your host, user name and password here!    
        self.realArchive=0
        self.HostFancyName='yourhost'
        self.UserFancyName='username'
        self.PasswordFancy='passwd'
        self.DBFancyName='AMON_test1'
        self.DBFancyName2='AMON_test2'
        self.StreamFancyName=0
        self.EventID=1
        self.EventRev=0
        self.TimeStart='2008-01-01 00:00:00'
        self.TimeSlice=10000 # seconds
        self.TimeStop='2010-01-01 00:00:00'  # not used for now
        self.AlertStream=1
        self.AlertRev=0
        self.AlertID=0
        self.TimeStart2='2000-01-01 00:00:00'
        
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass   
     
    def testReadSingle(self):
        print 'Testing read_event_single module'
        eventPrint=db_read.read_event_single(self.StreamFancyName, self.EventID, self.EventRev,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName) 
        print eventPrint.forprint()
        
    def testReadTimeSlice(self):  
        print 'Testing read_event_timeslice module' 
        eventPrintList=db_read.read_event_timeslice(self.TimeStart, self.TimeSlice,
                                 self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)
        for eventPrint in eventPrintList:
            print eventPrint.forprint()  
      
    
    def testReadEventConfig(self):
        print 'Testing read_eventConfig module'  
        eventPrintList=db_read.read_eventConfig(self.TimeStart, self.TimeSlice,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)   
        for eventPrint in eventPrintList:
            print eventPrint.forprint() 
                                                                  
      
    def testReadAlertConfig(self):
        print 'Testing read_alertConfig module'  
        eventPrintList=db_read.read_alertConfig(self.AlertStream, self.AlertRev,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName2)   
        #for eventPrint in eventPrintList
        print eventPrintList.forprint()   

    
    def testReadAlert(self):
        print 'Testing read_alert_signle module'  
        eventPrintList=db_read.read_alert_single(self.AlertStream, self.AlertRev,
                                                 self.AlertID, self.HostFancyName,
                                                 self.UserFancyName, self.PasswordFancy,
                                                 self.DBFancyName2)   
        #for eventPrint in eventPrintList:
        print eventPrintList.forprint()

    def testReadAlertTimeSlice(self):
        print 'Testing read_alert_time_slice module'  
        eventPrintList=db_read.read_alert_timeslice(self.TimeStart2, self.TimeSlice,
                                                 self.HostFancyName,
                                                 self.UserFancyName, self.PasswordFancy,
                                                 self.DBFancyName2)   
        for eventPrint in eventPrintList:
            print eventPrint.forprint()
             
if __name__ == '__main__':
    unittest.main()                                        
        
        
