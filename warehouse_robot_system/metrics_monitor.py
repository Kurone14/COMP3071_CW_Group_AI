import tkinter as tk
from metrics_calculator import SimulationMetricsCalculator

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
        self.collection_interval = 500  # milliseconds
    
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
            
            # Schedule next collection
            self.gui.root.after(self.collection_interval, self._schedule_metrics_collection)
    
    def _on_simulation_step(self, event_data=None):
        """Handle simulation step event"""
        # Update metrics on each step (already handled by scheduled collection)
        pass
    
    def _on_simulation_completed(self, event_data=None):
        """Handle simulation completion event"""
        # Ensure we get the final state
        self.metrics_calculator.update_metrics()
        
        # Show metrics visualization
        self._show_metrics_visualization()
    
    def _show_metrics_visualization(self):
        """Show the metrics visualization window"""
        self.metrics_calculator.create_visualization_window()

def add_metrics_monitor_to_gui(gui, simulation):
    """
    Add metrics monitoring to the GUI
    
    Args:
        gui: The GUI application instance
        simulation: The simulation instance
    
    Returns:
        MetricsMonitor: The metrics monitor instance
    """
    metrics_monitor = MetricsMonitor(gui, simulation)
    return metrics_monitor