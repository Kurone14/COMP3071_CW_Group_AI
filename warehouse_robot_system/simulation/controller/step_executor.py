"""
Executes simulation steps and manages the main simulation loop.
"""

from core.utils.event_system import publish, EventType
from core.models.grid import CellType


class StepExecutor:
    """Executes simulation steps and controls the simulation loop"""
    
    def __init__(self, simulation):
        """
        Initialize the step executor
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def execute_step(self) -> bool:
        """
        Perform one simulation step
        
        Returns:
            bool: True if simulation should continue, False if completed
        """
        if not self.simulation.running or self.simulation.paused:
            return False
        
        # Add a cycle counter if it doesn't exist
        if not hasattr(self, 'cycle_counter'):
            self.cycle_counter = 0
        self.cycle_counter += 1
        
        # Every 200 cycles, check if we need to force unstick all robots
        if self.cycle_counter % 200 == 0:
            items_delivered = self.simulation.performance_tracker.total_items_delivered if self.simulation.performance_tracker else 0
            robots_carrying = sum(1 for robot in self.simulation.robots if robot.carrying_items)
            
            # If no items delivered in 200 cycles and robots are carrying items, force reset
            if items_delivered == 0 and robots_carrying > 0:
                print("WARNING: Simulation appears completely stuck. Forcing reset of all robots")
                drop_x, drop_y = self.simulation.grid.drop_point
                
                for robot in self.simulation.robots:
                    if robot.carrying_items:
                        # Teleport to drop point
                        self.simulation.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                        robot.x, robot.y = drop_x, drop_y
                        self.simulation.grid.set_cell(drop_x, drop_y, CellType.ROBOT)
                        
                        # Clear items
                        robot.carrying_items = []
                        robot.current_weight = 0
                        robot.path = []
                        
                        if hasattr(self.simulation, '_on_progress_made'):
                            self.simulation._on_progress_made()
        
        # Get remaining items (not picked)
        remaining_items = [item for item in self.simulation.items if not item.picked]
        carrying_items = sum(len(robot.carrying_items) for robot in self.simulation.robots)
        
        self.simulation.logger.debug(f"Remaining items: {len(remaining_items)}, Being carried: {carrying_items}")
        
        # Publish simulation step event
        publish(EventType.SIMULATION_STEP, {
            'remaining_items': len(remaining_items),
            'carrying_items': carrying_items
        })
        
        # Check for stalls and attempt recovery if needed
        if self.simulation.stall_detector:
            stall_time, remaining_unpicked = self.simulation.stall_detector.check_progress(
                self.simulation.robots, self.simulation.items
            )
            
            # Pass to the stall handler to manage recovery actions
            if stall_time > 0:
                self.simulation.stall_handler.handle_stall(stall_time, remaining_unpicked, remaining_items)
            
            # Check for timeout
            if self.simulation.stall_detector.check_timeout():
                self.handle_timeout()
                return False
        
        # Assign items to robots
        self.simulation.item_assigner.assign_items_to_robots(
            self.simulation.robots, 
            self.simulation.items, 
            self.simulation.grid.drop_point
        )
        
        # Move robots
        steps_taken = self.simulation.movement_controller.move_robots(
            self.simulation.robots, 
            self.simulation._on_progress_made
        )
        
        # Update performance statistics
        if self.simulation.performance_tracker:
            self.simulation.performance_tracker.add_steps(steps_taken)
            
            # ADDED: Update robot states in performance tracker
            self.simulation.performance_tracker.update_robot_states(self.simulation.robots)
        
        # Update obstacle lifecycles
        self._update_obstacles()
        
        if self.simulation.gui:
            # First update robot states to get fresh utilization data
            if self.simulation.performance_tracker:
                self.simulation.performance_tracker.update_robot_states(self.simulation.robots)
            
            # Then update the environment display
            self.simulation.update_environment(
                self.simulation.grid, 
                self.simulation.robots, 
                self.simulation.items
            )
            
            # Update performance stats if available - this now includes fresh utilization data
            if self.simulation.performance_tracker:
                self.simulation.gui.update_performance_stats(
                    self.simulation.performance_tracker.format_statistics()
                )
                
        # Check if simulation is complete
        if self._check_completion(remaining_items):
            self.simulation.simulation_manager.handle_simulation_completed()
            return False
        
        # Schedule next step if using GUI
        if self.simulation.gui:
            self.simulation.gui.schedule_next_step(self.simulation.simulation_step)
        
        return True
    
    def _update_obstacles(self) -> None:
        """Update obstacle lifecycle and handle obstacle knowledge sharing"""
        obstacle_manager = self.simulation.obstacle_manager
        if not obstacle_manager:
            return
            
        # Update obstacle lifecycles
        removed_count = obstacle_manager.update_cycle()
        
        # Share obstacle knowledge between robots occasionally
        robots = self.simulation.robots
        if robots and len(robots) > 1:
            # Share knowledge every ~10 cycles randomly
            import random
            if random.random() < 0.1:
                # Pick a random pair of robots to share knowledge
                if len(robots) >= 2:
                    robot_pair = random.sample(robots, 2)
                    obstacle_manager.share_obstacle_knowledge(robot_pair[0].id, robot_pair[1].id)

    def handle_timeout(self):
        """Handle simulation timeout by showing a dialog and offering reset"""
        self.simulation.running = False
        self.simulation.paused = True
        
        self.simulation.logger.warning("TIMEOUT: Maximum simulation time reached")
        
        # If GUI is available, show timeout dialog
        if self.simulation.gui:
            from tkinter import messagebox
            
            def do_reset():
                """Reset the simulation when the user confirms"""
                self.simulation.reset()
            
            # Schedule dialog to appear in main thread
            self.simulation.gui.root.after(100, lambda: self._show_timeout_dialog(do_reset))

    def _show_timeout_dialog(self, reset_callback):
        """Show timeout dialog with reset option"""
        from tkinter import messagebox
        
        result = messagebox.askretrycancel(
            "Simulation Timed Out",
            "The simulation has stalled and timed out.\n\n"
            "Would you like to reset the simulation and try again?",
            icon="warning"
        )
        
        if result:  # User clicked "Retry"
            reset_callback()
    
    def _check_completion(self, remaining_items) -> bool:
        """
        Check if all items have been collected and delivered
        
        Args:
            remaining_items: List of remaining unpicked items
            
        Returns:
            bool: True if simulation is complete
        """
        # First check if there are any unpicked items
        if remaining_items:
            return False
                
        # Then check if any robot is still carrying items
        robots_carrying = False
        for robot in self.simulation.robots:
            if robot.carrying_items:
                robots_carrying = True
                break
                    
        # If no unpicked items and no robots carrying items, simulation is complete
        if not robots_carrying:
            # Make sure delivered count matches total
            if self.simulation.performance_tracker:
                total_items = len(self.simulation.items)
                self.simulation.performance_tracker.sync_delivered_items_count(total_items, len(remaining_items))
            return True
        
        return False
