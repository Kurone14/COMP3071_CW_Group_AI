"""
Control panel component for the warehouse robot simulation GUI.
Contains simulation control buttons and entity controls.
"""

import tkinter as tk
from core.models.grid import CellType


class ControlPanel:
    """Panel with simulation control buttons and entity control buttons"""
    
    def __init__(self, app):
        """
        Initialize the control panel
        
        Args:
            app: The main application instance
        """
        self.app = app
        self.control_frame = tk.Frame(app.left_panel)
        self.control_frame.pack(pady=10, fill=tk.X)
        
        # Create control button sections
        self._create_simulation_controls()
        self._create_obstacle_controls()
        self._create_entity_controls()
    
    def _create_simulation_controls(self) -> None:
        """Create simulation control buttons (start, pause, reset)"""
        self.simulation_controls = tk.Frame(self.control_frame)
        self.simulation_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.start_button = tk.Button(self.simulation_controls, text="Start", 
                                    command=self._on_start_click)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(self.simulation_controls, text="Pause", 
                                    state=tk.DISABLED, command=self._on_pause_click)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = tk.Button(self.simulation_controls, text="Reset", 
                                    command=self._on_reset_click)
        self.reset_button.pack(side=tk.LEFT, padx=5)
    
    def _create_obstacle_controls(self) -> None:
        """Create obstacle control buttons if obstacle manager is available"""
        if not self.app.obstacle_manager:
            return
            
        self.obstacle_type_label = tk.Label(self.simulation_controls, text="Obstacle Types:")
        self.obstacle_type_label.pack(side=tk.LEFT, padx=(10, 2))
        
        # Temporary obstacle button
        self.temp_obstacle_button = tk.Button(
            self.simulation_controls, 
            text="Temporary", 
            background="#FFA500",  # Orange
            foreground="white",
            command=lambda: self._on_add_obstacle(CellType.TEMPORARY_OBSTACLE)
        )
        self.temp_obstacle_button.pack(side=tk.LEFT, padx=2)
        
        # Semi-permanent obstacle button
        self.semi_perm_obstacle_button = tk.Button(
            self.simulation_controls, 
            text="Semi-Perm", 
            background="#8B4513",  # Brown
            foreground="white",
            command=lambda: self._on_add_obstacle(CellType.SEMI_PERMANENT_OBSTACLE)
        )
        self.semi_perm_obstacle_button.pack(side=tk.LEFT, padx=2)
        
        # Permanent obstacle button
        self.perm_obstacle_button = tk.Button(
            self.simulation_controls, 
            text="Permanent", 
            background="gray",
            foreground="white",
            command=lambda: self._on_add_obstacle(CellType.PERMANENT_OBSTACLE)
        )
        self.perm_obstacle_button.pack(side=tk.LEFT, padx=2)
    
    def _create_entity_controls(self) -> None:
        """Create entity control buttons (add robot, add item, roadblock)"""
        self.entity_controls = tk.Frame(self.control_frame)
        self.entity_controls.pack(side=tk.RIGHT)
        
        self.add_robot_button = tk.Button(self.entity_controls, text="Add Robot", 
                                        command=self._on_add_robot_click)
        self.add_robot_button.pack(side=tk.LEFT, padx=5)
        
        self.add_item_button = tk.Button(self.entity_controls, text="Add Item", 
                                       command=self._on_add_item_click)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        
        self.roadblock_button = tk.Button(self.entity_controls, text="Add Roadblock", 
                                        command=self._on_add_roadblock_click)
        self.roadblock_button.pack(side=tk.LEFT, padx=5)
        self.roadblock_button.config(state=tk.DISABLED)  # Initially disabled
    
    def enable_controls(self, enable: bool = True) -> None:
        """
        Enable or disable entity control buttons
        
        Args:
            enable: True to enable, False to disable
        """
        state = tk.NORMAL if enable else tk.DISABLED
        self.add_robot_button.config(state=state)
        self.add_item_button.config(state=state)
        
        # Enable/disable obstacle type buttons if they exist
        if hasattr(self, 'temp_obstacle_button'):
            self.temp_obstacle_button.config(state=state)
            self.semi_perm_obstacle_button.config(state=state)
            self.perm_obstacle_button.config(state=state)
        
        # Roadblock button is opposite (enabled during simulation, disabled during setup)
        if enable:
            self.roadblock_button.config(state=tk.DISABLED)
        else:
            self.roadblock_button.config(state=tk.NORMAL)
    
    # Button event handlers
    def _on_start_click(self) -> None:
        """Handle start button click"""
        if self.app.start_callback:
            self.app.start_callback()
    
    def _on_pause_click(self) -> None:
        """Handle pause button click"""
        if self.app.pause_callback:
            self.app.pause_callback()
    
    def _on_reset_click(self) -> None:
        """Handle reset button click"""
        if self.app.reset_callback:
            self.app.reset_callback()
    
    def _on_add_robot_click(self) -> None:
        """Handle add robot button click"""
        from tkinter import messagebox
        
        self.app.click_handler.set_mode("robot", self.add_robot_button)
        self.app.canvas_view.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Robot", "Click on the grid to place a new robot")
    
    def _on_add_item_click(self) -> None:
        """Handle add item button click"""
        from tkinter import messagebox
        
        self.app.click_handler.set_mode("item", self.add_item_button)
        self.app.canvas_view.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Item", "Click on the grid to place a new item")
    
    def _on_add_roadblock_click(self) -> None:
        """Handle add roadblock button click"""
        from tkinter import messagebox
        
        self.app.click_handler.set_mode("roadblock", self.roadblock_button)
        self.app.canvas_view.canvas.config(cursor="crosshair")
        messagebox.showinfo("Add Roadblocks", "Click on the grid to place roadblocks. Press ESC when done.")
        self.app.root.bind("<Escape>", lambda e: self.app.click_handler.exit_mode())
    
    def _on_add_obstacle(self, obstacle_type) -> None:
        """
        Handle add obstacle button click
        
        Args:
            obstacle_type: Type of obstacle to add
        """
        button = None
        
        if obstacle_type == CellType.TEMPORARY_OBSTACLE:
            self.app.click_handler.set_mode("temp_obstacle", self.temp_obstacle_button)
            button = self.temp_obstacle_button
        elif obstacle_type == CellType.SEMI_PERMANENT_OBSTACLE:
            self.app.click_handler.set_mode("semi_perm_obstacle", self.semi_perm_obstacle_button)
            button = self.semi_perm_obstacle_button
        elif obstacle_type == CellType.PERMANENT_OBSTACLE:
            self.app.click_handler.set_mode("obstacle", self.perm_obstacle_button)
            button = self.perm_obstacle_button
            
        if button:
            button.config(relief=tk.SUNKEN)
            self.app.canvas_view.canvas.config(cursor="plus")
            self.app.root.bind("<Escape>", lambda e: self.app.click_handler.exit_mode())