#test_db_class.py
import sys
from sys import argv
sys.path.append("../")
sys.path.append("../../sim/")
from db_classes import *
import unittest
import ast
"""@package test_db_class
Unit tests for db_class module
"""
# Unit tests
class TestDBclass(unittest.TestCase):
    """
       Unit tests for db_class module.
    """
    def setUp(self):
        # no set up actions yet
        # print 'setting up unit tests: ', argv[0]
        # default is the simplest class, given by Event = event_def()
        # try these alternates...
        config = simstream(0)
        #Event = event_def(config)
        Event = event_def(config,True)
        
        
        pass
        
    def tearDown(self):
        # no tear down actions yet
        # print 'tearing down unit tests: ', argv[0]        
        pass

    def test1_init_del(self):
        print 
        print '(1) test_init_del'
        event1 = Event(1,0,0)
        print 'Created an event. Number of events:', Event._num_events
        del event1
        print 'Deleted event. Number of events:', Event._num_events        
        print

    #def test2_dict(self):
    #    print 
    #    print '(2) test_dict'
    #    event1 = Event(1,0,0)
    #    print '    event dictionary: '
   #     print event1.__dict__
   #     #print event1.dict        
   #     print 
                 
    def test3_forprint(self):
        print 
        print '(3) test_forprint'
        event1 = Event(1,0,0)
        print "here's a printed list: "
        event1.forprint()
        print ''
    
    #def test4_lock(self):
    #    print 
    #    print '(4) test_lock'
    #    event1 = Event(1,0,0)
    #    print 'lock status: ', event1._Event__lock
    #    print 'now lock the event'
    #    event1.set_lock(True)        
    #    print 'lock status: ', event1._Event__lock
    #    print 

    def test5_list(self):
        print
        print '(5) test_list'
        events = [Event(1,0,0), Event(1,1,0)]
        print 'Created a list of 2 events. Number of events:', Event._num_events
        print            
                    
    def test6_EventStreamConfig(self):
        print
        print '(6) test_list'
        config0 = simstream(0)
        print 'Created 1 configs. Number of configs:', \
                EventStreamConfig.num_configs
        print          
        config0.forprint()
        print
        fov_dict = ast.literal_eval(config0.fov)
        print fov_dict['lon']  
        print 
        
    def test7_del_Alert(self):
        print 
        print '(7) test Alert class'
        alert1 = Alert(1,0,0)
        print 'Created an alert. Number of alerts:', Alert.num_alerts
        del alert1
        print 'Deleted event. Number of events:', Alert.num_alerts        
        print       
      
    def test8_print_Alert(self):
        print 
        print '(8) test Alert class'
        alert1 = Alert(1,0,0)
        print 'Created an alert. Number of alerts:', Alert.num_alerts
        alert1.forprint()
        print
        
    def test9_AlertConfig(self):
        print
        print '(9) test AlertConfig class'
        configAlert = AlertConfig(1,0)
        print 'Created 1 alert configs. Number of configs:', \
                AlertConfig.num_configs
        print          
        configAlert.forprint()
        print
          
    
# Run the unittests
if __name__ == '__main__':
    unittest.main()
   
