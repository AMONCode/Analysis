import sys
sys.path.append('../')
sys.path.append('../../tools')
sys.path.append('../../sim')

import db_write
import unittest
from db_classes import *
"""@package test_db_write
Unit tests for db_write module.
"""
class TestDBWrite(unittest.TestCase):
    """
       Unit tests for db_write module.
    """
    def setUp(self):
# insert your host, user name and password here!    
        self.realArchive=0  # read archival data
        self.HostFancyName='yourhost' #localhost or db.hpc.rcc.psu.edu
        self.UserFancyName='yourname'
        self.PasswordFancy='yourpass'
        self.DBFancyName='AMON_test1'
        self.DBFancyNameMC='AMON_test2'
        self.StreamFancyName=0
        self.AlertStreamFancyName=1
        self.StreamFancyNameMC=[0,1,3,7]  # IceCube is 0
        self.StreamAlertConfig=[1]
        self.Filename='../../../data/icecube/IC40/IC40_finalPS_Public_NoPoles.txt'
        self.SimConfig=[simstream(0),simstream(1),simstream(3),simstream(7)]
        #self.AlertConfigSingle=[AlertConfig(1,0)]
        self.AlertConfigSingle=[exAlertConfig()]
        self.AlertSingle=[Alert(1,0,0)]
#        self.Event=[Event2(1,1,0)]
              
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass  
    
# Function to test the code, use it to write events on your localhost
# Running it on AMON db machine will fail since these data are already written
         
     
    def testWriteConfigArchive(self):
        print 'Testing write_event_config module'
        db_write.write_event_config_archive(self.StreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyName) 
    """     
    def testWriteConfig(self):
        print 'Testing write_event_config module'
        db_write.write_event_config(self.StreamFancyNameMC,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.SimConfig)
    """          
    def testWriteEventArchive(self):
        print 'Testing write_event module for archive data (for now)'
        db_write.write_event_archive(self.realArchive, self.StreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyName,self.Filename)
    
    def testWriteParam(self):
        print 'Testing write_parameter module for archive data (for now)'
        db_write.write_parameter(self.realArchive, self.StreamFancyName,self.HostFancyName,
                         self.UserFancyName, self.PasswordFancy, self.DBFancyName, self.Filename)
    """
    def testWriteAlertConfig(self):
        print 'Testing write_alert_config module'
        db_write.write_alert_config(self.StreamAlertConfig,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.AlertConfigSingle)
        
    def testWriteAlert(self):
        print 'Testing write_alert module'
        db_write.write_alert(self.AlertStreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.AlertSingle) 
       
    
    def testWriteEvent(self):
        print 'Testing write_event module for archive data (for now)'
        db_write.write_event(self.realArchive,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.Event) 
    """                       
if __name__ == '__main__':
    unittest.main()
