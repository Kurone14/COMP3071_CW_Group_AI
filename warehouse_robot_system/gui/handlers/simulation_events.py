"""
Simulation event handler component for the warehouse robot simulation GUI.
Handles simulation lifecycle events (start, pause, reset, complete).
"""

import tkinter as tk
from tkinter import messagebox


class SimulationEventHandler:
    """Handles simulation lifecycle events"""
    
    def __init__(self, app):
        """
        Initialize the simulation event handler
        
        Args:
            app: The main application instance
        """
        self.app = app
    
    def on_simulation_started(self) -> None:
        """Handle simulation start event"""
        self.app.control_panel.start_button.config(state=tk.DISABLED)
        self.app.control_panel.pause_button.config(state=tk.NORMAL, text="Pause")
        self.app.control_panel.enable_controls(False)
    
    def on_simulation_paused(self) -> None:
        """Handle simulation pause event"""
        self.app.control_panel.pause_button.config(text="Resume")
    
    def on_simulation_resumed(self) -> None:
        """Handle simulation resume event"""
        self.app.control_panel.pause_button.config(text="Pause")
    
    def on_simulation_reset(self) -> None:
        """Handle simulation reset event"""
        self.app.control_panel.start_button.config(state=tk.NORMAL)
        self.app.control_panel.pause_button.config(state=tk.DISABLED, text="Pause")
        self.app.control_panel.enable_controls(True)
    
    def on_simulation_completed(self) -> None:
        """Handle simulation completion event"""
        self.app.control_panel.start_button.config(state=tk.NORMAL)
        self.app.control_panel.pause_button.config(state=tk.DISABLED)
        self.app.control_panel.enable_controls(True)
        messagebox.showinfo("Simulation Complete", "All items have been collected and delivered!")