"""
Manages resetting the simulation and preserving environment state
"""

from core.utils.event_system import publish, EventType
from core.models.grid import Grid, CellType


class ResetManager:
    """Manages resetting the simulation while preserving environment"""
    
    def __init__(self, simulation):
        """
        Initialize the reset manager
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def reset(self) -> None:
        """Reset the simulation while preserving environment and respawning disappeared obstacles"""
        self.simulation.running = False
        self.simulation.paused = False
        
        # Stop performance tracking
        if self.simulation.performance_tracker:
            self.simulation.performance_tracker.stop()
            self.simulation.performance_tracker.reset()
        
        # Reset stall detector if it exists
        if self.simulation.stall_detector:
            try:
                self.simulation.stall_detector.reset()
            except Exception as e:
                self.simulation.logger.warning(f"Error resetting stall detector: {e}")
        
        # Store original obstacle data before resetting grid
        original_obstacle_data = {}
        if self.simulation.obstacle_manager:
            # Get the original obstacles from obstacle manager
            original_obstacle_data = self.simulation.obstacle_manager.obstacles.copy()
            
            # Also recover recently removed obstacles that should reappear
            recently_removed = set()
            try:
                recently_removed = self.simulation.obstacle_manager.recently_removed
            except AttributeError:
                # If recently_removed attribute doesn't exist, create an empty set
                self.simulation.logger.warning("recently_removed attribute not found in obstacle_manager")
                recently_removed = set()
                
            for pos in recently_removed:
                try:
                    if isinstance(pos, tuple) and len(pos) == 2:
                        x, y = pos
                        pos_key = (x, y)  # Use tuple as key to match how it's stored
                        # Only preserve if it's a temporary or semi-permanent obstacle
                        # We can't know its exact type now, so we'll make it temporary by default
                        if pos_key not in original_obstacle_data:
                            original_obstacle_data[pos_key] = {
                                'type': CellType.TEMPORARY_OBSTACLE,
                                'lifespan': 10,  # Default lifespan
                                'age': 0,
                                'confidence': 0.8
                            }
                except (ValueError, IndexError, TypeError):
                    # Skip invalid positions
                    continue
        
        # Reset grid (keeping walls and drop point)
        self._reset_grid(original_obstacle_data)
        
        # Reset all robots to starting positions
        self._reset_robots()
        
        # Reset all items
        self._reset_items()
        
        self.simulation.logger.info("Simulation reset")
        
        # Publish simulation reset event
        publish(EventType.SIMULATION_RESET, {
            'robots': self.simulation.robots,
            'items': self.simulation.items,
            'grid': self.simulation.grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            # Direct use of the event handler
            if hasattr(self.simulation.gui, 'event_handler'):
                self.simulation.gui.event_handler.on_simulation_reset()
            else:
                # Backward compatibility
                self.simulation.gui.on_simulation_reset()
                
            self.simulation.gui.update_environment(self.simulation.grid, self.simulation.robots, self.simulation.items)
            
            # Update performance stats if available
            if self.simulation.performance_tracker:
                self.simulation.gui.update_performance_stats(self.simulation.performance_tracker.format_statistics())

    def _reset_grid(self, original_obstacle_data=None) -> None:
        """
        Reset grid while preserving walls and drop point, properly handling all obstacle types
        and respawning disappeared obstacles
        
        Args:
            original_obstacle_data: Optional dict of original obstacle data to restore
        """
        # Create a new grid with only walls, drop point, and obstacles
        preserved_grid = Grid(self.simulation.grid.width, self.simulation.grid.height)
        
        # Preserve original obstacles if not provided
        if original_obstacle_data is None and self.simulation.obstacle_manager:
            original_obstacle_data = self.simulation.obstacle_manager.obstacles.copy()
        
        # First, preserve existing obstacles in the grid
        for y in range(self.simulation.grid.height):
            for x in range(self.simulation.grid.width):
                cell_type = self.simulation.grid.get_cell(x, y)
                # Preserve all obstacle types and drop point
                if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, 
                                CellType.SEMI_PERMANENT_OBSTACLE, CellType.DROP_POINT]:
                    preserved_grid.set_cell(x, y, cell_type)
        
        # Then, restore any disappeared obstacles from original data
        if original_obstacle_data:
            for pos_key, obstacle_data in original_obstacle_data.items():
                try:
                    # Handle both string keys "x,y" and tuple keys (x,y)
                    if isinstance(pos_key, str):
                        x, y = map(int, pos_key.split(','))
                    elif isinstance(pos_key, tuple):
                        x, y = pos_key
                    else:
                        continue  # Skip unknown key types
                    
                    # Only restore if position is empty now
                    if preserved_grid.is_cell_empty(x, y):
                        preserved_grid.set_cell(x, y, obstacle_data['type'])
                except (ValueError, IndexError, TypeError):
                    # Skip invalid position keys
                    self.simulation.logger.warning(f"Skipping invalid position key: {pos_key}")
                    continue
        
        # Set drop point
        if self.simulation.grid.drop_point:
            preserved_grid.drop_point = self.simulation.grid.drop_point
        
        # Update all component references to the grid
        self.simulation.grid = preserved_grid
        
        # Reinitialize the obstacle manager with all obstacles
        if self.simulation.obstacle_manager:
            # First, clear existing obstacles and recently removed tracking
            self.simulation.obstacle_manager.obstacles = {}
            self.simulation.obstacle_manager.recently_removed = set()
            
            # Update grid reference
            self.simulation.obstacle_manager.grid = preserved_grid
            
            # Re-register all obstacles from the grid and original data
            for y in range(preserved_grid.height):
                for x in range(preserved_grid.width):
                    cell_type = preserved_grid.get_cell(x, y)
                    
                    if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, 
                                    CellType.SEMI_PERMANENT_OBSTACLE]:
                        # Default values
                        obstacle_type = cell_type
                        lifespan = -1 if cell_type == CellType.PERMANENT_OBSTACLE else (
                            30 if cell_type == CellType.SEMI_PERMANENT_OBSTACLE else 10)
                        confidence = 0.8
                        
                        # Try to find original data for this position
                        pos_str_key = f"{x},{y}"
                        pos_tuple_key = (x, y)
                        
                        old_data = None
                        if original_obstacle_data:
                            if pos_str_key in original_obstacle_data:
                                old_data = original_obstacle_data[pos_str_key]
                            elif pos_tuple_key in original_obstacle_data:
                                old_data = original_obstacle_data[pos_tuple_key]
                        
                        # Use original data if available
                        if old_data:
                            # Use original type if available (more accurate)
                            obstacle_type = old_data.get('type', cell_type)
                            
                            # For temporary obstacles, reset age but preserve original lifespan
                            if obstacle_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                                lifespan = old_data.get('lifespan', lifespan)
                            
                            confidence = old_data.get('confidence', confidence)
                        
                        # Add the obstacle to the manager
                        self.simulation.obstacle_manager.add_obstacle(
                            x, y, obstacle_type, confidence=confidence, lifespan=lifespan
                        )
        
        # Update all component references to the grid
        if self.simulation.path_finder:
            self.simulation.path_finder.grid = preserved_grid
        if self.simulation.item_assigner:
            self.simulation.item_assigner.grid = preserved_grid
        if self.simulation.movement_controller:
            self.simulation.movement_controller.grid = preserved_grid
        if self.simulation.stall_detector:
            self.simulation.stall_detector.grid = preserved_grid
    
    def _reset_robots(self) -> None:
        """Reset all robots to starting positions"""
        for robot in self.simulation.robots:
            # Clear current position
            self.simulation.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
            
            # Reset robot state
            if robot.id in self.simulation.robot_start_positions:
                start_x, start_y = self.simulation.robot_start_positions[robot.id]
                robot.reset(start_x, start_y)
            else:
                robot.reset()
            
            # Set robot in grid at new position
            self.simulation.grid.set_cell(robot.x, robot.y, CellType.ROBOT)
    
    def _reset_items(self) -> None:
        """Reset all items"""
        for item in self.simulation.items:
            # Reset item state
            item.reset()
            
            # Set item in grid
            self.simulation.grid.set_cell(item.x, item.y, CellType.ITEM)