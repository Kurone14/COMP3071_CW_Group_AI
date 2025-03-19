from typing import List, Dict, Tuple, Set, Optional, Any, Callable
from .collision_resolver import CollisionResolver
from core.models.grid import Grid, CellType


class MovementController:
    """
    Controls robot movement, pathfinding, and interactions with items and obstacles.
    Handles collision avoidance and waiting for temporary obstacles.
    """
    
    def __init__(self, grid: Grid, path_finder, obstacle_manager=None):
        """
        Initialize the movement controller
        
        Args:
            grid: The environment grid
            path_finder: PathFinder instance for calculating paths
            obstacle_manager: Optional obstacle manager for temporary obstacles
        """
        self.grid = grid
        self.path_finder = path_finder
        self.obstacle_manager = obstacle_manager
        self.collision_resolver = CollisionResolver()
        
        self.robot_stuck_time: Dict[int, int] = {}  # Track how long robots have been stuck
        self.robot_waiting: Dict[int, Dict] = {}    # Track robots waiting for temporary obstacles
    
    def handle_temporary_obstacles(self, robot: Any, goal: Tuple[int, int]) -> bool:
        """
        Handle interactions with temporary obstacles
        
        Args:
            robot: The robot object
            goal: The target position (y, x)
            
        Returns:
            bool: True if robot should wait, False if it should proceed normally
        """
        if not self.obstacle_manager:
            return False
            
        # Check if robot is already waiting
        if robot.id in self.robot_waiting:
            wait_info = self.robot_waiting[robot.id]
            wait_info['current'] -= 1
            
            if wait_info['current'] <= 0:
                # Waiting time is over
                print(f"Robot {robot.id} finished waiting for temporary obstacle at ({wait_info['x']}, {wait_info['y']})")
                del self.robot_waiting[robot.id]
                return False
            else:
                # Continue waiting
                print(f"Robot {robot.id} waiting for temporary obstacle: {wait_info['current']}/{wait_info['total']} cycles remaining")
                return True
        
        # Not waiting yet - check if there's a temporary obstacle blocking the path
        if not robot.path:
            return False
        
        next_step = robot.path[0]
        next_y, next_x = next_step
        
        # If the next step is a temporary obstacle
        if self.obstacle_manager.is_obstacle_temporary(next_x, next_y):
            lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(next_x, next_y)
            
            # If it will disappear soon, consider waiting
            if lifespan > 0 and lifespan <= 5:
                # Check if waiting is more efficient than finding a new path
                wait_time = self.path_finder.wait_or_navigate(robot, goal, [], (next_x, next_y))
                
                if wait_time > 0:
                    print(f"Robot {robot.id} decided to wait {wait_time} cycles for temporary obstacle at ({next_x}, {next_y})")
                    self.robot_waiting[robot.id] = {
                        'x': next_x,
                        'y': next_y,
                        'current': wait_time,
                        'total': wait_time
                    }
                    return True
        
        return False
    
    def move_robots(self, robots: List[Any], progress_callback: Optional[Callable] = None) -> int:
        """
        Move robots and handle interactions with items and drop points
        
        Args:
            robots: List of robots to move
            progress_callback: Optional callback function when progress is made
            
        Returns:
            int: Total number of steps taken
        """
        next_positions: Dict[int, Tuple[int, int]] = {}
        total_steps_taken = 0
        
        # Collect all proposed next positions
        for robot in robots:
            if robot.path:
                # Skip robots that are waiting for temporary obstacles
                if self.obstacle_manager and robot.id in self.robot_waiting:
                    continue
                    
                next_y, next_x = robot.path[0]
                next_positions[robot.id] = (next_x, next_y)
        
        # Resolve collisions
        robots_to_skip = self.collision_resolver.resolve_collisions(
            robots, next_positions, self.robot_stuck_time
        )
        
        # Process each robot's movement
        for robot in robots:
            # Check if robot should be waiting for a temporary obstacle
            if robot.target_items and not robot.carrying_items:
                goal = (robot.target_items[0].y, robot.target_items[0].x)
                if self.handle_temporary_obstacles(robot, goal):
                    continue
            elif robot.carrying_items:
                goal = (self.grid.drop_point[1], self.grid.drop_point[0])
                if self.handle_temporary_obstacles(robot, goal):
                    continue
            
            if not robot.path:
                # Increase stuck time for robots carrying items but with no path
                if robot.carrying_items:
                    self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            if robot.id in robots_to_skip:
                self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            # Robot is not stuck, reset stuck time
            self.robot_stuck_time[robot.id] = 0
            
            # Move the robot
            old_x, old_y = robot.x, robot.y
            self.grid.set_cell(old_x, old_y, CellType.EMPTY)
            
            next_y, next_x = robot.path.pop(0)
            
            # Register robot successfully navigating to this position
            if self.obstacle_manager:
                cell_type = self.grid.get_cell(next_x, next_y)
                if cell_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                    self.obstacle_manager.register_robot_interaction(robot.id, next_x, next_y, True)
            
            robot.x, robot.y = next_x, next_y
            robot.steps += 1
            total_steps_taken += 1
            
            self.grid.set_cell(next_x, next_y, CellType.ROBOT)
            
            # Check if robot has reached an item
            self._check_item_pickup(robot, progress_callback)
                
            # Check if robot has reached drop point
            self._check_drop_point_delivery(robot, progress_callback)
        
        # Handle robots that have been stuck for too long
        self._handle_stuck_robots(robots)
        
        return total_steps_taken
    
    def _check_item_pickup(self, robot: Any, progress_callback: Optional[Callable]) -> None:
        """Check if robot has reached its target item and handle pickup"""
        if robot.target_items and not robot.carrying_items:
            target_item = robot.target_items[0]
            if (robot.x, robot.y) == (target_item.x, target_item.y):
                print(f"Robot {robot.id} picking up item #{target_item.id}")
                picked_item = robot.target_items.pop(0)
                robot.carrying_items.append(picked_item)
                picked_item.picked = True
                robot.current_weight = sum(item.weight for item in robot.carrying_items)
                
                self._continue_picking_items(robot)
                
        elif robot.target_items and robot.carrying_items:
            target_item = robot.target_items[0]
            if (robot.x, robot.y) == (target_item.x, target_item.y):
                if robot.current_weight + target_item.weight <= robot.capacity:
                    print(f"Robot {robot.id} picking up additional item #{target_item.id}")
                    picked_item = robot.target_items.pop(0)
                    robot.carrying_items.append(picked_item)
                    picked_item.picked = True
                    robot.current_weight = sum(item.weight for item in robot.carrying_items)
                    
                    self._continue_picking_items(robot)
                else:
                    print(f"Robot {robot.id} at item #{target_item.id} but capacity exceeded")
                    robot.path = self.path_finder.find_path(
                        (robot.y, robot.x), 
                        (self.grid.drop_point[1], self.grid.drop_point[0]), 
                        None,  # Not passing robots to avoid deadlocks
                        robot.id,
                        robot.current_weight
                    )
    
    def _check_drop_point_delivery(self, robot: Any, progress_callback: Optional[Callable]) -> None:
        """Check if robot has reached drop point and handle delivery"""
        if robot.carrying_items and (robot.x, robot.y) == self.grid.drop_point:
            print(f"Robot {robot.id} successfully delivered {len(robot.carrying_items)} items!")
            robot.carrying_items = []
            robot.current_weight = 0
            robot.path = []  
            
            if progress_callback:
                progress_callback()
    
    def _continue_picking_items(self, robot: Any) -> None:
        """Handle continuation of item picking"""
        if robot.target_items:
            next_item = robot.target_items[0]
            if robot.current_weight + next_item.weight <= robot.capacity:
                print(f"Robot {robot.id} heading to next item #{next_item.id}")
                robot.path = self.path_finder.find_path(
                    (robot.y, robot.x), 
                    (next_item.y, next_item.x), 
                    None,  # Not passing robots to avoid deadlocks
                    robot.id
                )
                
                if not robot.path:
                    print(f"WARNING: Robot {robot.id} can't find path to next item. Heading to drop point.")
                    robot.path = self.path_finder.find_path(
                        (robot.y, robot.x), 
                        (self.grid.drop_point[1], self.grid.drop_point[0]), 
                        None,
                        robot.id,
                        robot.current_weight
                    )
            else:
                print(f"Robot {robot.id} at capacity limit. Next item too heavy. Heading to drop point.")
                robot.path = self.path_finder.find_path(
                    (robot.y, robot.x), 
                    (self.grid.drop_point[1], self.grid.drop_point[0]), 
                    None,
                    robot.id,
                    robot.current_weight
                )
        else:
            print(f"Robot {robot.id} heading to drop point with all items")
            robot.path = self.path_finder.find_path(
                (robot.y, robot.x), 
                (self.grid.drop_point[1], self.grid.drop_point[0]), 
                None,
                robot.id,
                robot.current_weight
            )
    
    def _handle_stuck_robots(self, robots: List[Any]) -> None:
        """Handle robots that have been stuck for too long"""
        stuck_threshold = 10  # Cycles before considering a robot stuck
        
        for robot in robots:
            if robot.carrying_items and not robot.path and self.robot_stuck_time.get(robot.id, 0) >= stuck_threshold:
                print(f"CRITICAL: Robot {robot.id} has been stuck carrying items for {self.robot_stuck_time[robot.id]} cycles")
                print(f"Attempting emergency movement toward drop point")
                
                drop_x, drop_y = self.grid.drop_point
                
                dx = drop_x - robot.x
                dy = drop_y - robot.y
                
                dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
                dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
                
                directions_to_try = [
                    (dx, dy),     # Toward drop point
                    (dx, 0),      # Horizontal toward drop point
                    (0, dy),      # Vertical toward drop point
                    (-dx, 0),     # Horizontal away from drop point
                    (0, -dy),     # Vertical away from drop point
                    (1, 0), (-1, 0), (0, 1), (0, -1)  # Cardinal directions
                ]
                
                moved = False
                for try_dx, try_dy in directions_to_try:
                    new_x, new_y = robot.x + try_dx, robot.y + try_dy
                    
                    if self.grid.in_bounds(new_x, new_y):
                        cell_type = self.grid.get_cell(new_x, new_y)
                        if cell_type not in [CellType.PERMANENT_OBSTACLE, CellType.ROBOT]:
                            print(f"Emergency move: Robot {robot.id} moving to ({new_x}, {new_y})")
                            
                            self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                            robot.x, robot.y = new_x, new_y
                            self.grid.set_cell(new_x, new_y, CellType.ROBOT)
                            robot.steps += 1
                            self.robot_stuck_time[robot.id] = 0
                            moved = True
                            break
                
                if not moved:
                    print(f"CRITICAL: Robot {robot.id} cannot move in any direction!")
                    if self.robot_stuck_time[robot.id] > 30:  # Really stuck
                        print(f"EMERGENCY: Robot {robot.id} dropping items to allow simulation to continue")
                        for item in robot.carrying_items:
                            item.picked = False
                            item.assigned = False
                        robot.carrying_items = []
                        robot.current_weight = 0