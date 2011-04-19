'''
Created on 2010-08-12

@author: Pierre Thibault
@license: MIT
@change: 2011-04-16: 
    Use weak references of observer of type IObserver.
    
    Any callable can be used as an observer as long as the callable can be
    called with the single event parameter or without argument at all. 
    
    When adding an observer, you can specify the method to be called on the
    observer to receive the event.
    
    Implementation changes: Using a type hierarchy instead of 
    a type flag for the different types of observers.
'''

import inspect
import types
import weakref


#==============================================================================
# ObserverRegistry
#==============================================================================

class ObserverRegistry(object):
    """
    The registry containing all the observers.
    """
    
    default_registry = None # Cannot defined yet
    """
    The default registry. Usually the registry of the application.
    """
    
    def __init__(self):
        # Create the delegate for each type of observer:
        self.__registries = [i() for i in \
                             _ObserverRegistryDelegate.__subclasses__()]
    
    def add_observer(self, observer, sent_by=None, named=None, \
                     method="__call__"):
        """
        Add an observer to the registry. There are four types of registration
        for an observer:
        
        1) For all events (use sent_by=None, named=None);
        
        2) For a specific sender (use sent_by=the_sender, named=None);
        
        3) For a specific name (use sent_by=None, named=the_name);
        
        4) For a specific sender using a specific name (sent_by=the_sender, 
        named=the_name).
        
        @param observer: The observer to add. An object of type
        IObserver, or any callable that can called with zero or one argument.
        If the callable can be called with one argument, this argument will be
        the event (an object of type Event).
        @param sent_by: The sender that the observer want to observe. Optional.
        @param named: The name of the event the observer want to observe. Must
        be a string if specified. Optional.
        @param method: Method name to call on the observer. If the observer is
        IObserver, receive_event will be used regardless of this value. 
        Optional.
        """
        
        _validate_event_name(named)
        
        self.remove_observer(observer)
        
        # Add in proper registry:
        for i in self.__registries:
            if i._add_observer_cond(sent_by, named):
                i._add_observer_imp(_ObserverHolder(observer, method), \
                                    sent_by, named)
                return
        assert False, "Observer registration type unknown."
            
    def send_event(self, event_or_sender, name=None, info=None):
        """
        Send an event to all observers registered for the event.
        @param event_or_sender: The event to send of type Event or the
        sender of the event.
        @param name: The name of the event if event_or_sender is not an
        Event.
        @param info: Give more information about an event if event_or_sender 
        is not an Event. It is recommended to use a dictionary. Optional. 
        """
        
        is_event = isinstance(event_or_sender, Event)
        
        # Validation:
        assert (is_event and name == None) or not is_event, "The name" + \
          " was supplied two times." 
        assert (is_event and info == None) or not is_event, "The info" + \
          " was supplied two times." 
        
        # Create the event if needed:
        event = event_or_sender if is_event else \
          Event(event_or_sender, name, info)  
        
        # Collect the observer holder:
        observer_holders = set()
        for registry in self.__registries:
            observer_holders |= registry._get_observer_holders(event)
        
        # Notify the observers about the event:
        has_dead_observers = False
        for observer_holder in observer_holders:
            observer_holder(event)
            # Collect dead weakrefs:
            has_dead_observers |= observer_holder.is_dead
                
        # Remove the dead weakref observers:
        if has_dead_observers:
            self.remove_observer(None)
                
    def remove_observer(self, observer):
        """
        Remove an observer from the registry.
        @param observer: The observer to remove. The same observer as for 
        add_observer.
        """
        
        observer_holder = _NullObserverHolder(observer) if observer else None
        for registry in self.__registries:
            registry._remove_observer_imp(observer_holder)
        
    def clear(self):
        """
        Remove all the observers.
        """
        
        for registry in self.__registries:
            registry._clear_imp()
        
#==============================================================================
# _ObserverRegistryDelegate
#==============================================================================

