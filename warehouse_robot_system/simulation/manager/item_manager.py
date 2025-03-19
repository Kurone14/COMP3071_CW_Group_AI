"""
Manages item creation, editing, and deletion.
"""

import random
from typing import Optional

from core.models.grid import CellType
from core.models.item import Item
from core.utils.event_system import publish, EventType


class ItemManager:
    """Manages item entities in the simulation"""
    
    def __init__(self, simulation):
        """
        Initialize the item manager
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def create_item(self, item_id: int) -> Item:
        """
        Create an item with a valid position
        
        Args:
            item_id: ID to assign to the item
            
        Returns:
            Item: The created item
        """
        grid = self.simulation.grid
        
        # Try to place item in top half of grid
        attempts = 0
        while attempts < 100:
            item_x = random.randint(1, grid.width - 2)
            item_y = random.randint(1, grid.height // 2)
            
            if grid.is_cell_empty(item_x, item_y):
                break
                
            attempts += 1
        
        if attempts >= 100:
            self.simulation.logger.warning(f"Could not find empty space for item {item_id}")
            # Last resort, find any empty cell
            for y in range(grid.height):
                for x in range(grid.width):
                    if grid.is_cell_empty(x, y):
                        item_x, item_y = x, y
                        break
        
        # Create item with random weight
        weight = random.randint(1, 8)
        item = Item(item_id, item_x, item_y, weight)
        
        # Register item in grid
        grid.set_cell(item_x, item_y, CellType.ITEM)
        self.simulation.items.append(item)
        
        self.simulation.logger.info(f"Created item {item_id} at ({item_x}, {item_y}) with weight {weight}")
        
        # Publish item added event
        publish(EventType.ITEM_ADDED, {
            'item': item,
            'grid': grid
        })
        
        return item
    
    def add_item(self, x: int, y: int, weight: Optional[int] = None) -> bool:
        """
        Add a new item at specified position
        
        Args:
            x, y: Position coordinates
            weight: Optional weight (default: random)
            
        Returns:
            bool: True if item was added successfully
        """
        grid = self.simulation.grid
        
        if not grid.is_cell_empty(x, y):
            self.simulation.logger.warning(f"Cannot place item at ({x}, {y}): position not empty")
            return False
        
        # Generate item ID
        item_id = max(item.id for item in self.simulation.items) + 1 if self.simulation.items else 0
        
        # Set weight
        if weight is None:
            weight = random.randint(1, 8)
        
        # Create item
        item = Item(item_id, x, y, weight)
        self.simulation.items.append(item)
        
        # Register in grid
        grid.set_cell(x, y, CellType.ITEM)
        
        self.simulation.logger.info(f"Added item {item_id} at ({x}, {y}) with weight {weight}kg")
        
        # Publish item added event
        publish(EventType.ITEM_ADDED, {
            'item': item,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True
    
    def edit_item(self, item_id: int, new_x: int, new_y: int, new_weight: int) -> bool:
        """
        Edit an existing item
        
        Args:
            item_id: ID of the item to edit
            new_x, new_y: New position coordinates
            new_weight: New weight
            
        Returns:
            bool: True if item was edited successfully
        """
        grid = self.simulation.grid
        
        # Find item by ID
        item = next((i for i in self.simulation.items if i.id == item_id), None)
        if not item:
            self.simulation.logger.warning(f"Item {item_id} not found")
            return False
        
        # Check if item is assigned or picked
        if item.picked or item.assigned:
            self.simulation.logger.warning(f"Cannot edit item {item_id} while it is picked or assigned")
            return False
        
        # Update position if changed
        if (new_x, new_y) != (item.x, item.y):
            if not grid.is_cell_empty(new_x, new_y):
                self.simulation.logger.warning(f"Cannot move item to ({new_x}, {new_y}): position not empty")
                return False
            
            # Update grid
            grid.set_cell(item.x, item.y, CellType.EMPTY)
            
            item.x, item.y = new_x, new_y
            
            grid.set_cell(new_x, new_y, CellType.ITEM)
        
        # Update weight if changed
        if new_weight != item.weight:
            item.weight = new_weight
        
        self.simulation.logger.info(f"Updated item {item_id} to position ({new_x}, {new_y}) with weight {new_weight}kg")
        
        # Publish item updated event
        publish(EventType.ITEM_ADDED, {  # Reusing ITEM_ADDED for updates
            'item': item,
            'grid': grid,
            'is_update': True
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True
    
    def delete_item(self, item_id: int) -> bool:
        """
        Delete an existing item
        
        Args:
            item_id: ID of the item to delete
            
        Returns:
            bool: True if item was deleted successfully
        """
        grid = self.simulation.grid
        
        # Find item by ID and index
        item_index = None
        for i, item in enumerate(self.simulation.items):
            if item.id == item_id:
                item_index = i
                break
                
        if item_index is None:
            self.simulation.logger.warning(f"Item {item_id} not found")
            return False
        
        item = self.simulation.items[item_index]
        
        # Check if item is picked or assigned
        if item.picked or item.assigned:
            self.simulation.logger.warning(f"Cannot delete item {item_id} while it is picked or assigned")
            return False
        
        # Update grid
        grid.set_cell(item.x, item.y, CellType.EMPTY)
        
        # Remove item from list
        self.simulation.items.pop(item_index)
        
        self.simulation.logger.info(f"Deleted item {item_id}")
        
        # Publish item deleted event
        publish(EventType.ITEM_DELETED, {
            'item_id': item_id,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True