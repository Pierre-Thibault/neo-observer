'''
Created on 2010-08-11

@author: Pierre Thibault
'''
from __future__ import with_statement
from neo_observer import observer, IObserver, ObserverRegistry, Event
import unittest

class Prototype():
    pass

event_expected1 = Prototype()
event_expected2 = Prototype()
event_expected3 = Prototype()
event_expected4 = Prototype()
event_expected5 = Prototype()
event_expected6 = Prototype()
event_expected1.event = None
event_expected2.event = None
event_expected3.event = None
event_expected4.event = None
event_expected5.event = None
event_expected6.event = None
test_case = None
zero_param_func_result = None

def receiver1(event):
    event_expected1.event = event
    
@observer(named="name2")
def receiver2(event):
    event_expected2.event = event
    
def receiver3(event):
    event_expected3.event = event
    
def zero_param_func():
    global zero_param_func_result
    zero_param_func_result = "called"
    
class Observer4(IObserver):
    def receive_event(self, event):
        event_expected4.event = event
    
class Observer5(IObserver):
    def receive_event(self, event):
        event_expected5.event = event
    
class Observer6(object):
    def receive_event_method(self, event):
        event_expected6.event = event
    
class Test(unittest.TestCase):

    def setUp(self):
        global test_case
        test_case = self
        self.registry1 = ObserverRegistry.default_registry
        self.registry2 = ObserverRegistry()
        self.observer4 = Observer4()
        self.observer5 = Observer5()

    def tearDown(self):
        self.reset_events()
        self.registry1.clear()
        self.registry2.clear()

    def test_1st_decorator_observer(self):
        self.registry1.send_event("this", "name2")
        self.validate_events((None, Event("this", "name2"), None, None, None))
        self.reset_events()
        self.registry1.send_event("this", "name3")
        self.validate_events((None, None, None, None, None))
    
    def test_observer_for_sender(self):
        """
        Test that observers are receiving theirs events when registered for
        a specific sender.
        """

        # Register some observers:
        self.registry1.add_observer(self.observer4, "sender2")
        self.registry2.add_observer(receiver1, "sender1")
        self.registry2.add_observer(receiver1, "sender3")

        self.registry1.send_event("sender6", "name")
        self.validate_events((None, None, None, None, None))
        self.reset_events()
        self.registry1.send_event(Event("sender2", "xx"))
        self.registry2.send_event(Event("sender2", "z"))
        self.validate_events((None, None, None, Event("sender2", "xx"), None))
        self.reset_events()
        self.registry1.send_event(Event("sender2", "xx"))
        self.registry1.send_event(Event("sender2", "z"))
        self.validate_events((None, None, None, Event("sender2", "z"), None))
        self.reset_events()
        self.registry2.send_event("sender3", "-")
        self.registry2.send_event("sender1", "a")
        self.validate_events((Event("sender1", "a"), None, None, None, None))
        self.registry1.add_observer(self.observer5, "sender2")
        self.registry1.send_event("sender2", "b")
        self.validate_events((Event("sender1", "a"), None, None, 
                              Event("sender2", "b"), Event("sender2", "b")))
        
    def test_observer_for_name(self):
        """
        Test that observers are receiving theirs events when registered for
        a specific name.
        """
        
        # Register some observers:
        self.registry1.add_observer(receiver1, None, "a")
        self.registry1.add_observer(receiver1, None, "b")
        self.registry1.add_observer(receiver2, None, "c")
        self.registry1.add_observer(receiver3, None, "c")
        self.registry2.add_observer(self.observer4, None, "d")
        self.registry2.add_observer(self.observer4, None, "b")
        self.registry2.add_observer(self.observer5, None, "z")

        event = Event("sender1", "b", "info")
        self.registry1.send_event(event)
        self.validate_events((event, None, None, None, None))
        self.reset_events()
        self.registry2.send_event(Event("sender", "b"))
        self.registry2.send_event(Event("sender2", "d"))
        self.validate_events((None, None, None, Event("sender2", "d"), None))
        self.reset_events()
        self.registry1.send_event("sender", "c")
        self.validate_events((None, Event("sender", "c"), 
                              Event("sender", "c"), None, None))
        
    def test_observer_for_sender_and_name(self):
        """
        Test that observers are receiving theirs events when registered for
        a specific sender and a specific name. Also test remove_observer.
        """

        # Register some observers:
        self.registry1.add_observer(receiver1, "1", "a")
        self.registry1.add_observer(receiver1, "1", "b")
        self.registry1.add_observer(receiver2, "2", "c")
        self.registry1.remove_observer(receiver1)
        self.registry1.add_observer(receiver1, "1", "a")
        self.registry1.add_observer(receiver1, "1", "b")
        self.registry1.add_observer(receiver3, "3", "c")
        self.registry2.add_observer(self.observer4, "2", "d")
        self.registry2.add_observer(self.observer4, "2", "d")
        self.registry2.add_observer(self.observer5, "3", "z")
        
        self.registry1.send_event("2", "c")
        self.validate_events((None, Event("2", "c"), None, None, None))
        self.reset_events()
        self.registry2.send_event(Event("2", "d"))
        self.validate_events((None, None, None, Event("2", "d"), None))
        self.reset_events()
        
        # Checking that they are not receiving when only matching the sender:
        self.registry1.send_event(Event("1", "z"))
        self.validate_events((None, None, None, None, None))
        
        # Checking that they are not receiving when only matching the name:
        self.registry1.send_event(Event("99", "c"))
        self.validate_events((None, None, None, None, None))
        
    def test_event(self):
        """
        Testing that Event cannot be constructed without a sender or without
        a name.
        """
        
        # No sender:
        try:
            Event(None, "name")
        except:
            pass
        else:
            self.fail()
        
        try:
            Event("", "name")
        except:
            pass
        else:
            self.fail()
        
        # No name:
        try:
            Event("sender", None)
        except:
            pass
        else:
            self.fail()
        try:
            Event("sender", "")
        except:
            pass
        else:
            self.fail()

        # Name is not a string:
        try:
            Event("sender", object())
        except:
            pass
        else:
            self.fail()
        
        # No nothing:
        try:
            Event(None, None)
        except:
            pass
        else:
            self.fail()
        try:
            Event("", "")
        except:
            pass
        else:
            self.fail()
        
        # With sender and name (OK):
        Event("sender", "name")
        
    def test_observer_for_all_events(self):
        """
        Test that observers are receiving theirs events when registered to
        receive all of them. Also test remove_observer.
        """

        # Register some observers:
        self.registry1.add_observer(receiver1, None, None)
        self.registry1.add_observer(receiver1, None, None)
        self.registry1.add_observer(receiver2, None, None)
        self.registry1.remove_observer(receiver1)
        self.registry1.add_observer(receiver3, None, None)
        self.registry2.add_observer(self.observer4, None, None)
        self.registry2.add_observer(self.observer4, None, None)
        self.registry2.add_observer(self.observer5, None, None)
        self.registry1.add_observer(self.observer5, None, None)
        self.registry1.add_observer(receiver1, None, None)
        self.registry1.remove_observer(self.observer5)
        event = Event("0", "name", "info")
        self.registry1.send_event(event)
        self.validate_events((event, event, event, None, None))
        self.reset_events()
        self.registry2.send_event(event)
        self.validate_events((None, None, None, event, event))
        
    def test_event_not_equal(self):
        self.assertTrue(Event("sender", "name") != Event(1, "name"))
        self.assertTrue(Event("sender", "name", "info") !=
          Event(1, "name", "info"))
        self.assertTrue(Event("sender", "name") != Event("sender", "name2"))
        self.assertTrue(Event("sender", "name", "info") != 
          Event("sender", "name", "diff"))
        self.assertTrue(Event("sender", "name") != None)
        self.assertTrue(Event("sender", "name") != 10)

    def test_weak_ref(self):
        default_registry = ObserverRegistry.default_registry
        o4 = Observer4()
        o5 = Observer5()
        default_registry.add_observer(o4)
        default_registry.add_observer(o5)
        e = Event("test_weak_ref", "test_weak_ref")
        default_registry.send_event(e)
        self.assertEquals(event_expected4.event, e)
        self.assertEquals(event_expected5.event, e)
        self.reset_events()
        del o4
        default_registry.send_event(e)
        self.assertEquals(event_expected4.event, None)
        self.assertEquals(event_expected5.event, e)
        # Test with a name:
        self.reset_events()
        o4 = Observer4()
        default_registry.add_observer(o4, named="test_weak_ref")
        default_registry.send_event(e)
        self.assertEquals(event_expected4.event, e)
        self.assertEquals(event_expected5.event, e)
        self.reset_events()
        del o4
        default_registry.send_event(e)
        self.assertEquals(event_expected4.event, None)
        self.assertEquals(event_expected5.event, e)

    def test_abstract_classes(self):
