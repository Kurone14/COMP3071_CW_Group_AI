"""
Manages the grid environment, including resizing and drop point placement.
"""

from core.models.grid import CellType
from core.utils.event_system import publish, EventType


class GridManager:
    """Manages the grid environment"""
    
    def __init__(self, simulation):
        """
        Initialize the grid manager
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def set_drop_point(self, x: int, y: int) -> bool:
        """
        Set the drop point location
        
        Args:
            x, y: Drop point coordinates
            
        Returns:
            bool: True if drop point was set successfully
        """
        grid = self.simulation.grid
        
        if not grid.in_bounds(x, y):
            self.simulation.logger.warning(f"Cannot set drop point at ({x},{y}): out of bounds")
            return False
            
        cell_type = grid.get_cell(x, y)
        if cell_type not in [CellType.EMPTY, CellType.DROP_POINT]:
            self.simulation.logger.warning(f"Cannot set drop point at ({x},{y}): position occupied")
            return False
            
        # Set the drop point in the grid
        if grid.set_drop_point(x, y):
            self.simulation.logger.info(f"Set drop point to ({x},{y})")
            
            # Update components that need to know the drop point
            if self.simulation.path_finder:
                self.simulation.path_finder.drop_point = (x, y)
            if self.simulation.movement_controller:
                self.simulation.movement_controller.drop_point = (x, y)
            if self.simulation.stall_detector:
                self.simulation.stall_detector.drop_point = (x, y)
                
            # Publish drop point set event
            publish(EventType.DROP_POINT_SET, {
                'drop_point': (x, y),
                'grid': grid
            })
            
            # Update GUI if connected
            if self.simulation.gui:
                self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
                
            return True
            
        return False
    
    def resize_grid(self, new_width: int, new_height: int) -> bool:
        """
        Resize the grid, preserving entities when possible
        
        Args:
            new_width, new_height: New grid dimensions
            
        Returns:
            bool: True if grid was resized successfully
        """
        grid = self.simulation.grid
        
        if new_width < grid.width or new_height < grid.height:
            self.simulation.logger.warning("Grid can only be expanded, not reduced in size.")
            return False
        
        old_width, old_height = grid.width, grid.height
        
        # Resize grid while preserving entities
        if not grid.resize(new_width, new_height):
            self.simulation.logger.error("Failed to resize grid")
            return False
        
        # Update width and height
        grid.width = new_width
        grid.height = new_height
        
        # Update components with the new grid
        if self.simulation.path_finder:
            self.simulation.path_finder.grid = grid
        if self.simulation.item_assigner:
            self.simulation.item_assigner.grid = grid
        if self.simulation.movement_controller:
            self.simulation.movement_controller.grid = grid
        if self.simulation.stall_detector:
            self.simulation.stall_detector.grid = grid
        if self.simulation.obstacle_manager:
            self.simulation.obstacle_manager.grid = grid
        
        self.simulation.logger.info(f"Grid resized from {old_width}x{old_height} to {new_width}x{new_height}")
        
        # Publish grid resized event
        publish(EventType.GRID_RESIZED, {
            'old_width': old_width,
            'old_height': old_height,
            'new_width': new_width,
            'new_height': new_height,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True