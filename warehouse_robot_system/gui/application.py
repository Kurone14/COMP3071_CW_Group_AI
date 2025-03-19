"""
Main GUI application for the warehouse robot system.
Manages all visual components and user interactions.
"""

import tkinter as tk
from typing import List, Callable, Optional

from core.models.grid import Grid
from core.models.robot import Robot
from core.models.item import Item

# Import refactored components
from gui.components.main_menu import MainMenuBar
from gui.panels.control_panel import ControlPanel
from gui.panels.status_panel import StatusPanel
from gui.views.canvas_view import CanvasView
from gui.handlers.click_handler import ClickHandler
from gui.handlers.entity_selection import SelectionHandler
from gui.handlers.simulation_events import SimulationEventHandler
from gui.components.main_controller import MainController


class WarehouseGUI:
    """
    Main GUI application for the warehouse simulation.
    Manages all visual components and user interactions.
    """
    
    def __init__(self, width: int, height: int, grid: Grid, path_finder, obstacle_manager=None):
        """
        Initialize the GUI application
        
        Args:
            width: Width of the grid in cells
            height: Height of the grid in cells
            grid: Grid model
            path_finder: PathFinder instance for path visualization
            obstacle_manager: Optional obstacle manager for advanced visualization
        """
        self.width = width
        self.height = height
        self.grid = grid
        self.path_finder = path_finder
        self.obstacle_manager = obstacle_manager
        
        # Initialize simulation state
        self.robots = []
        self.items = []
        self.selected_robot_id = None
        self.selected_item_id = None
        
        # Initialize Tkinter
        self.root = tk.Tk()
        self.root.title("Autonomous Warehouse Robot Simulation")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # Set minimum size for the window
        self.root.minsize(800, 600)
        
        # Initialize component handlers - IMPORTANT: Create these before UI components
        self.selection_handler = SelectionHandler(self)
        self.click_handler = ClickHandler(self)
        self.event_handler = SimulationEventHandler(self)
        
        # Create main layout
        self._create_layout()
        
        # Initialize main controller
        self.controller = MainController(self)
        
        # Initialize callbacks
        self.start_callback = None
        self.pause_callback = None
        self.reset_callback = None
        self.add_robot_callback = None
        self.add_item_callback = None
        self.edit_robot_callback = None
        self.delete_robot_callback = None
        self.edit_item_callback = None
        self.delete_item_callback = None
    
    def _create_layout(self) -> None:
        """Create the main application layout"""
        # Main container with proper weight configuration
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Configure row and column weights to allow proper expansion
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)
        
        # Create menu bar
        self.menu_bar = MainMenuBar(self)
        
        # Main content frame with horizontal layout
        self.content_frame = tk.Frame(self.main_container)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - make this expandable
        self.left_panel = tk.Frame(self.content_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Make sure left panel expands properly
        self.left_panel.grid_columnconfigure(0, weight=1)
        self.left_panel.grid_rowconfigure(0, weight=1)
        
        # Initialize canvas view for grid visualization with centering
        self.canvas_view = CanvasView(self.left_panel, self.width, self.height)
        
        # Create control panel
        self.control_panel = ControlPanel(self)
        
        # Right panel (Status and Entity displays)
        self.right_panel = tk.Frame(self.content_frame, width=350)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, expand=False, padx=5, pady=5)
        self.right_panel.pack_propagate(False)
        
        # Create status panel
        self.status_panel = StatusPanel(self)
    
    def set_simulation_controller(self, start_callback: Callable, pause_callback: Callable, 
                                reset_callback: Callable, add_robot_callback: Callable, 
                                add_item_callback: Callable, edit_robot_callback: Callable, 
                                delete_robot_callback: Callable, edit_item_callback: Callable, 
                                delete_item_callback: Callable) -> None:
        """
        Set the simulation controller callbacks
        
        Args:
            start_callback: Callback for starting simulation
            pause_callback: Callback for pausing/resuming simulation
            reset_callback: Callback for resetting simulation
            add_robot_callback: Callback for adding a robot
            add_item_callback: Callback for adding an item
            edit_robot_callback: Callback for editing a robot
            delete_robot_callback: Callback for deleting a robot
            edit_item_callback: Callback for editing an item
            delete_item_callback: Callback for deleting an item
        """
        self.start_callback = start_callback
        self.pause_callback = pause_callback
        self.reset_callback = reset_callback
        self.add_robot_callback = add_robot_callback
        self.add_item_callback = add_item_callback
        
        # Set up robot and item action callbacks
        self.status_panel.set_robot_action_callbacks(
            lambda: edit_robot_callback(self.selected_robot_id),
            lambda: delete_robot_callback(self.selected_robot_id)
        )
        
        self.status_panel.set_item_action_callbacks(
            lambda: edit_item_callback(self.selected_item_id),
            lambda: delete_item_callback(self.selected_item_id)
        )
        
        # Set canvas click handler
        self.canvas_view.set_click_handler(self.click_handler.on_canvas_click)

    def on_simulation_started(self):
        """Handle simulation start event"""
        self.event_handler.on_simulation_started()
    
    def on_simulation_paused(self):
        """Handle simulation pause event"""
        self.event_handler.on_simulation_paused()
        
    def on_simulation_resumed(self):
        """Handle simulation resume event"""
        self.event_handler.on_simulation_resumed()
        
    def on_simulation_reset(self):
        """Handle simulation reset event"""
        self.event_handler.on_simulation_reset()
        
    def on_simulation_completed(self):
        """Handle simulation completion event"""
        self.event_handler.on_simulation_completed()
    
    def update_environment(self, grid: Grid, robots: List[Robot], items: List[Item]) -> None:
        """
        Update the environment visualization
        
        Args:
            grid: Updated grid model
            robots: List of robots
            items: List of items
        """
        self.grid = grid
        self.robots = robots
        self.items = items
        
        # Update canvas with current state
        self.canvas_view.draw_environment(
            grid, self.width, self.height, grid.drop_point, robots, items,
            self.selected_robot_id, self.selected_item_id, self.obstacle_manager
        )
        
        # Update status panels
        self.status_panel.update(grid, robots, items)
    
    def update_performance_stats(self, stats: List[str]) -> None:
        """
        Update the performance statistics display
        
        Args:
            stats: List of formatted statistics strings
        """
        self.status_panel.update_performance_stats(stats)
    
    def enable_controls(self, enable: bool = True) -> None:
        """
        Enable or disable entity control buttons
        
        Args:
            enable: True to enable, False to disable
        """
        self.control_panel.enable_controls(enable)
    
    def schedule_next_step(self, step_function: Callable) -> None:
        """
        Schedule the next simulation step
        
        Args:
            step_function: Function to call for the next step
        """
        if not hasattr(self, 'paused') or not self.paused:
            self.root.after(300, step_function)
    
    def _on_close(self) -> None:
        """Handle application close"""
        from tkinter import messagebox
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.root.destroy()
    
    def run(self) -> None:
        """Run the GUI application"""
        # Set initial window size
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        initial_width = min(1024, screen_width - 100)
        initial_height = min(768, screen_height - 100)
        self.root.geometry(f"{initial_width}x{initial_height}")
        
        self.root.mainloop()