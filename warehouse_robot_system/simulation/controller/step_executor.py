"""
Executes simulation steps and manages the main simulation loop.
"""

from core.utils.event_system import publish, EventType


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
                self.simulation.logger.warning("TIMEOUT: Maximum simulation time reached")
                self.simulation.simulation_manager.handle_simulation_completed()
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
        
        # Update obstacle lifecycles
        self._update_obstacles()
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.update_environment(
                self.simulation.grid, 
                self.simulation.robots, 
                self.simulation.items
            )
            
            # Update performance stats if available
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
    
    def _check_completion(self, remaining_items) -> bool:
        """
        Check if all items have been collected and delivered
        
        Args:
            remaining_items: List of remaining unpicked items
            
        Returns:
            bool: True if simulation is complete
        """
        if remaining_items:
            return False
            
        # Check if any robot is still carrying items
        for robot in self.simulation.robots:
            if robot.carrying_items:
                return False
                
        return True