class _ObserverRegistryDelegate(object):
    """
    An abstract delegate class for ObserverRegistry representing in a type
    hierarchy of the different type of observer registration.
    """
    
    def __init__(self):
        if self.__class__ == _ObserverRegistryDelegate:
            raise TypeError(self.__class__.__name__ + " is an abstract class" \
              + " that cannot be instantiated.")
    
    def _add_observer_cond(self, sent_by, named):
        """
        Specify if a derived class accept this kind of observer. Must be 
        overridden.
        """
        
        raise NotImplementedError()

    def _add_observer_imp(self, observer_holder, sent_by, named):
        """
        Add an already validated observer holder. Must be overridden.
        """
        
        raise NotImplementedError()
    
    def _get_observer_holders(self, event):
        """
        Method used to get all the observer holders of an event. Must be 
        overridden.
        """

        raise NotImplementedError()
    
    def _remove_observer_imp(self, observer_holder):
        """
        Default implementation of remove an observer_holder.
        @param observer_holder: An _ObserverHolder or None to delete dead
        observer holders.
        """
        
        new_dict = dict()
        for key, set_of_holders in self._registry.iteritems():
            if observer_holder:
                set_of_holders.discard(observer_holder)
            else:
                holders_to_remove = set()
                for o in set_of_holders:
                    if o.is_dead:
                        holders_to_remove.add(o)
                set_of_holders -= holders_to_remove
            if len(set_of_holders) > 0:
                new_dict[key] = set_of_holders
        self._registry.clear()
        self._registry.update(new_dict)
        
    def _clear_imp(self):
        """
        Default implementation to remove all observers.
        """
        
        self._registry.clear()
    

class _AllEventsObserverRegistryDelegate(_ObserverRegistryDelegate):
    """
    A registry for observers who want to be notified of all events.
    """
    
    def __init__(self):
        self._registry = set()

    def _add_observer_cond(self, sent_by, named):
        return sent_by == None and named == None

    def _add_observer_imp(self, observer_holder, sent_by, named):
        self._registry.add(observer_holder)

    def _get_observer_holders(self, event):
        return self._registry
        
    def _remove_observer_imp(self, observer_holder):
        if observer_holder:
            self._registry.discard(observer_holder)
        else:
            holders_to_remove = set()
            for o in self._registry:
                if o.is_dead:
                    holders_to_remove.add(o)
            self._registry -= holders_to_remove

class _SendersObserverRegistryDelegate(_ObserverRegistryDelegate):
    """
    A registry for observers who want to be notified of all events sent by a
    specific sender.
    """

    def __init__(self):
        self._registry = dict()
    
    def _add_observer_cond(self, sent_by, named):
        return sent_by != None and named == None

    def _add_observer_imp(self, observer_holder, sent_by, named):
        if not self._registry.has_key(sent_by):
            self._registry[sent_by] = set()
        self._registry[sent_by].add(observer_holder)

    def _get_observer_holders(self, event):
        return self._registry.get(event.sender, frozenset())
        
class _NamesObserverRegistryDelegate(_ObserverRegistryDelegate):
    """
    A registry for observers who want to be notified of all events sent with a
    specific name.
    """

    def __init__(self):
        self._registry = dict()
    
    def _add_observer_cond(self, sent_by, named):
        return sent_by == None and named != None

    def _add_observer_imp(self, observer_holder, sent_by, named):
        if not self._registry.has_key(named):
            self._registry[named] = set()
        self._registry[named].add(observer_holder)

    def _get_observer_holders(self, event):
        return self._registry.get(event.name, frozenset())
        
class _SendersAndNamesObserverRegistryDelegate \
        (_ObserverRegistryDelegate):
    """
    A registry for observers who want to be notified of all events sent by a
    specific sender under a certain name.
    """

    def __init__(self):
        self._registry = dict()
    
    def _add_observer_cond(self, sent_by, named):
        return sent_by != None and named != None

    def _add_observer_imp(self, observer_holder, sent_by, named):
        key = (sent_by, named)
        if not self._registry.has_key(key):
            self._registry[key] = set()
        self._registry[key].add(observer_holder)

    def _get_observer_holders(self, event):
        key = (event.sender, event.name)
        return self._registry.get(key, frozenset())
        
# Create the default registry:
ObserverRegistry.default_registry = ObserverRegistry()

#==============================================================================
# _ObserverHolder
#==============================================================================