#        # _ObserverHolder seems not testable for abstract classes
#        from neo_observer import _WeakRefObserverHolder
#        with self.assertRaises(TypeError): 
#            _WeakRefObserverHolder("", "")
        from neo_observer import _ObserverRegistryDelegate
        with self.assertRaises(TypeError):
            _ObserverRegistryDelegate()
            
    def test_not_implemented(self):
        from neo_observer import _ObserverHolder
        from neo_observer import _NullObserverHolder
        null_observer = _NullObserverHolder("xxx")
        with self.assertRaises(NotImplementedError): 
            _ObserverHolder.__call__(null_observer, None)
        with self.assertRaises(NotImplementedError): 
            _ObserverHolder._is_holder_or_class(None, None)
        self.assertTrue(null_observer == null_observer)
        self.assertFalse(null_observer != null_observer)
        from neo_observer import _ObserverRegistryDelegate
        
        class _ObserverRegistryDelegateTemp(_ObserverRegistryDelegate):
            call_super = False
            def _add_observer_cond(self, sent_by, named):
                if self.call_super:
                    super(_ObserverRegistryDelegateTemp, self) \
                      ._add_observer_cond(None, None)
                else:
                    return False
            
            def _add_observer_imp(self, observer_holder, sent_by, named):
                if self.call_super:
                    super(_ObserverRegistryDelegateTemp, self) \
                  ._add_observer_imp(None, None, None)
            
            def _get_observer_holders(self, event):
                if self.call_super:
                    super(_ObserverRegistryDelegateTemp, self) \
                  ._get_observer_holders(None)
                else:
                    return frozenset()
                
            def _remove_observer_imp(self, observer_holder):
                pass
            
            def _clear_imp(self):
                pass
        
        temp_delegate = _ObserverRegistryDelegateTemp()
        temp_delegate.call_super = True
        with self.assertRaises(NotImplementedError): 
            temp_delegate._add_observer_cond(None, None)
        with self.assertRaises(NotImplementedError): 
            temp_delegate._add_observer_imp(None, None, None)
        with self.assertRaises(NotImplementedError): 
            temp_delegate._get_observer_holders(None)
        
        class _ObserverHolderTemp(_ObserverHolder):
            def __init__(self, observer):
                pass
            
            @classmethod
            def _is_holder_or_class(cls, observer, method):
                return observer is None
        
        temp_holder = _ObserverHolder(None)
        with self.assertRaises(NotImplementedError): 
            temp_holder.is_dead
        with self.assertRaises(NotImplementedError): 
            temp_holder.observer
            
        with self.assertRaises(NotImplementedError): 
            IObserver().receive_event(None)    
            
        temp_delegate.call_super = True
            
            
    def test_zero_param_func(self):
        default_registry = ObserverRegistry.default_registry
        default_registry.add_observer(zero_param_func)
        e = Event("test_weak_ref", "test_weak_ref")
        default_registry.send_event(e)
        self.assertEquals("called", zero_param_func_result)
        
    def test_unholdable_observer(self):
        from neo_observer import _ObserverHolder
        with self.assertRaises(ValueError):
            _ObserverHolder("xxx")
            
    def test_observer_with_method(self):
        default_registry = ObserverRegistry.default_registry
        o6 = Observer6()
        e = Event("test_with_method", "test_with_method")
        default_registry.send_event(e)
        self.assertNotEquals(event_expected6.event, e)
        self.reset_events()
        default_registry.add_observer(o6, None, None, "receive_event_method")
        default_registry.send_event(e)
        self.assertEquals(event_expected6.event, e)
        
    def test_HardRef(self):
        default_registry = ObserverRegistry.default_registry
        default_registry.add_observer(__import__)
        e = Event("test_HardRef", "test_HardRef")
        with self.assertRaises(TypeError): 
            default_registry.send_event(e)
        
    def test_HardRef2(self):
        default_registry = ObserverRegistry.default_registry
        default_registry.add_observer(locals)
        e = Event("test_HardRef", "test_HardRef")
        default_registry.send_event(e)
        
        
    def validate_events(self, results):
        global event_expected1, event_expected2, event_expected3, \
            event_expected4, event_expected5
        self.assertEqual(event_expected1.event, results[0])
        self.assertEqual(event_expected2.event, results[1])
        self.assertEqual(event_expected3.event, results[2])
        self.assertEqual(event_expected4.event, results[3])
        self.assertEqual(event_expected5.event, results[4])
        
    def reset_events(self):
        global event_expected1, event_expected2, event_expected3, \
            event_expected4, event_expected5
        global event_count
        event_expected1.event = None
        event_expected2.event = None
        event_expected3.event = None
        event_expected4.event = None
        event_expected5.event = None
        event_count = 0
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()