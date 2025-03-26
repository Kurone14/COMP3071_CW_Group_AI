"""
Manages the simulation lifecycle (start, pause, resume, etc.)
"""

import time
import tkinter as tk  # Add this import for tk.NORMAL
from core.utils.event_system import publish, EventType


class SimulationManager:
    """Manages the lifecycle of the simulation"""
    
    def __init__(self, simulation):
        """
        Initialize the simulation manager
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def start(self) -> None:
        """Start the simulation"""
        if not self.simulation.running:
            self.simulation.running = True
            self.simulation.paused = False
            
            # Start performance tracking
            if self.simulation.performance_tracker:
                self.simulation.performance_tracker.start()
            
            self.simulation.logger.info("Simulation started")
            
            # Publish simulation started event
            publish(EventType.SIMULATION_STARTED, {
                'robots': self.simulation.robots,
                'items': self.simulation.items,
                'grid': self.simulation.grid
            })
            
            # If GUI is connected, start simulation loop through GUI
            if self.simulation.gui:
                # Direct use of the event handler
                if hasattr(self.simulation.gui, 'event_handler'):
                    self.simulation.gui.event_handler.on_simulation_started()
                else:
                    # Backward compatibility
                    self.simulation.gui.on_simulation_started()
                    
                self.simulation.gui.schedule_next_step(self.simulation.simulation_step)
    
    def toggle_pause(self) -> None:
        """Pause or resume the simulation"""
        self.simulation.paused = not self.simulation.paused
        
        if self.simulation.performance_tracker:
            if self.simulation.paused:
                self.simulation.performance_tracker.stop()
            else:
                self.simulation.performance_tracker.start()
        
        self.simulation.logger.info(f"Simulation {'paused' if self.simulation.paused else 'resumed'}")
        
        # Publish appropriate event
        if self.simulation.paused:
            publish(EventType.SIMULATION_PAUSED, {})
        else:
            publish(EventType.SIMULATION_RESUMED, {})
            
        if self.simulation.gui:
            # Direct use of the event handler
            if hasattr(self.simulation.gui, 'event_handler'):
                if self.simulation.paused:
                    self.simulation.gui.event_handler.on_simulation_paused()
                else:
                    self.simulation.gui.event_handler.on_simulation_resumed()
            else:
                # Backward compatibility
                if self.simulation.paused:
                    self.simulation.gui.on_simulation_paused()
                else:
                    self.simulation.gui.on_simulation_resumed()
                    
            if not self.simulation.paused:
                self.simulation.gui.schedule_next_step(self.simulation.simulation_step)
                
            # When paused, enable obstacle and item controls to allow additions
            if self.simulation.paused:
                if hasattr(self.simulation.gui, 'control_panel'):
                    # Enable add obstacle and item buttons during pause
                    if hasattr(self.simulation.gui.control_panel, 'add_obstacle_button'):
                        self.simulation.gui.control_panel.add_obstacle_button.config(state=tk.NORMAL)
                    if hasattr(self.simulation.gui.control_panel, 'add_item_button'):
                        self.simulation.gui.control_panel.add_item_button.config(state=tk.NORMAL)
    
    def run_headless(self) -> None:
        """Run the simulation without GUI (for testing)"""
        self.simulation.logger.info("Starting headless simulation...")
        self.start()
        
        while self.simulation.running and not self.simulation.paused:
            continue_sim = self.simulation.simulation_step()
            if not continue_sim:
                break
            
            # Add a small delay for CPU usage
            time.sleep(0.1)
            
        self.simulation.logger.info("Headless simulation completed.")
    
    def handle_simulation_completed(self) -> None:
        """Handle simulation completion"""
        self.simulation.running = False
        
        if self.simulation.performance_tracker:
            self.simulation.performance_tracker.stop()
        
        self.simulation.logger.info("Simulation completed: All items collected and delivered!")
        
        # Publish simulation completed event
        publish(EventType.SIMULATION_COMPLETED, {
            'total_steps': self.simulation.performance_tracker.total_robot_steps if self.simulation.performance_tracker else 0,
            'total_items': self.simulation.performance_tracker.total_items_delivered if self.simulation.performance_tracker else 0,
            'elapsed_time': self.simulation.performance_tracker.get_elapsed_time() if self.simulation.performance_tracker else 0
        })
        
        if self.simulation.gui:
            # Direct use of the event handler
            if hasattr(self.simulation.gui, 'event_handler'):
                self.simulation.gui.event_handler.on_simulation_completed()
            else:
                # Backward compatibility
                self.simulation.gui.on_simulation_completed()
                
            if self.simulation.performance_tracker:
                self.simulation.gui.update_performance_stats(self.simulation.performance_tracker.format_statistics())