class _ObserverHolder(object):
    """
    An abstract class encapsulating of observer so they all can be treated
    polymorphically.
    """
    
    def __new__(cls, observer, method="__call__"):
        """
        The constructor of the class. Will create the appropriate instance
        type based on observer.
        """

        if cls == _NullObserverHolder:
            return object.__new__(cls, observer)
        
        for delegate_class in cls.__subclasses__():
            if delegate_class == _NullObserverHolder:
                continue
            is_holder_or_class = delegate_class._is_holder_or_class(observer, \
                                                                    method) 
            if is_holder_or_class:
                class_type = delegate_class if is_holder_or_class is True \
                  else is_holder_or_class
                return object.__new__(class_type, observer, method)
        raise ValueError("Observer is not callable with 1 or 0 argument " + \
                         "or an IObserver.")
        
    def __init__(self, method):
        if self.__class__ == _ObserverHolder:
            raise TypeError(self.__class__.__name__ + " is an abstract class" \
              + " that cannot be instantiated.")
        self._hash = hash(self.observer)
        self.method = method
    
    def __call__(self, event):
        """
        Every observer holder must be able to call the observer they are
        holding.
        """

        raise NotImplementedError()
    
    def __eq__(self, other):
        if isinstance(other, _ObserverHolder):
            if self.is_dead:
                return other.is_dead
            return self.observer == other.observer
        return False
    
    def __ne__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return self._hash
    
    @classmethod
    def _is_holder_or_class(cls, observer, method):
        """
        Method derived class must implement to tell if they can hold this
        type of observer. They may return True or false (truth as Python 
        defines it) or the class to be used.
        """

        raise NotImplementedError()

    @property
    def is_dead(self):
        """
        Property telling if an observer is still alive. This method is used to
        manage weak references that may be gone.
        """

        raise NotImplementedError()
    
    @property
    def observer(self):
        """
        Property to get access the observer the holder is holding.
        """

        raise NotImplementedError()

    @staticmethod
    def _is_zero_param(info):
        if info:
            min_arg = 0
            if not info["is_function"]:
                min_arg = 1
            return info["len_agr_spec"] == min_arg
        return False
    
    @staticmethod
    def _is_one_param(info):
        if info:
            min_arg = 1
            if not info["is_function"]:
                min_arg = 2
            return (info["len_agr_spec"] >= min_arg \
              and info["len_agr_spec"] - info["len_arg_spec_defaults"] \
                <= min_arg) or info["varargs"]
        return False

    @staticmethod
    def _callable_param_info(observer, method):
        """
        A method giving information about the parameters of a callable.
        """

        info = dict()
        if not isinstance(observer, types.BuiltinFunctionType):
            if not (isinstance(observer, types.FunctionType) \
                    and method == "__call__"):
                if hasattr(observer, method):
                    observer = getattr(observer, method)
                else:
                    return info
            if callable(observer):
                info["is_function"] = isinstance(observer, types.FunctionType)
                arg_spec = inspect.getargspec(observer)
                info["len_agr_spec"] = len(arg_spec.args)
                info["len_arg_spec_defaults"] = 0 if not arg_spec.defaults \
                    else len(arg_spec.defaults)
                info["varargs"] = bool(arg_spec.varargs)
        return info
    
    @staticmethod
    def _is_function(o):
        return isinstance(o, (types.FunctionType, types.BuiltinFunctionType))
    
class _NullObserverHolder(_ObserverHolder):
    """
    An null observer just needed to remove observers.
    """
    def __init__(self, observer):
        self.__observer = observer
        super(_NullObserverHolder, self).__init__("")
        
    def __call__(self, event):
        pass
    
    @property
    def is_dead(self):
        return False
    
    @property
    def observer(self):
        return self.__observer



class _IObserverHolder(_ObserverHolder):
    """
    An abstract final holder for an IObserver to be scan by _ObserverHolder. 
    Only direct subclasses of _ObserverHolder are scanned.
    """

    @classmethod
    def _is_holder_or_class(cls, observer, method):
        if _IObserverWeakRefInstanceObserverHolder \
          ._is_holder_or_class(observer, "receive_event"):
            return _IObserverWeakRefInstanceObserverHolder
    
    def __init__(self, observer):
        raise TypeError(self.__class__.__name__ + " is an abstract final"
          " class that cannot be instantiated.")

class _WeakRefObserverHolder(_ObserverHolder):
    """
    An abstract holder using a weak reference.
    """

    @classmethod
    def _is_holder_or_class(cls, observer, method):
        info = cls._callable_param_info(observer, method)
        if info:
            try:
                weakref.ref(observer)
            except:
                return False
            if cls._is_zero_param(info):
                return _ZeroParamWeakRefObserverHolder
            elif cls._is_one_param(info):
                return _OneParamWeakRefObserverHolder
    
    def __init__(self, observer, method):
        if self.__class__ == _WeakRefObserverHolder:
            raise TypeError(self.__class__.__name__ + " is an abstract class" \
              + " that cannot be instantiated.")
        self.weak_ref = weakref.ref(observer)
        super(_WeakRefObserverHolder, self).__init__(method)
    
    def __call__(self, event):
        raise NotImplementedError
            
    @property
    def is_dead(self):
        return self.weak_ref() == None

    @property
    def observer(self):
        return self.weak_ref()
    
