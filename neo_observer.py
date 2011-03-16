'''
Created on 2010-08-12

@author: Pierre Thibault
'''

from types import FunctionType
from types import LambdaType

class _ObserverRegistrationType():
    """
    Enum type like to representing the possible types of registration for a
    an event. 
    """
    
    for_all_events = 0  # Register to received all events
    by_sender = 1 # Register to received all events for a specific sender
    by_name = 2 # Register to received all events for a specific name
    # Register to received all events of a specific sender under a specific
    # name:
    by_sender_and_name = 3 
    
    @staticmethod
    def get_registration_type(sender, name):
        """
        Get the specific registration type based on the sender and the name.
        """
        
        if sender != None and name == None:
            return _ObserverRegistrationType.by_sender
        elif sender == None and name != None:
            return _ObserverRegistrationType.by_name
        elif sender != None and name != None:
            return _ObserverRegistrationType.by_sender_and_name
        else:
            return _ObserverRegistrationType.for_all_events
            
def _validate_event_name(name):
    assert name == None or (type(name) == str and name != ""), \
        "Event names must be none empty strings."
    
class ObserverRegistry(object):
    """
    The registry containing all the observers.
    """
    
    default_registry = None # Cannot defined yet
    """
    The default registry. Usually the registry of the application.
    """
    
    @staticmethod
    def __validate_add_observer(observer_or_func, sent_by=None, named=None):
        assert isinstance(observer_or_func, IObserver) or \
            isinstance(observer_or_func, FunctionType) or \
            isinstance(observer_or_func, LambdaType), \
            "Invalidate type for observer."
        _validate_event_name(named)
        
    def __init__(self):
        self.clear()
    
    def add_observer(self, observer_or_func, sent_by=None, named=None):
        """
        Add an observer to the registry. You can be notified of all events by
        not specifying sent_by and named. You can also specify both sent_by
        and named to received only the event of a specific sender under a
        specific name.
        @param observer_or_func: The observer to add. An object of type
        IObserver, a function or a lambda expression.
        @param sent_by: The sender that the observer want to observe. Optional.
        @param named: The name of the event the observer want to observe. Must
        be a string if specified. Optional.
        """
        
        ObserverRegistry.__validate_add_observer(observer_or_func, sent_by, 
            named)
        observer_registration_type = _ObserverRegistrationType. \
            get_registration_type(sent_by, named)
        if observer_registration_type == \
          _ObserverRegistrationType.for_all_events:
            self.__observers_for_all_events.add(observer_or_func)
        elif observer_registration_type == \
          _ObserverRegistrationType.by_sender:
            if not self.__senders_to_observers.has_key(sent_by):
                self.__senders_to_observers[sent_by] = set()
            self.__senders_to_observers[sent_by].add(observer_or_func)
        elif observer_registration_type == \
          _ObserverRegistrationType.by_name:
            if not self.__names_to_observers.has_key(named):
                self.__names_to_observers[named] = set()
            self.__names_to_observers[named].add(observer_or_func)
        elif observer_registration_type == \
            _ObserverRegistrationType.by_sender_and_name:
            key = (sent_by, named)
            if not self.__senders_names_to_observers.has_key(key):
                self.__senders_names_to_observers[key] = set()
            self.__senders_names_to_observers[key].add(observer_or_func)
        else:
            assert False, "Observer registration type unknown."
        
    
    def send_event(self, event_or_sender, name=None, info=None):
        """
        Send an event to all observers registered for the event.
        @param event_or_sender: The event to send of type Event or the
        sender of the event.
        @param name: The name of the event if event_or_sender is not an
        Event.
        @param info: Give more information about an event. It is recommanded
        to use a dictionary. Optional. 
        """
        
        is_event = isinstance(event_or_sender, Event)
        assert (is_event and name == None) or not is_event, "The name" + \
          " was supplied two times." 
        
        event = event_or_sender if is_event else \
          Event(event_or_sender, name, info)  
        observers = set()
        if self.__senders_to_observers.has_key(event.sender):
            observers.update(self.__senders_to_observers[event.sender])
        if self.__names_to_observers.has_key(event.name):
            observers.update(self.__names_to_observers[event.name])
        key = (event.sender, event.name)
        if self.__senders_names_to_observers.has_key(key):
            observers.update(self.__senders_names_to_observers[key])
        observers.update(self.__observers_for_all_events)
        for observer in observers:
            if isinstance(observer, IObserver):
                observer.receive_event(event)
            else: # Function or lambda
                observer(event)
    
    def remove_observer(self, observer_or_func):
        """
        Remove an observer from the registry.
        @param observer: The observer to remove. An object of type IObserver,
        a function or a lambda expression.
        """
        
        list_of_dict = [self.__senders_to_observers, 
                    self.__names_to_observers, self.__senders_names_to_observers]
        for index, dictionary in enumerate(list_of_dict):
            new_dict = dict()
            for key, set_of_observers in dictionary.iteritems():
                if observer_or_func in set_of_observers:
                    set_of_observers -= frozenset((observer_or_func,))
                if len(set_of_observers) > 0:
                    new_dict[key] = set_of_observers
            list_of_dict[index].clear()
            list_of_dict[index].update(new_dict)
        self.__observers_for_all_events -= frozenset((observer_or_func,))
    
    def clear(self):
        """
        Remove all the observers.
        """
        
        self.__senders_to_observers = dict()
        self.__names_to_observers = dict()
        self.__senders_names_to_observers = dict()
        self.__observers_for_all_events = set()
    
# Create the default registry:
ObserverRegistry.default_registry = ObserverRegistry()
    
class IObserver(object):
    """
    The interface defining the method a class must implement to receive events.
    """
    def receive_event(self, event):
        """
        The method receiving events.
        @param event: The event object of type Event containing the
        information about the event.
        """
def observer(sent_by=None, named=None):
    _validate_event_name(named)
    def decorator(func):
        ObserverRegistry.default_registry.add_observer(func, sent_by, named)
        return func
    return decorator

class Event(object):
    '''
    Encapsulate the information about an event. An event has as a sender
    (an object), a name (a string) and an info attribute that is usually a
    dictionary.
    '''
    @staticmethod
    def validate_sender_name(sender, name):
        assert sender != None and sender != "", "Sender must be specified."
        assert name != None and name != "", "Name must be specified."
        assert isinstance(name, str), "Name must be a string."
        
    
    def __init__(self, sender, name, info=None):
        """
        Create a new Event object.
        @param sender: The sender of the event. Cannot be None.
        @param name: The name of the event. Must be a none empty string.
        @param info: An optional object containing more information about the
        event. Recommendation: Use a dictionary.
        """
        
        Event.validate_sender_name(sender, name)
        self.sender = sender
        self.name = name
        self.info = info

    def __eq__(self, other): 
        if self is other:
            return True
        if isinstance(other, Event):
            if isinstance(self, other.__class__):
                return self._compare_value(other)
            else:
                return other == self # Line not tested because no derived yet
        return False
    
    def _compare_value(self, other):
        return self.sender == other.sender and \
                self.name == other.name and \
                self.info == other.info
    
    def __hash__(self):
        return hash(hash(self.sender) + hash(self.name) + hash(self.info)) 