"""
Click handler component for the warehouse robot simulation GUI.
Manages and processes canvas click events.
"""

import tkinter as tk
from tkinter import simpledialog


class ClickHandler:
    """Handles canvas click events and manages interaction modes"""
    
    def __init__(self, app):
        """
        Initialize the click handler
        
        Args:
            app: The main application instance
        """
        self.app = app
        self.mode = None
        self.active_button = None
    
    def set_mode(self, mode: str, button=None) -> None:
        """
        Set the current interaction mode
        
        Args:
            mode: The mode to set ('robot', 'item', 'obstacle', etc.)
            button: The button that was clicked to activate this mode
        """
        self.mode = mode
        
        # Reset previous active button if exists
        if self.active_button and self.active_button != button:
            self.active_button.config(relief=tk.RAISED)
        
        # Set new active button
        self.active_button = button
        if button:
            button.config(relief=tk.SUNKEN)
    
    def exit_mode(self) -> None:
        """Exit the current interaction mode"""
        self.mode = None
        
        # Reset active button
        if self.active_button:
            self.active_button.config(relief=tk.RAISED)
            self.active_button = None
        
        # Reset cursor
        self.app.canvas_view.canvas.config(cursor="")
        
        # Unbind escape key
        self.app.root.unbind("<Escape>")
    
    def on_canvas_click(self, event) -> None:
        """
        Handle clicks on the canvas based on current mode
        
        Args:
            event: Mouse click event
        """
        if not self.mode:
            return
            
        # Calculate grid coordinates from mouse position
        cell_size = self.app.canvas_view.cell_size
        x = event.x // cell_size
        y = event.y // cell_size
        
        if x < 0 or x >= self.app.width or y < 0 or y >= self.app.height:
            return
            
        # Handle click based on current mode
        if self.mode == "robot" and self.app.add_robot_callback:
            self._handle_add_robot(x, y)
            
        elif self.mode == "item" and self.app.add_item_callback:
            self._handle_add_item(x, y)
                
        elif self.mode == "roadblock" and hasattr(self.app.controller, "add_roadblock"):
            self.app.controller.add_roadblock(x, y)
            
        elif self.mode == "drop_point" and hasattr(self.app.controller, "set_drop_point"):
            self.app.controller.set_drop_point(x, y)
            self.exit_mode()
            
        elif self.mode == "obstacle" and hasattr(self.app.controller, "toggle_obstacle"):
            self.app.controller.toggle_obstacle(x, y)
            
        elif self.mode == "temp_obstacle" and hasattr(self.app.controller, "add_temporary_obstacle"):
            self.app.controller.add_temporary_obstacle(x, y)
            
        elif self.mode == "semi_perm_obstacle" and hasattr(self.app.controller, "add_semi_permanent_obstacle"):
            self.app.controller.add_semi_permanent_obstacle(x, y)
    
    def _handle_add_robot(self, x: int, y: int) -> None:
        """
        Handle adding a robot at specified coordinates
        
        Args:
            x, y: Grid coordinates
        """
        self.app.add_robot_callback(x, y)
        self.exit_mode()
    
    def _handle_add_item(self, x: int, y: int) -> None:
        """
        Handle adding an item at specified coordinates
        
        Args:
            x, y: Grid coordinates
        """
        # Prompt for item weight
        weight = simpledialog.askinteger("Item Weight", "Enter item weight (kg):", 
                                        minvalue=1, maxvalue=10)
        if weight:
            self.app.add_item_callback(x, y, weight)
            self.exit_mode()