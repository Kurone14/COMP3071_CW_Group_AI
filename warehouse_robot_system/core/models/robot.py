from typing import List, Optional, Tuple
from dataclasses import dataclass, field


class Robot:
    """
    Represents a warehouse robot with movement and item carrying capabilities.
    """
    def __init__(self, robot_id: int, x: int, y: int, capacity: int):
        """
        Initialize a robot
        
        Args:
            robot_id: Unique identifier for the robot
            x, y: Initial position
            capacity: Maximum weight capacity
        """
        self.id = robot_id
        self.x = x
        self.y = y
        self.capacity = capacity
        
        # Current state
        self.current_weight = 0
        self.carrying_items = []
        self.target_items = []
        self.path = []
        self.steps = 0
        self.waiting = False
        
    @property
    def position(self) -> Tuple[int, int]:
        """Get current position as (x, y)"""
        return (self.x, self.y)
        
    @property
    def is_idle(self) -> bool:
        """Check if robot is idle (no path and not carrying items)"""
        return not self.path and not self.carrying_items
        
    @property
    def is_carrying(self) -> bool:
        """Check if robot is carrying any items"""
        return len(self.carrying_items) > 0
        
    def add_path(self, path: List[Tuple[int, int]]) -> None:
        """Set or append to the robot's path"""
        self.path = path
    
    def pick_up_item(self, item) -> bool:
        """
        Pick up an item if capacity allows
        
        Returns:
            bool: True if item was picked up successfully
        """
        if self.current_weight + item.weight > self.capacity:
            return False
            
        self.carrying_items.append(item)
        self.current_weight += item.weight
        
        if item in self.target_items:
            self.target_items.remove(item)
            
        item.picked = True
        return True
        
    def drop_items(self) -> List:
        """Drop all carried items and return them"""
        items = self.carrying_items
        self.carrying_items = []
        self.current_weight = 0
        return items
        
    def move_step(self) -> bool:
        """
        Move one step along the path
        
        Returns:
            bool: True if moved, False if couldn't move
        """
        if not self.path:
            return False
            
        next_y, next_x = self.path.pop(0)
        self.x, self.y = next_x, next_y
        self.steps += 1
        return True
        
    def reset(self, x: Optional[int] = None, y: Optional[int] = None) -> None:
        """
        Reset robot state for a new simulation
        
        Args:
            x, y: Optional new position, if not provided, keep current position
        """
        if x is not None and y is not None:
            self.x, self.y = x, y
            
        self.carrying_items = []
        self.target_items = []
        self.current_weight = 0
        self.path = []
        self.steps = 0
        self.waiting = False
    
    def to_dict(self) -> dict:
        """Convert robot to dictionary for serialization"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'capacity': self.capacity,
            'current_weight': self.current_weight,
            'carrying_items': [item.id for item in self.carrying_items],
            'path': self.path,
            'steps': self.steps,
            'waiting': self.waiting
        }
        
    def __repr__(self) -> str:
        """String representation of the robot"""
        status = "idle"
        if self.path:
            if self.carrying_items:
                status = "to_drop"
            else:
                status = "to_item"
                
        return f"Robot({self.id}, pos=({self.x},{self.y}), status={status}, items={len(self.carrying_items)})"