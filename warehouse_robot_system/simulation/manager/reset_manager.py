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
        """Reset the simulation while preserving environment"""
        self.simulation.running = False
        self.simulation.paused = False
        
        # Stop performance tracking
        if self.simulation.performance_tracker:
            self.simulation.performance_tracker.stop()
            self.simulation.performance_tracker.reset()
        
        # Reset stall detector
        if self.simulation.stall_detector:
            self.simulation.stall_detector.reset()
        
        # Reset grid (keeping walls and drop point)
        self._reset_grid()
        
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
    
    def _reset_grid(self) -> None:
        """Reset grid while preserving walls and drop point"""
        # Create a new grid with only walls and drop point
        preserved_grid = Grid(self.simulation.grid.width, self.simulation.grid.height)
        
        for y in range(self.simulation.grid.height):
            for x in range(self.simulation.grid.width):
                cell_type = self.simulation.grid.get_cell(x, y)
                # Preserve permanent obstacles and drop point
                if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.DROP_POINT]:
                    preserved_grid.set_cell(x, y, cell_type)
        
        # Set drop point
        if self.simulation.grid.drop_point:
            preserved_grid.drop_point = self.simulation.grid.drop_point
        
        # Update all component references to the grid
        self.simulation.grid = preserved_grid
        
        if self.simulation.path_finder:
            self.simulation.path_finder.grid = preserved_grid
        if self.simulation.item_assigner:
            self.simulation.item_assigner.grid = preserved_grid
        if self.simulation.movement_controller:
            self.simulation.movement_controller.grid = preserved_grid
        if self.simulation.stall_detector:
            self.simulation.stall_detector.grid = preserved_grid
        if self.simulation.obstacle_manager:
            self.simulation.obstacle_manager.grid = preserved_grid
    
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