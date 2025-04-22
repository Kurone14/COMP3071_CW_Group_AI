from typing import Tuple, Optional
from dataclasses import dataclass


class Item:
    """
    Represents an item that can be picked up and delivered by robots.
    """
    def __init__(self, item_id: int, x: int, y: int, weight: int):
        """
        Initialize an item
        
        Args:
            item_id: Unique identifier for the item
            x, y: Position of the item
            weight: Weight of the item
        """
        self.id = item_id
        self.x = x
        self.y = y
        self.weight = weight
        self.picked = False
        self.assigned = False
        
    @property
    def position(self) -> Tuple[int, int]:
        """Get current position as (x, y)"""
        return (self.x, self.y)
        
    @property
    def is_available(self) -> bool:
        """Check if item is available (not picked or assigned)"""
        return not self.picked and not self.assigned
        
    def assign_to_robot(self, robot_id: int) -> None:
        """Mark item as assigned to a robot"""
        self.assigned = True
        
    def mark_as_picked(self) -> None:
        """Mark item as picked"""
        self.picked = True
        
    def reset(self) -> None:
        """Reset item state for a new simulation"""
        self.picked = False
        self.assigned = False
        
    def to_dict(self) -> dict:
        """Convert item to dictionary for serialization"""
        return {
            'id': self.id,
            'x': self.x,
            'y': self.y,
            'weight': self.weight,
            'picked': self.picked,
            'assigned': self.assigned
        }
        
    def __repr__(self) -> str:
        """String representation of the item"""
        status = "available"
        if self.picked:
            status = "picked"
        elif self.assigned:
            status = "assigned"
            
        return f"Item({self.id}, pos=({self.x},{self.y}), weight={self.weight}, status={status})"