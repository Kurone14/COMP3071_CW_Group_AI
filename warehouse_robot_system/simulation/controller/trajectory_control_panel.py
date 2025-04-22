"""
Control panel for robot trajectory visualization settings.
"""

import tkinter as tk
from tkinter import ttk
import collections
from typing import Callable, Optional


class TrajectoryControlPanel:
    """
    Control panel for configuring robot trajectory visualization settings.
    """
    
    def __init__(self, parent, trajectory_tracker):
        """
        Initialize the trajectory control panel
        
        Args:
            parent: Parent widget
            trajectory_tracker: The trajectory tracker instance
        """
        self.parent = parent
        self.trajectory_tracker = trajectory_tracker
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Trajectory Visualization")
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create controls
        self._create_enable_toggle()
        self._create_history_slider()
        
    def _create_enable_toggle(self):
        """Create toggle for enabling/disabling trajectory visualization"""
        frame = ttk.Frame(self.frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Toggle checkbox
        self.enabled_var = tk.BooleanVar(value=self.trajectory_tracker.is_enabled())
        self.enabled_checkbox = ttk.Checkbutton(
            frame, 
            text="Show Robot Trajectories",
            variable=self.enabled_var,
            command=self._on_toggle_enabled
        )
        self.enabled_checkbox.pack(side=tk.LEFT, padx=5)
        
        # Clear button
        self.clear_button = ttk.Button(
            frame,
            text="Clear Trajectories",
            command=self._on_clear_trajectories
        )
        self.clear_button.pack(side=tk.RIGHT, padx=5)
        
    def _create_history_slider(self):
        """Create slider for adjusting history length"""
        frame = ttk.Frame(self.frame)
        frame.pack(fill=tk.X, padx=5, pady=2)
        
        # Label
        ttk.Label(frame, text="History Length:").pack(side=tk.LEFT, padx=5)
        
        # Slider
        self.history_var = tk.IntVar(value=self.trajectory_tracker.max_history)
        self.history_slider = ttk.Scale(
            frame,
            from_=10,
            to=200,
            orient=tk.HORIZONTAL,
            variable=self.history_var,
            command=self._on_history_changed
        )
        self.history_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Value label
        self.history_label = ttk.Label(frame, text=str(self.trajectory_tracker.max_history))
        self.history_label.pack(side=tk.RIGHT, padx=5)
        
    def _on_toggle_enabled(self):
        """Handle toggle of enabled state"""
        enabled = self.enabled_var.get()
        self.trajectory_tracker.toggle(enabled)
        
    def _on_clear_trajectories(self):
        """Handle clear button click"""
        self.trajectory_tracker.reset()
        
    def _on_history_changed(self, value):
        """Handle history slider change"""
        # Convert to integer and update label
        history = int(float(value))
        self.history_label.config(text=str(history))
        
        # Update tracker
        self.trajectory_tracker.max_history = history
        
        # Resize all existing trajectory deques
        for robot_id, trajectory in self.trajectory_tracker.trajectories.items():
            new_trajectory = collections.deque(trajectory, maxlen=history)
            self.trajectory_tracker.trajectories[robot_id] = new_trajectory
    
    def get_frame(self):
        """Get the main frame of this control panel"""
        return self.frame