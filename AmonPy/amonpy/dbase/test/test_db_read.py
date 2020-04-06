from __future__ import print_function
import sys

from amonpy.dbase import db_read
from amonpy.tools import *
from amonpy.tools.config import AMON_CONFIG
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
        self.HostFancyName=AMON_CONFIG.get('database','host_name')
        self.UserFancyName=AMON_CONFIG.get('database','username')
        self.PasswordFancy=AMON_CONFIG.get('database','password')
        self.DBFancyName=AMON_CONFIG.get('database','realtime_dbname')
        self.DBFancyName2='AMON_test2'
        self.StreamFancyName=0
        self.EventID=1
        self.EventRev=0
        self.TimeStart='2020-04-01 00:00:00'
        self.TimeSlice=10000 # seconds
        self.TimeStop='2020-04-02 00:00:00'  # not used for now
        self.AlertStream=1
        self.AlertRev=0
        self.AlertID=0
        self.ParameterName="energy"
        self.StreamFancyName2=0
        self.EventID2=13390853588700
        self.EventRev2=0
        self.TimeStart2='2020-03-01 00:00:00'

    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]
        pass

    def testReadSingle(self):
        print('\nTesting read_event_single module')
        eventPrint=db_read.read_event_single(self.StreamFancyName, self.EventID2, self.EventRev,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)
        print(eventPrint.forprint())

    def testReadTimeSliceStreams(self):
        print('\nTesting read_event_timeslice module')
        eventPrintList=db_read.read_event_timeslice_streams([self.StreamFancyName,self.StreamFancyName2],self.TimeStart, self.TimeSlice,
                                 self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)
        for eventPrint in eventPrintList:
            print(eventPrint.forprint())


    def testReadEventConfig(self):
        print('\nTesting read_eventConfig module')
        eventPrintList=db_read.read_eventConfig(self.TimeStart, self.TimeSlice,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)
        for eventPrint in eventPrintList:
            print(eventPrint.forprint())


    def testReadAlertConfig(self):
        print('\nTesting read_alertConfig module')
        eventPrintList=db_read.read_alertConfig(self.AlertStream, self.AlertRev,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName2)
        #for eventPrint in eventPrintList
        print(eventPrintList.forprint())


    def testReadAlert(self):
        print('\nTesting read_alert_signle module')
        eventPrintList=db_read.read_alert_single(self.AlertStream, self.AlertRev,
                                                 self.AlertID, self.HostFancyName,
                                                 self.UserFancyName, self.PasswordFancy,
                                                 self.DBFancyName2)
        #for eventPrint in eventPrintList:
        print(eventPrintList.forprint())

    def testReadAlertTimeSliceStreams(self):
        print('\nTesting read_alert_time_slice module')
        eventPrintList=db_read.read_alert_timeslice_streams([self.AlertStream],self.TimeStart2, self.TimeSlice,
                                                 self.HostFancyName,
                                                 self.UserFancyName, self.PasswordFancy,
                                                 self.DBFancyName2)
        for eventPrint in eventPrintList:
            print(eventPrint.forprint())

    def testReadParameterSingle(self):
        print('\nTesting read_parameter_single module')
        eventPrint=db_read.read_parameter_single(self.ParameterName, self.StreamFancyName2,
                                  self.EventID2, self.EventRev2,
                                  self.HostFancyName,self.UserFancyName,
                                  self.PasswordFancy, self.DBFancyName)
        print(eventPrint.forprint())

if __name__ == '__main__':
    unittest.main()
