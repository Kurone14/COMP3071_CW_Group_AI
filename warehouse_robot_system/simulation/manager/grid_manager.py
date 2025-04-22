"""
Manages the grid environment, including resizing and drop point placement.
"""

import tkinter as tk
from tkinter import messagebox
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
        print(f"GridManager: Resizing grid to {new_width}x{new_height}")
        grid = self.simulation.grid
        
        old_width, old_height = grid.width, grid.height
        
        # Check if any entities would be lost in a reduction
        if new_width < grid.width or new_height < grid.height:
            entities_at_risk = []
            
            # Check robots
            for robot in self.simulation.robots:
                if robot.x >= new_width or robot.y >= new_height:
                    entities_at_risk.append(f"Robot {robot.id} at ({robot.x}, {robot.y})")
            
            # Check items
            for item in self.simulation.items:
                if not item.picked and (item.x >= new_width or item.y >= new_height):
                    entities_at_risk.append(f"Item {item.id} at ({item.x}, {item.y})")
            
            # Check drop point
            if grid.drop_point and (grid.drop_point[0] >= new_width or grid.drop_point[1] >= new_height):
                entities_at_risk.append(f"Drop point at ({grid.drop_point[0]}, {grid.drop_point[1]})")
            
            if entities_at_risk:
                # Log the error
                error_msg = f"Cannot resize to {new_width}x{new_height}: {len(entities_at_risk)} entities would be lost"
                self.simulation.logger.error(error_msg)
                print(error_msg)
                
                # Show error message to user if GUI is available
                if self.simulation.gui:
                    from tkinter import messagebox
                    message = "Cannot resize grid: The following entities would be lost:\n"
                    message += "\n".join(entities_at_risk[:10])  # Show first 10 only to avoid huge dialogs
                    if len(entities_at_risk) > 10:
                        message += f"\n... and {len(entities_at_risk) - 10} more"
                    messagebox.showerror("Resize Error", message)
                
                return False
        
        print(f"Current grid size: {grid.width}x{grid.height}")
        
        # Resize grid while preserving entities
        if not grid.resize(new_width, new_height):
            error_msg = f"Failed to resize grid to {new_width}x{new_height}"
            print(error_msg)
            self.simulation.logger.error(error_msg)
            
            # Show error to user if GUI is available
            if self.simulation.gui:
                from tkinter import messagebox
                messagebox.showerror("Resize Error", "Failed to resize grid. Check console for details.")
            
            return False
        
        # Update width and height explicitly (make sure they're actually changed)
        grid.width = new_width
        grid.height = new_height
        
        print(f"After resize: Grid size is now {grid.width}x{grid.height}")
        
        # Update components with the new grid
        if self.simulation.path_finder:
            self.simulation.path_finder.grid = grid
            print("Updated path_finder grid")
        if self.simulation.item_assigner:
            self.simulation.item_assigner.grid = grid
            print("Updated item_assigner grid")
        if self.simulation.movement_controller:
            self.simulation.movement_controller.grid = grid
            print("Updated movement_controller grid")
        if self.simulation.stall_detector:
            self.simulation.stall_detector.grid = grid
            print("Updated stall_detector grid")
        if self.simulation.obstacle_manager:
            self.simulation.obstacle_manager.grid = grid
            print("Updated obstacle_manager grid")
        
        self.simulation.logger.info(f"Grid resized from {old_width}x{old_height} to {new_width}x{new_height}")
        
        # Publish grid resized event
        from core.utils.event_system import publish, EventType
        publish(EventType.GRID_RESIZED, {
            'old_width': old_width,
            'old_height': old_height,
            'new_width': new_width,
            'new_height': new_height,
            'grid': grid
        })
        print(f"Published grid resized event: {old_width}x{old_height} -> {new_width}x{new_height}")
        
        # Update GUI if connected
        if self.simulation.gui:
            print("Updating GUI with new grid size")
            # Force GUI to recognize the new grid dimensions
            self.simulation.gui.width = new_width
            self.simulation.gui.height = new_height
            
            # Resize the canvas if the method exists
            if hasattr(self.simulation.gui, 'canvas_view') and hasattr(self.simulation.gui.canvas_view, 'resize_canvas'):
                self.simulation.gui.canvas_view.resize_canvas(new_width, new_height)
            
            # Update the environment with the new grid
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
            
            # Show confirmation message
            from tkinter import messagebox
            messagebox.showinfo("Grid Resize", f"Grid resize completed. New size: {grid.width}x{grid.height}")
        else:
            print("GUI not connected, cannot update display")
        
        print(f"Grid resize complete. New size: {grid.width}x{grid.height}")
        
        return True