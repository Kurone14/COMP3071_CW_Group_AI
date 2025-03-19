"""
Menu action handlers for the warehouse robot simulation GUI.
"""

from tkinter import messagebox
from core.models.grid import CellType


class MenuHandlers:
    """Handlers for menu actions"""
    
    def __init__(self, app):
        """
        Initialize the menu handlers
        
        Args:
            app: The main application instance
        """
        self.app = app
    
    def on_new_simulation(self) -> None:
        """Handle new simulation menu action"""
        messagebox.showinfo("New Simulation", "Please use the reset button to start a new simulation")
    
    def on_set_grid_size(self) -> None:
        """Handle set grid size menu action"""
        from gui.components.dialogs import GridSizeDialog
        result = GridSizeDialog.show_dialog(self.app.root, self.app.width, self.app.height)
        if not result["cancelled"] and hasattr(self.app.controller, "resize_grid"):
            self.app.controller.resize_grid(result["width"], result["height"])
    
    def on_set_drop_point(self) -> None:
        """Handle set drop point menu action"""
        self.app.click_handler.set_mode("drop_point")
        self.app.canvas_view.canvas.config(cursor="crosshair")
        messagebox.showinfo("Set Drop Point", "Click on the grid to place the drop point")
    
    def on_toggle_obstacle(self) -> None:
        """Handle toggle obstacle menu action"""
        self.app.click_handler.set_mode("obstacle")
        self.app.canvas_view.canvas.config(cursor="plus")
        messagebox.showinfo("Toggle Obstacles", 
                          "Click on the grid to add or remove obstacles. Press ESC when done.")
        self.app.root.bind("<Escape>", lambda e: self.app.click_handler.exit_mode())
    
    def on_add_obstacle(self, obstacle_type) -> None:
        """
        Handle add obstacle menu action
        
        Args:
            obstacle_type: Type of obstacle to add (from CellType enum)
        """
        if obstacle_type == CellType.TEMPORARY_OBSTACLE:
            self.app.click_handler.set_mode("temp_obstacle")
            messagebox.showinfo("Add Temporary Obstacle", 
                              "Click on the grid to place temporary obstacles. These will disappear after ~10 cycles.")
                              
        elif obstacle_type == CellType.SEMI_PERMANENT_OBSTACLE:
            self.app.click_handler.set_mode("semi_perm_obstacle")
            messagebox.showinfo("Add Semi-Permanent Obstacle", 
                              "Click on the grid to place semi-permanent obstacles. These will disappear after ~30 cycles.")
                              
        elif obstacle_type == CellType.PERMANENT_OBSTACLE:
            self.app.click_handler.set_mode("obstacle")  # Reuse the toggle obstacle mode
            messagebox.showinfo("Add Permanent Obstacle", 
                              "Click on the grid to place permanent obstacles. These will not disappear.")
                              
        self.app.canvas_view.canvas.config(cursor="plus")
        self.app.root.bind("<Escape>", lambda e: self.app.click_handler.exit_mode())
    
    def on_about(self) -> None:
        """Handle about menu action"""
        messagebox.showinfo("About", 
                          "Autonomous Warehouse Robot Simulation\n\n"
                          "A simulation of autonomous robots navigating a warehouse environment\n"
                          "to pick up and deliver items while avoiding obstacles.")