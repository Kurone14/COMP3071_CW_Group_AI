"""
Event system for the warehouse robot system.
Provides a publish-subscribe mechanism for inter-module communication.
"""

from typing import Dict, List, Callable, Any, Set
from enum import Enum, auto
import threading


class EventType(Enum):
    """Enumeration of event types"""
    # Simulation events
    SIMULATION_STARTED = auto()
    SIMULATION_PAUSED = auto()
    SIMULATION_RESUMED = auto()
    SIMULATION_RESET = auto()
    SIMULATION_COMPLETED = auto()
    SIMULATION_STEP = auto()
    
    # Robot events
    ROBOT_ADDED = auto()
    ROBOT_DELETED = auto()
    ROBOT_MOVED = auto()
    ROBOT_PICKED_ITEM = auto()
    ROBOT_DELIVERED_ITEM = auto()
    ROBOT_WAITING = auto()
    
    # Item events
    ITEM_ADDED = auto()
    ITEM_DELETED = auto()
    ITEM_ASSIGNED = auto()
    ITEM_PICKED = auto()
    ITEM_DELIVERED = auto()
    
    # Environment events
    GRID_RESIZED = auto()
    OBSTACLE_ADDED = auto()
    OBSTACLE_REMOVED = auto()
    OBSTACLE_EXPIRED = auto()
    DROP_POINT_SET = auto()
    
    # Pathfinding events
    PATH_FOUND = auto()
    PATH_FAILED = auto()
    
    # Analytics events
    STALL_DETECTED = auto()
    STALL_RESOLVED = auto()
    PERFORMANCE_UPDATED = auto()


class EventBus:
    """
    Central event bus for the warehouse robot system.
    Implements a publish-subscribe pattern for inter-module communication.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the event bus if not already initialized"""
        if self._initialized:
            return
            
        # Dictionary of event types to sets of subscribers
        self.subscribers: Dict[EventType, List[Callable]] = {}
        
        # Dictionary to track once-only subscribers
        self.once_subscribers: Dict[EventType, Set[Callable]] = {}
        
        # Lock for thread safety
        self.lock = threading.RLock()
        
        self._initialized = True
    
    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
    
    def subscribe_once(self, event_type: EventType, callback: Callable) -> None:
        """
        Subscribe to an event type and unsubscribe after first notification
        
        Args:
            event_type: Type of event to subscribe to
            callback: Function to call when event is published
        """
        with self.lock:
            # Regular subscription
            self.subscribe(event_type, callback)
            
            # Mark as once-only
            if event_type not in self.once_subscribers:
                self.once_subscribers[event_type] = set()
            self.once_subscribers[event_type].add(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable) -> bool:
        """
        Unsubscribe from an event type
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Function to unsubscribe
            
        Returns:
            bool: True if unsubscribed successfully, False if not found
        """
        with self.lock:
            if event_type in self.subscribers and callback in self.subscribers[event_type]:
                self.subscribers[event_type].remove(callback)
                
                # Also remove from once_subscribers if present
                if event_type in self.once_subscribers and callback in self.once_subscribers[event_type]:
                    self.once_subscribers[event_type].remove(callback)
                
                return True
            return False
    
    def publish(self, event_type: EventType, *args, **kwargs) -> None:
        """
        Publish an event to all subscribers
        
        Args:
            event_type: Type of event to publish
            *args, **kwargs: Arguments to pass to subscriber callbacks
        """
        with self.lock:
            if event_type not in self.subscribers:
                return
                
            # Take a copy of subscribers to avoid modification during iteration
            callbacks = self.subscribers[event_type].copy()
            once_callbacks = self.once_subscribers.get(event_type, set()).copy()
        
        # Call all subscribers outside the lock
        for callback in callbacks:
            try:
                callback(*args, **kwargs)
            except Exception as e:
                # Log error but continue with other subscribers
                from core.utils.logger import get_logger
                logger = get_logger()
                logger.error(f"Error in event handler for {event_type}: {e}")
        
        # Unsubscribe once-only subscribers
        if once_callbacks:
            with self.lock:
                for callback in once_callbacks:
                    if callback in self.subscribers[event_type]:
                        self.subscribers[event_type].remove(callback)
                    if event_type in self.once_subscribers and callback in self.once_subscribers[event_type]:
                        self.once_subscribers[event_type].remove(callback)


# Create a global event bus instance
event_bus = EventBus()

# Function to get the global event bus
def get_event_bus():
    """Get the global event bus instance"""
    return event_bus

# Convenience functions for event operations
def subscribe(event_type: EventType, callback: Callable) -> None:
    """Subscribe to an event type"""
    event_bus.subscribe(event_type, callback)

def subscribe_once(event_type: EventType, callback: Callable) -> None:
    """Subscribe to an event type and unsubscribe after first notification"""
    event_bus.subscribe_once(event_type, callback)

def unsubscribe(event_type: EventType, callback: Callable) -> bool:
    """Unsubscribe from an event type"""
    return event_bus.unsubscribe(event_type, callback)

def publish(event_type: EventType, *args, **kwargs) -> None:
    """Publish an event to all subscribers"""
    event_bus.publish(event_type, *args, **kwargs)