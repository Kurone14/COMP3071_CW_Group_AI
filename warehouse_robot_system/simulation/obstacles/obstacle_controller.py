"""
Manages obstacles in the simulation environment.
"""

from core.models.grid import CellType
from core.utils.event_system import publish, EventType


class ObstacleController:
    """Controls obstacles in the simulation environment"""
    
    def __init__(self, simulation):
        """
        Initialize the obstacle controller
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def toggle_obstacle(self, x: int, y: int) -> bool:
        """
        Toggle an obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            
        Returns:
            bool: True if obstacle was toggled successfully
        """
        grid = self.simulation.grid
        
        if not grid.in_bounds(x, y):
            self.simulation.logger.warning(f"Cannot toggle obstacle at ({x},{y}): out of bounds")
            return False
            
        cell_type = grid.get_cell(x, y)
        
        if cell_type == CellType.EMPTY:
            # Add obstacle - even during runtime
            grid.set_cell(x, y, CellType.PERMANENT_OBSTACLE)
            
            # Register with obstacle manager if available
            if self.simulation.obstacle_manager:
                self.simulation.obstacle_manager.add_obstacle(x, y, obstacle_type=CellType.PERMANENT_OBSTACLE)
                
            self.simulation.logger.info(f"Added obstacle at ({x},{y})")
            
            # If simulation is running, recalculate affected robot paths
            if self.simulation.running:
                self._recalculate_affected_robot_paths(x, y)
                
            # Publish obstacle added event
            publish(EventType.OBSTACLE_ADDED, {
                'position': (x, y),
                'type': CellType.PERMANENT_OBSTACLE,
                'grid': grid
            })
            
        elif cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
            # Remove obstacle - even during runtime
            grid.set_cell(x, y, CellType.EMPTY)
            
            # Unregister with obstacle manager if available
            if self.simulation.obstacle_manager:
                self.simulation.obstacle_manager.remove_obstacle(x, y)
                
            self.simulation.logger.info(f"Removed obstacle at ({x},{y})")
            
            # Publish obstacle removed event
            publish(EventType.OBSTACLE_REMOVED, {
                'position': (x, y),
                'grid': grid
            })
            
        else:
            self.simulation.logger.warning(f"Cannot toggle obstacle at ({x},{y}): position contains another entity")
            return False
            
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
            
        return True

    def add_temporary_obstacle(self, x: int, y: int, lifespan: int = 10) -> bool:
        """
        Add a temporary obstacle at the specified position - even during runtime
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
            
        Returns:
            bool: True if obstacle was added successfully
        """
        if not self.simulation.obstacle_manager:
            # Fall back to regular obstacle if no obstacle manager
            return self.toggle_obstacle(x, y)
            
        grid = self.simulation.grid
            
        if not grid.in_bounds(x, y):
            self.simulation.logger.warning(f"Cannot add temporary obstacle at ({x},{y}): out of bounds")
            return False
            
        cell_type = grid.get_cell(x, y)
        if cell_type not in [CellType.EMPTY, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE, CellType.PERMANENT_OBSTACLE]:
            self.simulation.logger.warning(f"Cannot add temporary obstacle at ({x},{y}): position occupied by another entity")
            return False
            
        # Add temporary obstacle with obstacle manager - even during runtime
        result = self.simulation.obstacle_manager.add_temporary_obstacle(x, y, lifespan)
        
        if result:
            self.simulation.logger.info(f"Added temporary obstacle at ({x},{y}) with lifespan {lifespan}")
            
            # If simulation is running, recalculate affected robot paths
            if self.simulation.running:
                self._recalculate_affected_robot_paths(x, y)
            
            # Publish obstacle added event
            publish(EventType.OBSTACLE_ADDED, {
                'position': (x, y),
                'type': CellType.TEMPORARY_OBSTACLE,
                'lifespan': lifespan,
                'grid': grid
            })
            
            # Update GUI if connected
            if self.simulation.gui:
                self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return result

    def add_semi_permanent_obstacle(self, x: int, y: int, lifespan: int = 30) -> bool:
        """
        Add a semi-permanent obstacle at the specified position - even during runtime
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
            
        Returns:
            bool: True if obstacle was added successfully
        """
        if not self.simulation.obstacle_manager:
            # Fall back to regular obstacle if no obstacle manager
            return self.toggle_obstacle(x, y)
            
        grid = self.simulation.grid
            
        if not grid.in_bounds(x, y):
            self.simulation.logger.warning(f"Cannot add semi-permanent obstacle at ({x},{y}): out of bounds")
            return False
            
        cell_type = grid.get_cell(x, y)
        if cell_type not in [CellType.EMPTY, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE, CellType.PERMANENT_OBSTACLE]:
            self.simulation.logger.warning(f"Cannot add semi-permanent obstacle at ({x},{y}): position occupied by another entity")
            return False
            
        # Add semi-permanent obstacle with obstacle manager - even during runtime
        result = self.simulation.obstacle_manager.add_semi_permanent_obstacle(x, y, lifespan)
        
        if result:
            self.simulation.logger.info(f"Added semi-permanent obstacle at ({x},{y}) with lifespan {lifespan}")
            
            # If simulation is running, recalculate affected robot paths
            if self.simulation.running:
                self._recalculate_affected_robot_paths(x, y)
            
            # Publish obstacle added event
            publish(EventType.OBSTACLE_ADDED, {
                'position': (x, y),
                'type': CellType.SEMI_PERMANENT_OBSTACLE,
                'lifespan': lifespan,
                'grid': grid
            })
            
            # Update GUI if connected
            if self.simulation.gui:
                self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return result
    
    def add_roadblock(self, x: int, y: int) -> bool:
        """
        Add a roadblock during simulation
        
        Args:
            x, y: Roadblock coordinates
            
        Returns:
            bool: True if roadblock was added successfully
        """
        # If obstacle manager exists, add a temporary obstacle
        if self.simulation.obstacle_manager:
            return self.add_temporary_obstacle(x, y, lifespan=15)
        
        grid = self.simulation.grid
        
        if not grid.in_bounds(x, y):
            self.simulation.logger.warning(f"Cannot add roadblock at ({x},{y}): out of bounds")
            return False
        
        cell_type = grid.get_cell(x, y)
        if cell_type != CellType.EMPTY:
            self.simulation.logger.warning(f"Cannot add roadblock at ({x},{y}): position is occupied")
            return False
        
        grid.set_cell(x, y, CellType.PERMANENT_OBSTACLE)
        self.simulation.logger.info(f"Added roadblock at ({x},{y})")
        
        # Recalculate paths for affected robots
        self._recalculate_affected_robot_paths(x, y)
        
        # Publish obstacle added event
        publish(EventType.OBSTACLE_ADDED, {
            'position': (x, y),
            'type': CellType.PERMANENT_OBSTACLE,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True
    
    def _recalculate_affected_robot_paths(self, block_x: int, block_y: int) -> None:
        """
        Recalculate paths for robots that are affected by a new obstacle
        
        Args:
            block_x, block_y: Obstacle coordinates
        """
        for robot in self.simulation.robots:
            if not robot.path:
                continue
            
            # Check if the new obstacle is on the robot's path
            path_coords = [(py, px) for py, px in robot.path]
            block_pos = (block_y, block_x)
            
            if block_pos in path_coords:
                self.simulation.logger.info(f"Robot {robot.id}'s path is blocked by new obstacle. Recalculating path.")
                
                if robot.carrying_items:
                    # Robot carrying items needs path to drop point
                    new_path = self.simulation.path_finder.find_path(
                        (robot.y, robot.x), 
                        (self.simulation.grid.drop_point[1], self.simulation.grid.drop_point[0]), 
                        self.simulation.robots,
                        robot.id,
                        robot.current_weight
                    )
                elif robot.target_items:
                    # Robot targeting items needs path to first item
                    first_item = robot.target_items[0]
                    new_path = self.simulation.path_finder.find_path(
                        (robot.y, robot.x), 
                        (first_item.y, first_item.x), 
                        self.simulation.robots,
                        robot.id
                    )
                else:
                    new_path = []
                
                if new_path:
                    robot.path = new_path
                    self.simulation.logger.info(f"New path found for robot {robot.id}.")
                else:
                    self.simulation.logger.warning(f"Robot {robot.id} can't find new path. Will retry next cycle.")
                    robot.path = []  # Clear path and retry next cycle