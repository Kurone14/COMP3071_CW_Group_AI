"""
Handles stall detection and recovery in the simulation.
"""

from typing import List, Tuple, Dict, Set
import random

from core.models.item import Item
from core.models.robot import Robot
from core.models.grid import CellType


class StallHandler:
    """Handles stall detection and recovery in the simulation"""
    
    def __init__(self, simulation):
        """
        Initialize the stall handler
        
        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
    
    def handle_stall(self, stall_time: int, remaining_unpicked: List[Item], remaining_items: List[Item]) -> bool:
        """
        Apply increasingly aggressive recovery measures based on stall time
        
        Args:
            stall_time: How long the simulation has been stalled
            remaining_unpicked: Items that haven't been picked up yet
            remaining_items: All items that aren't marked as picked
            
        Returns:
            bool: True if the stall was handled, False otherwise
        """
        stall_detector = self.simulation.stall_detector
        if not stall_detector:
            return False
            
        # Apply increasingly aggressive recovery measures based on stall time
        if stall_time > 15:
            stall_detector.level1_recovery(self.simulation.robots, self.simulation.items, stall_time)
        
        if stall_time > 20:
            stall_detector.level2_recovery(self.simulation.robots, self.simulation.items, stall_time)
        
        if stall_time > 35:
            stall_detector.level3_recovery(self.simulation.robots, self.simulation.items, stall_time, remaining_unpicked)
        
        if stall_time > 50:
            force_complete = stall_detector.level4_recovery(self.simulation.robots, self.simulation.items, stall_time, remaining_unpicked)
            if force_complete:
                self.simulation.simulation_manager.handle_simulation_completed()
                return True
                
        return False
    
    def detect_deadlocks(self) -> bool:
        """
        Detect potential deadlocks between robots
        
        Returns:
            bool: True if a deadlock was detected
        """
        # Check for robots that are stuck and not making progress
        robots = self.simulation.robots
        stuck_robots = []
        
        for robot in robots:
            # Consider a robot stuck if it has a path but hasn't moved
            # for several cycles, or it should be carrying items to
            # the drop point but isn't moving
            if (robot.path and hasattr(robot, 'stuck_count') and 
                getattr(robot, 'stuck_count', 0) > 5):
                stuck_robots.append(robot)
            elif robot.carrying_items and not robot.path:
                stuck_robots.append(robot)
        
        if len(stuck_robots) >= 2:
            self.simulation.logger.warning(f"Potential deadlock detected between {len(stuck_robots)} robots")
            return True
        
        return False
    
    def resolve_deadlock(self, stuck_robots: List[Robot]) -> bool:
        """
        Attempt to resolve a deadlock between robots
        
        Args:
            stuck_robots: List of robots involved in the deadlock
            
        Returns:
            bool: True if the deadlock was resolved
        """
        if not stuck_robots:
            return False
        
        grid = self.simulation.grid
        
        # Pick a random robot to move out of the way
        robot = random.choice(stuck_robots)
        
        # Find a nearby empty cell to move to
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)
        
        for dx, dy in directions:
            new_x, new_y = robot.x + dx, robot.y + dy
            
            if grid.in_bounds(new_x, new_y) and grid.is_cell_empty(new_x, new_y):
                # Clear the robot's current cell
                grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                
                # Move the robot
                robot.x, robot.y = new_x, new_y
                
                # Update the grid
                grid.set_cell(new_x, new_y, CellType.ROBOT)
                
                # Clear the robot's path so it will be recalculated
                robot.path = []
                
                self.simulation.logger.info(f"Moved robot {robot.id} to ({new_x}, {new_y}) to resolve deadlock")
                return True
        
        return False
    
    def check_unreachable_items(self) -> List[Item]:
        """
        Check for items that might be unreachable by any robot
        
        Returns:
            List[Item]: List of potentially unreachable items
        """
        unreachable_items = []
        path_finder = self.simulation.path_finder
        
        for item in self.simulation.items:
            if item.picked or item.assigned:
                continue
                
            reachable = False
            
            # Check if any robot can reach this item
            for robot in self.simulation.robots:
                if robot.carrying_items:
                    continue
                    
                path = path_finder.find_path(
                    (robot.y, robot.x),
                    (item.y, item.x),
                    self.simulation.robots,
                    robot.id
                )
                
                if path:
                    reachable = True
                    break
            
            if not reachable:
                unreachable_items.append(item)
        
        return unreachable_items
    
    def teleport_robot_to_unreachable_item(self, item: Item) -> bool:
        """
        Teleport a robot to an unreachable item as a last resort
        
        Args:
            item: The unreachable item
            
        Returns:
            bool: True if a robot was teleported
        """
        grid = self.simulation.grid
        
        # Find an available robot (not carrying items)
        available_robot = None
        for robot in self.simulation.robots:
            if not robot.carrying_items:
                available_robot = robot
                break
                
        if not available_robot:
            return False
            
        # Clear the robot's current position
        grid.set_cell(available_robot.x, available_robot.y, CellType.EMPTY)
        
        # Find a position next to the item
        directions = [(0, 0), (0, 1), (1, 0), (0, -1), (-1, 0)]
        
        for dx, dy in directions:
            new_x, new_y = item.x + dx, item.y + dy
            
            if grid.in_bounds(new_x, new_y) and grid.is_cell_empty(new_x, new_y):
                # Teleport the robot
                available_robot.x, available_robot.y = new_x, new_y
                
                # Update the grid
                grid.set_cell(new_x, new_y, CellType.ROBOT)
                
                # Assign the item to the robot
                available_robot.target_items = [item]
                item.assigned = True
                
                self.simulation.logger.info(f"Teleported robot {available_robot.id} to ({new_x}, {new_y}) near unreachable item {item.id}")
                return True
        
        return False
    
    def force_completion(self) -> bool:
        """
        Force simulation completion as a last resort
        
        Returns:
            bool: True if the simulation was force-completed
        """
        # Mark all remaining items as picked
        remaining_items = [item for item in self.simulation.items if not item.picked]
        for item in remaining_items:
            item.picked = True
            
        # Clear all robots' carrying items
        for robot in self.simulation.robots:
            robot.carrying_items = []
            robot.current_weight = 0
            robot.path = []
            
        self.simulation.logger.warning("Force completing simulation due to unresolvable stall")
        return True