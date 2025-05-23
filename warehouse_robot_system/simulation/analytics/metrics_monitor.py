"""
Integrates metrics monitoring into the warehouse simulation GUI.
"""

import tkinter as tk
from simulation.analytics.metrics_calculator import SimulationMetricsCalculator

class MetricsMonitor:
    """
    Integrates metrics monitoring into the warehouse simulation GUI.
    This class creates a button in the GUI to open the metrics visualization.
    """
    
    def __init__(self, gui, simulation):
        """
        Initialize the metrics monitor
        
        Args:
            gui: The GUI application instance
            simulation: The simulation instance
        """
        self.gui = gui
        self.simulation = simulation
        
        # Create metrics calculator
        self.metrics_calculator = SimulationMetricsCalculator(simulation)
        
        # Flag to track if monitoring is active
        self.monitoring_active = False
        
        # Add metrics button to GUI
        self._add_metrics_button()
        
        # Setup periodic metrics collection
        self.collection_interval = 250  # milliseconds (faster updates)
    
    def _add_metrics_button(self):
        """Add metrics button to the GUI"""
        # Find a suitable place to add the button
        if hasattr(self.gui, 'control_panel') and hasattr(self.gui.control_panel, 'simulation_controls'):
            # Add to existing control panel
            metrics_button = tk.Button(
                self.gui.control_panel.simulation_controls,
                text="Metrics",
                command=self._toggle_metrics,
                background="#4CAF50",  # Green
                foreground="white"
            )
            metrics_button.pack(side=tk.LEFT, padx=5)
            self.metrics_button = metrics_button
        else:
            # Create a new button in the main window
            metrics_button = tk.Button(
                self.gui.root,
                text="Metrics",
                command=self._toggle_metrics,
                background="#4CAF50",  # Green
                foreground="white"
            )
            metrics_button.pack(side=tk.TOP, padx=5, pady=5)
            self.metrics_button = metrics_button
    
    def _toggle_metrics(self):
        """Toggle metrics monitoring on/off"""
        if not self.monitoring_active:
            # Start monitoring
            self.monitoring_active = True
            self.metrics_calculator.start_tracking()
            self._schedule_metrics_collection()
            self.metrics_button.config(background="#F44336")  # Red when active
            
            # Subscribe to simulation events
            if hasattr(self.simulation, 'event_bus'):
                from core.utils.event_system import EventType
                self.simulation.event_bus.subscribe(EventType.SIMULATION_STEP, self._on_simulation_step)
                self.simulation.event_bus.subscribe(EventType.SIMULATION_COMPLETED, self._on_simulation_completed)
        else:
            # Show metrics visualization if already monitoring
            self._show_metrics_visualization()
    
    def _schedule_metrics_collection(self):
        """Schedule periodic metrics collection"""
        if self.monitoring_active:
            # Collect metrics
            self.metrics_calculator.update_metrics()
            
            # If simulation is running, ensure data reflects current state
            if self.simulation.running and not self.simulation.paused:
                # Force immediate update of robot states
                # This ensures we capture robot movement between UI updates
                for robot_id, metrics in self.metrics_calculator.robot_metrics.items():
                    # Find the robot
                    for robot in self.simulation.robots:
                        if robot.id == robot_id:
                            # Update position tracking
                            metrics['previous_position'] = (robot.x, robot.y)
                            break
            
            # Schedule next collection
            self.gui.root.after(self.collection_interval, self._schedule_metrics_collection)
    
    def _on_simulation_step(self, event_data=None):
        """Handle simulation step event"""
        # Ensure metrics are up to date on each step
        self.metrics_calculator.update_metrics()
    
    def _on_simulation_completed(self, event_data=None):
        """Handle simulation completion event"""
        # Ensure we get the final state
        self.metrics_calculator.update_metrics()
        
        # Show metrics visualization
        self._show_metrics_visualization()
    
    def _show_metrics_visualization(self):
        """Show the metrics visualization window"""
        self.metrics_calculator.create_visualization_window()
    
    def reset_metrics(self):
        """Reset all metrics data"""
        if self.metrics_calculator:
            self.metrics_calculator.start_tracking()  # This resets the tracking data
            print("Metrics monitor data has been reset")
            return True
        return False

def add_metrics_monitor_to_gui(gui, simulation):
    """
    Add metrics monitoring to the GUI with proper integration
    
    Args:
        gui: The GUI application instance
        simulation: The simulation instance
    
    Returns:
        MetricsMonitor: The metrics monitor instance
    """
    from simulation.analytics.metrics_monitor import MetricsMonitor
    
    # Create metrics monitor
    metrics_monitor = MetricsMonitor(gui, simulation)
    
    # Store reference to metrics monitor in simulation for callbacks
    simulation.set_metrics_monitor(metrics_monitor)
    
    # Initialize the performance tracker with robot states if available
    if simulation.performance_tracker:
        simulation.performance_tracker.update_robot_states(simulation.robots)
    
    return metrics_monitor