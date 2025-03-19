"""
Manages robot creation, editing, and deletion.
"""

import random
from typing import Optional, Tuple

from core.models.grid import CellType
from core.models.robot import Robot
from core.utils.event_system import publish, EventType


class RobotManager:
    """Manages robot entities in the simulation"""
    
    def __init__(self, simulation):
        """
        Initialize the robot manager
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def create_robot(self, robot_id: int) -> Robot:
        """
        Create a robot with a valid position
        
        Args:
            robot_id: ID to assign to the robot
            
        Returns:
            Robot: The created robot
        """
        # Try to place robot along the bottom of the grid
        grid = self.simulation.grid
        robot_x = 2 + robot_id * 2
        robot_y = grid.height - 2
        
        # Adjust if off grid
        if robot_x >= grid.width:
            robot_x = robot_x % (grid.width - 4) + 2
            robot_y -= 1
        
        # Find an empty cell
        attempts = 0
        while not grid.is_cell_empty(robot_x, robot_y) and attempts < 100:
            robot_x = (robot_x + 1) % (grid.width - 2) + 1
            attempts += 1
        
        if attempts >= 100:
            self.simulation.logger.warning(f"Could not find empty space for robot {robot_id}")
            # Last resort, find any empty cell
            for y in range(grid.height):
                for x in range(grid.width):
                    if grid.is_cell_empty(x, y):
                        robot_x, robot_y = x, y
                        break
        
        # Create robot with some capacity variation
        capacity = 10 + (robot_id * 2) % 6
        robot = Robot(robot_id, robot_x, robot_y, capacity)
        
        # Register robot in grid
        grid.set_cell(robot_x, robot_y, CellType.ROBOT)
        self.simulation.robots.append(robot)
        
        # Remember start position for reset
        self.simulation.robot_start_positions[robot_id] = (robot_x, robot_y)
        
        self.simulation.logger.info(f"Created robot {robot_id} at ({robot_x}, {robot_y}) with capacity {capacity}")
        
        # Publish robot added event
        publish(EventType.ROBOT_ADDED, {
            'robot': robot,
            'grid': grid
        })
        
        return robot
    
    def add_robot(self, x: int, y: int, capacity: Optional[int] = None) -> bool:
        """
        Add a new robot at specified position
        
        Args:
            x, y: Position coordinates
            capacity: Optional capacity (default: random)
            
        Returns:
            bool: True if robot was added successfully
        """
        grid = self.simulation.grid
        
        if not grid.is_cell_empty(x, y):
            self.simulation.logger.warning(f"Cannot place robot at ({x}, {y}): position not empty")
            return False
        
        # Generate robot ID
        robot_id = max(robot.id for robot in self.simulation.robots) + 1 if self.simulation.robots else 0
        
        # Set capacity
        if capacity is None:
            capacity = random.randint(10, 15)
        
        # Create robot
        robot = Robot(robot_id, x, y, capacity)
        self.simulation.robots.append(robot)
        
        # Register in grid
        grid.set_cell(x, y, CellType.ROBOT)
        
        # Store start position for reset
        self.simulation.robot_start_positions[robot_id] = (x, y)
        
        self.simulation.logger.info(f"Added robot {robot_id} at ({x}, {y}) with capacity {capacity}kg")
        
        # Publish robot added event
        publish(EventType.ROBOT_ADDED, {
            'robot': robot,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True
    
    def edit_robot(self, robot_id: int, new_x: int, new_y: int, new_capacity: int) -> bool:
        """
        Edit an existing robot
        
        Args:
            robot_id: ID of the robot to edit
            new_x, new_y: New position coordinates
            new_capacity: New capacity
            
        Returns:
            bool: True if robot was edited successfully
        """
        grid = self.simulation.grid
        
        # Find robot by ID
        robot = next((r for r in self.simulation.robots if r.id == robot_id), None)
        if not robot:
            self.simulation.logger.warning(f"Robot {robot_id} not found")
            return False
        
        # Check if robot is active
        if robot.carrying_items or robot.path:
            self.simulation.logger.warning(f"Cannot edit robot {robot_id} while it is active")
            return False
        
        # Update position if changed
        if (new_x, new_y) != (robot.x, robot.y):
            if not grid.is_cell_empty(new_x, new_y):
                self.simulation.logger.warning(f"Cannot move robot to ({new_x}, {new_y}): position not empty")
                return False
            
            # Update grid
            grid.set_cell(robot.x, robot.y, CellType.EMPTY)
            
            robot.x, robot.y = new_x, new_y
            
            grid.set_cell(new_x, new_y, CellType.ROBOT)
            
            # Update start position for reset
            self.simulation.robot_start_positions[robot_id] = (new_x, new_y)
        
        # Update capacity if changed
        if new_capacity != robot.capacity:
            robot.capacity = new_capacity
        
        self.simulation.logger.info(f"Updated robot {robot_id} to position ({new_x}, {new_y}) with capacity {new_capacity}kg")
        
        # Publish robot updated event
        publish(EventType.ROBOT_ADDED, {  # Reusing ROBOT_ADDED for updates
            'robot': robot,
            'grid': grid,
            'is_update': True
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True
    
    def delete_robot(self, robot_id: int) -> bool:
        """
        Delete an existing robot
        
        Args:
            robot_id: ID of the robot to delete
            
        Returns:
            bool: True if robot was deleted successfully
        """
        grid = self.simulation.grid
        
        # Find robot by ID and index
        robot_index = None
        for i, robot in enumerate(self.simulation.robots):
            if robot.id == robot_id:
                robot_index = i
                break
                
        if robot_index is None:
            self.simulation.logger.warning(f"Robot {robot_id} not found")
            return False
        
        robot = self.simulation.robots[robot_index]
        
        # Check if robot is carrying items
        if robot.carrying_items:
            self.simulation.logger.warning(f"Cannot delete robot {robot_id} while it is carrying items")
            return False
        
        # Update grid
        grid.set_cell(robot.x, robot.y, CellType.EMPTY)
        
        # Remove robot from list
        self.simulation.robots.pop(robot_index)
        
        # Remove from start positions
        if robot_id in self.simulation.robot_start_positions:
            del self.simulation.robot_start_positions[robot_id]
        
        self.simulation.logger.info(f"Deleted robot {robot_id}")
        
        # Publish robot deleted event
        publish(EventType.ROBOT_DELETED, {
            'robot_id': robot_id,
            'grid': grid
        })
        
        # Update GUI if connected
        if self.simulation.gui:
            self.simulation.gui.update_environment(grid, self.simulation.robots, self.simulation.items)
        
        return True