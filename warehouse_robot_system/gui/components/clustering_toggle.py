"""
Component for toggling item clustering in the warehouse simulation GUI.
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


class ClusteringToggle:
    """
    Toggle component for enabling/disabling item clustering.
    This affects how robots pick up multiple nearby items at once.
    """
    
    def __init__(self, parent, simulation):
        """
        Initialize the clustering toggle
        
        Args:
            parent: Parent widget
            simulation: The main simulation instance
        """
        self.parent = parent
        self.simulation = simulation
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Item Clustering")
        self.frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create checkbox for toggle
        self.enabled_var = tk.BooleanVar(value=True)  # Default: enabled
        self.enabled_checkbox = ttk.Checkbutton(
            self.frame,
            text="Enable Item Clustering",
            variable=self.enabled_var,
            command=self._on_toggle_clustering
        )
        self.enabled_checkbox.pack(anchor=tk.W, padx=5, pady=(5,0))
        
        # Create a text widget for description with fixed width
        # This allows proper word wrapping
        self.description_text = tk.Text(
            self.frame,
            wrap=tk.WORD,
            height=2,
            width=30,
            font=("Arial", 8),
            bg=parent.cget("bg"),
            relief=tk.FLAT,
            padx=5
        )
        self.description_text.pack(fill=tk.X, padx=5, pady=(2,5))
        
        # Insert description
        description = "When enabled, robots will attempt to pick up multiple nearby items in a single trip if they fit within capacity."
        self.description_text.insert(tk.END, description)
        self.description_text.config(state=tk.DISABLED)  # Make read-only
        
        # Status label with fixed width and appropriate wrapping
        self.status_var = tk.StringVar(value="Status: Enabled")
        self.status_label = ttk.Label(
            self.frame,
            textvariable=self.status_var,
            font=("Arial", 8, "bold"),
            wraplength=250  # Force wrapping at this width
        )
        self.status_label.pack(anchor=tk.W, padx=5, pady=(0,5))
        
        # Initial state update
        self._update_status()
    
    def _on_toggle_clustering(self):
        """Handle toggle clustering checkbox"""
        enabled = self.enabled_var.get()
        
        # Update the item assigner's clustering flag
        if hasattr(self.simulation, 'item_assigner'):
            self.simulation.item_assigner.clustering_enabled = enabled
        
        # Update status display
        self._update_status()
    
    def _update_status(self):
        """Update the status label based on current state"""
        enabled = self.enabled_var.get()
        
        if enabled:
            self.status_var.set("Status: Enabled - Robots will collect multiple nearby items")
        else:
            self.status_var.set("Status: Disabled - Robots will collect one item at a time")
    
    def get_frame(self):
        """Get the main frame of this component"""
        return self.frame