class _ZeroParamWeakRefObserverHolder(_WeakRefObserverHolder):
    """
    A concrete class of _WeakRefObserverHolder for a zero parameter callable.
    """

    def __init__(self, observer, method):
        super(_ZeroParamWeakRefObserverHolder, self).__init__(observer, method)
    
    def __call__(self, event):
        observer = self.observer
        if observer != None:
            getattr(observer, self.method)()
    
class _OneParamWeakRefObserverHolder(_WeakRefObserverHolder):
    """
    A concrete class of _WeakRefObserverHolder for a one parameter callable.
    """

    def __init__(self, observer, method):
        super(_OneParamWeakRefObserverHolder, self).__init__(observer, method)
    
    def __call__(self, event):
        observer = self.observer
        if observer != None:
            getattr(observer, self.method)(event)
    
class _IObserverWeakRefInstanceObserverHolder \
  (_WeakRefObserverHolder):
    """
    An IObserver holder built on top of _WeakRefObserverHolder. 
    """
    
    @classmethod
    def _is_holder_or_class(cls, observer, method):
        return isinstance(observer, IObserver)

    def __init__(self, observer, method):
        super(_IObserverWeakRefInstanceObserverHolder, self) \
          .__init__(observer, "receive_event")
          
    def __call__(self, event):
        observer = self.observer
        if observer != None:
            observer.receive_event(event)
    

class _HardRefObserverHolder(_ObserverHolder):
    """
    An abstract class for an observer that is a function that can be 
    called with the single parameter event or no parameter at all.
    """

    @classmethod
    def _is_holder_or_class(cls, observer, method):
        return hasattr(observer, method) \
          and callable(getattr(observer, method))
    
    def __init__(self, observer, method):
        self.__observer = observer
        super(_HardRefObserverHolder, self).__init__(method)
    
    def __call__(self, event):
        try:
            getattr(self.observer, self.method)(event)
        except TypeError:
            getattr(self.observer, self.method)()
            
    @property
    def is_dead(self):
        return False

    @property
    def observer(self):
        return self.__observer
    
#==============================================================================
# IObserver
#==============================================================================

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
        
        raise NotImplementedError()
    
#==============================================================================
# observer
#==============================================================================

def observer(sent_by=None, named=None, registry=None):
    """
    A decorator that automatically register the function decorated.
    @param sent_by: The sender to observe.
    @param named: The name of the event to observe.
    @param registry: The registry to use. None means default_registry.
    """
    
    _validate_event_name(named)
    def decorator(func):
        registry_imp = registry if registry \
          else ObserverRegistry.default_registry 
        registry_imp.add_observer(func, sent_by, named)
        return func
    return decorator

#==============================================================================
# Event
#==============================================================================

class Event(object):
    '''
    Encapsulate the information about an event. An event has as a sender
    (an object), a name (a string) and an info attribute that is usually a
    dictionary.
    '''
    
    @staticmethod
    def _validate_sender_name(sender, name):
        assert sender != None and sender != "", "Sender must be specified."
        assert name != None and name != "", "Name must be specified."
        assert isinstance(name, basestring), "Name must be a string."
        
    
    def __init__(self, sender, name, info=None):
        """
        Create a new Event object.
        @param sender: The sender of the event. Cannot be None.
        @param name: The name of the event. Must be a none empty string.
        @param info: An optional object containing more information about the
        event. Recommendation: Use a dictionary.
        """
        
        assert self.__class__ == Event, "Event is final."
        Event._validate_sender_name(sender, name)
        self.sender = sender
        self.name = name
        self.info = info

    def __eq__(self, other): 
        if isinstance(other, Event):
            return self.sender == other.sender and \
                    self.name == other.name and \
                    self.info == other.info
        return False
    
    def __ne__(self, other):
        return not (self == other)
    
    def __hash__(self):
        return hash(hash(self.sender) + hash(self.name) + hash(self.info)) 
    
    def __repr__(self):
        return "%s(%s, %s, %s)" % (self.__class__.__name__, repr(self.sender),\
                                   repr(self.name), repr(self.info), )
    
#==============================================================================
# Private utility functions
#==============================================================================

def _validate_event_name(name):
    assert name == None or (isinstance(name, basestring) and name != ""), \
        "Event names must be none empty strings."
