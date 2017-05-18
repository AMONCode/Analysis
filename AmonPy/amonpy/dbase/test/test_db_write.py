import sys, os
sys.path.append( os.path.abspath('..') )
sys.path.append( os.path.abspath('../..') )
sys.path.append( os.path.abspath('../../tools') )

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
        self.HostFancyName='dfc13-amon-test-01.hs.int.aci.ics.psu.edu' #localhost or db.hpc.rcc.psu.edu
        self.UserFancyName='amon'
        self.PasswordFancy='***REMOVED***'
        self.DBFancyName='AMON_test1'
        self.DBFancyNameMC='AMON_test2'
        self.StreamFancyName=0
        self.StreamFancyName2=[10,11,12,13,14,15] # IceCube HESE, HE, doublets MASTER, ASAS-SN, LCGOT and PTF
        self.AlertStreamFancyName=1
        self.StreamFancyNameMC=[0,1,3,7]  # IceCube is 0
        self.StreamAlertConfig=[1]
        self.StreamAlertConfig2=[2]
        self.Filename='../../../data/icecube/IC40/IC40_finalPS_Public_NoPoles.txt'
        self.SimConfig=[simstream(0),simstream(1),simstream(3),simstream(7)]
        #self.AlertConfigSingle=[AlertConfig(1,0)]
        self.AlertConfigSingle=[exAlertConfig()]
        self.AlertConfigSingle2=[exAlertArchivConfig()]
        self.AlertSingle=[Alert(1,0,0)]
        self.Parameter=[Parameter("energy",0,0,0)]
        
        self.Event=[Event(0,0,0)]
              
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass  
    
# Function to test the code, use it to write events on your localhost
# Running it on AMON db machine will fail since these data are already written
         
      
    def testWriteConfigArchive(self):
        print 'Testing write_event_config module archive'
        db_write.write_event_config_archive(self.StreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyName) 
        
      
    def testWriteConfig(self):
        print 'Testing write_event_config module MC'
        db_write.write_event_config(self.StreamFancyNameMC,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.SimConfig)
        
    def testWriteConfigHESE(self):
        print 'Testing write_event_config module for HESE'
        db_write.write_event_config_archive(self.StreamFancyName2[0],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)
        
    def testWriteConfigDoublet(self):
        print 'Testing write_event_config module for OFU MASTER'
        db_write.write_event_config_archive(self.StreamFancyName2[2],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)
        
    def testWriteConfigEHE(self):
        print 'Testing write_event_config module for EHE'
        db_write.write_event_config_archive(self.StreamFancyName2[1],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)
        
    def testWriteConfigDoublet2(self):
        print 'Testing write_event_config module for OFU ASAS-SN'
        db_write.write_event_config_archive(self.StreamFancyName2[3],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)    
    
    def testWriteConfigDoublet3(self):
        print 'Testing write_event_config module for OFU LCGOT'
        db_write.write_event_config_archive(self.StreamFancyName2[4],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)
   
    def testWriteConfigDoublet4(self):
        print 'Testing write_event_config module for OFU PTF'
        db_write.write_event_config_archive(self.StreamFancyName2[5],self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC)
       
    def testWriteEventArchive(self):
        print 'Testing write_event module for archive data (for now)'
        db_write.write_event_archive(self.realArchive, self.StreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyName,self.Filename)
    
    def testWriteParam(self):

        print 'Testing write_parameter module for archive data (for now)'
        db_write.write_parameter(self.realArchive, self.StreamFancyName,self.HostFancyName,
                         self.UserFancyName, self.PasswordFancy, self.DBFancyName, self.Filename)
   
   
    def testWriteAlertConfig(self):
        print 'Testing write_alert_config module MC'
        db_write.write_alert_config(self.StreamAlertConfig,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.AlertConfigSingle)
        
      
    def testWriteAlert(self):
        print 'Testing write_alert module MC'
        db_write.write_alert(self.AlertStreamFancyName,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.AlertSingle) 
       
   
    def testWriteEvent(self):
        print 'Testing write_event module MC'
        db_write.write_event(self.realArchive,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.Event) 
     
       
    def testWriteParamList(self):
        print 'Testing write_parameter_list module MC'
        db_write.write_parameter_list(self.HostFancyName, self.UserFancyName, 
                                      self.PasswordFancy, self.DBFancyNameMC, self.Parameter)
                                      
    
    def testWriteAlertConfigArchive(self):
        print 'Testing write_alert_config module, MC, late arival'
        db_write.write_alert_config(self.StreamAlertConfig2,self.HostFancyName,
        self.UserFancyName, self.PasswordFancy, self.DBFancyNameMC,self.AlertConfigSingle2)   
                 
if __name__ == '__main__':
    unittest.main()
