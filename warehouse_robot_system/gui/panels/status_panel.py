"""
Status panel component for the warehouse robot simulation GUI.
Contains performance metrics and entity displays.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Callable

from core.models.grid import Grid
from core.models.robot import Robot
from core.models.item import Item
from gui.panels.obstacle_legend import ObstacleLegend
from gui.views.entity_display import RobotDisplay, ItemDisplay
from gui.components.dialogs import RobotEditDialog, ItemEditDialog


class StatusPanel:
    """Panel displaying performance metrics and entity information"""
    
    def __init__(self, app):
        """
        Initialize the status panel
        
        Args:
            app: The main application instance
        """
        self.app = app
        self.status_frame = tk.Frame(app.right_panel)
        self.status_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add obstacle legend if obstacle manager is available
        if app.obstacle_manager:
            self.obstacle_legend = ObstacleLegend(self.status_frame)
        
        # Title
        self.status_label = tk.Label(self.status_frame, text="Warehouse Status", 
                                   font=("Arial", 14, "bold"))
        self.status_label.pack(pady=(0, 10))
        
        # Create performance metrics section
        self._create_performance_section()
        
        # Items left count
        self.items_left_var = tk.StringVar(value="Items left: 0")
        self.items_left_label = tk.Label(self.status_frame, textvariable=self.items_left_var, 
                                       font=("Arial", 12))
        self.items_left_label.pack(pady=5)
        
        # Create entity display notebook
        self._create_entity_notebook()
        
        # Store edit/delete callback functions
        self.edit_robot_callback = None
        self.delete_robot_callback = None
        self.edit_item_callback = None
        self.delete_item_callback = None
    
    def _create_performance_section(self) -> None:
        """Create the performance metrics section"""
        self.performance_frame = tk.LabelFrame(self.status_frame, text="Performance")
        self.performance_frame.pack(fill=tk.X, pady=5)
        
        # Performance metric labels
        self.performance_labels = []
        for i in range(5):  # 5 performance metrics
            label = tk.Label(self.performance_frame, text="-", anchor="w")
            label.pack(fill=tk.X, padx=5, pady=2)
            self.performance_labels.append(label)
    
    def _create_entity_notebook(self) -> None:
        """Create the notebook with tabs for robots and items"""
        self.notebook = ttk.Notebook(self.status_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Robot display tab
        self.robot_display = RobotDisplay(self.notebook)
        
        # Item display tab
        self.item_display = ItemDisplay(self.notebook)
        
        # Add tabs to notebook
        self.notebook.add(self.robot_display.get_frame(), text="Robots")
        self.notebook.add(self.item_display.get_frame(), text="Items")
        
        # Set up callbacks for robot and item displays
        self.robot_display.set_select_callback(self.app.selection_handler.on_robot_selected)
        self.item_display.set_select_callback(self.app.selection_handler.on_item_selected)
    
    def set_robot_action_callbacks(self, edit_callback: Callable, delete_callback: Callable) -> None:
        """
        Set the callbacks for robot action buttons
        
        Args:
            edit_callback: Function to call when edit button is clicked
            delete_callback: Function to call when delete button is clicked
        """
        self.edit_robot_callback = edit_callback
        self.delete_robot_callback = delete_callback
        
        # Fix: Set up button callbacks with dialog handling
        self.robot_display.set_action_buttons(
            lambda: self._on_edit_robot(),
            lambda: self._on_delete_robot()
        )
    
    def set_item_action_callbacks(self, edit_callback: Callable, delete_callback: Callable) -> None:
        """
        Set the callbacks for item action buttons
        
        Args:
            edit_callback: Function to call when edit button is clicked
            delete_callback: Function to call when delete button is clicked
        """
        self.edit_item_callback = edit_callback
        self.delete_item_callback = delete_callback
        
        # Fix: Set up button callbacks with dialog handling
        self.item_display.set_action_buttons(
            lambda: self._on_edit_item(),
            lambda: self._on_delete_item()
        )
    
    def _on_edit_robot(self) -> None:
        """Handle edit robot button click with proper dialog and parameters"""
        if self.robot_display.selected_id is not None:
            # Find selected robot
            robot_id = self.robot_display.selected_id
            selected_robot = None
            for robot in self.app.robots:
                if robot.id == robot_id:
                    selected_robot = robot
                    break
            
            if selected_robot and self.edit_robot_callback:
                # Use the edit dialog to get parameters
                result = RobotEditDialog.show_dialog(self.app.root, selected_robot)
                if not result["cancelled"]:
                    # Call edit_robot with all required parameters
                    self.edit_robot_callback(robot_id, result["x"], result["y"], result["capacity"])
    
    def _on_delete_robot(self) -> None:
        """Handle delete robot button click"""
        if self.robot_display.selected_id is not None and self.delete_robot_callback:
            self.delete_robot_callback(self.robot_display.selected_id)
    
    def _on_edit_item(self) -> None:
        """Handle edit item button click with proper dialog and parameters"""
        if self.item_display.selected_id is not None:
            # Find selected item
            item_id = self.item_display.selected_id
            selected_item = None
            for item in self.app.items:
                if item.id == item_id:
                    selected_item = item
                    break
            
            if selected_item and self.edit_item_callback:
                # Use the edit dialog to get parameters
                result = ItemEditDialog.show_dialog(self.app.root, selected_item)
                if not result["cancelled"]:
                    # Call edit_item with all required parameters
                    self.edit_item_callback(item_id, result["x"], result["y"], result["weight"])
    
    def _on_delete_item(self) -> None:
        """Handle delete item button click"""
        if self.item_display.selected_id is not None and self.delete_item_callback:
            self.delete_item_callback(self.item_display.selected_id)
    
    def update(self, grid: Grid, robots: List[Robot], items: List[Item]) -> None:
        """
        Update all status panels with current data
        
        Args:
            grid: The grid model
            robots: List of robots
            items: List of items
        """
        # Update robot display
        self.robot_display.setup_robot_frames(robots, self.app.selection_handler.on_robot_selected)
        self.robot_display.update_status(robots)
        
        # Update item display
        self.item_display.update_items_list(items, self.app.selection_handler.on_item_selected)
        self.item_display.update_status(items)
        
        # Update items left count
        items_left = sum(1 for item in items if not item.picked)
        self.items_left_var.set(f"Items left: {items_left}")
    
    def update_performance_stats(self, stats: List[str]) -> None:
        """
        Update the performance statistics display
        
        Args:
            stats: List of formatted statistics strings
        """
        for i, stat in enumerate(stats):
            if i < len(self.performance_labels):
                self.performance_labels[i].config(text=stat)