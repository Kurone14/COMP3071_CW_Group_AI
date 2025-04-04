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
        self.adjacent_delivery_counts: Dict[int, int] = {}  # Track adjacent delivery attempts
    
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
        
        # Check for robots that are stuck trying to reach items
        self._check_stuck_item_paths(robots)
        
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
                    
                    # Check if robot is near drop point but has no path
                    self._check_adjacent_to_drop_point(robot, progress_callback)
                elif robot.target_items:
                    # Increase stuck time for robots targeting items but with no path
                    self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            if robot.id in robots_to_skip:
                self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            # Robot is not stuck, reset stuck time
            self.robot_stuck_time[robot.id] = 0
            
            # Get next position
            next_y, next_x = robot.path[0]
            
            # Check if next position is an obstacle that hasn't expired
            cell_type = self.grid.get_cell(next_x, next_y)
            if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                # Do not move through obstacles, even temporary ones
                # Increase stuck time
                self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                
                # If obstacle is temporary and almost expired, consider waiting
                if self.obstacle_manager and cell_type == CellType.TEMPORARY_OBSTACLE:
                    lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(next_x, next_y)
                    if lifespan > 0 and lifespan <= 5:
                        # Start waiting for obstacle to clear
                        self.robot_waiting[robot.id] = {
                            'x': next_x,
                            'y': next_y,
                            'current': lifespan,
                            'total': lifespan
                        }
                        print(f"Robot {robot.id} waiting for temporary obstacle at ({next_x}, {next_y}) to clear in {lifespan} cycles")
                continue
            
            # Move the robot
            old_x, old_y = robot.x, robot.y
            self.grid.set_cell(old_x, old_y, CellType.EMPTY)
            
            robot.path.pop(0)
            robot.x, robot.y = next_x, next_y
            robot.steps += 1
            total_steps_taken += 1
            
            self.grid.set_cell(next_x, next_y, CellType.ROBOT)
            
            # Register robot successfully navigating to this position
            if self.obstacle_manager:
                self.obstacle_manager.register_robot_interaction(robot.id, next_x, next_y, True)
            
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
        if not robot.carrying_items:
            return

        # Get drop point coordinates
        drop_x, drop_y = self.grid.drop_point
        
        # Check exact match with drop point
        if (robot.x, robot.y) == (drop_x, drop_y):
            print(f"Robot {robot.id} successfully delivered {len(robot.carrying_items)} items!")
            robot.carrying_items = []
            robot.current_weight = 0
            robot.path = []
            
            # Reset adjacent delivery counter
            if robot.id in self.adjacent_delivery_counts:
                del self.adjacent_delivery_counts[robot.id]
            
            if progress_callback:
                progress_callback()
    
    def _check_adjacent_to_drop_point(self, robot: Any, progress_callback: Optional[Callable]) -> None:
        """Check if robot is adjacent to drop point but has no path"""
        if not robot.carrying_items:
            return
            
        drop_x, drop_y = self.grid.drop_point
        
        # Check if robot is adjacent to drop point (including diagonals)
        if abs(robot.x - drop_x) <= 1 and abs(robot.y - drop_y) <= 1:
            # Increment adjacent delivery counter
            self.adjacent_delivery_counts[robot.id] = self.adjacent_delivery_counts.get(robot.id, 0) + 1
            
            # After 3 attempts, force delivery
            if self.adjacent_delivery_counts[robot.id] >= 3:
                print(f"Robot {robot.id} adjacent to drop point ({drop_x}, {drop_y}) - force delivering after {self.adjacent_delivery_counts[robot.id]} attempts")
                robot.carrying_items = []
                robot.current_weight = 0
                
                # Reset counter
                del self.adjacent_delivery_counts[robot.id]
                
                if progress_callback:
                    progress_callback()
            else:
                print(f"Robot {robot.id} adjacent to drop point - attempt #{self.adjacent_delivery_counts[robot.id]}")
    
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
                
                # Calculate direction toward drop point
                dx = drop_x - robot.x
                dy = drop_y - robot.y
                
                # Normalize direction
                dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
                dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
                
                # Try moving in priority order:
                # 1. Directly toward drop point
                # 2. Horizontally toward drop point
                # 3. Vertically toward drop point
                # 4. In any cardinal direction
                directions_to_try = [
                    (dx, dy),      # Toward drop point (can be diagonal)
                    (dx, 0),       # Horizontal toward drop point
                    (0, dy),       # Vertical toward drop point
                    (-dx, 0),      # Horizontal away from drop point
                    (0, -dy),      # Vertical away from drop point
                    (1, 0), (-1, 0), (0, 1), (0, -1)  # All cardinal directions
                ]
                
                moved = False
                for try_dx, try_dy in directions_to_try:
                    new_x, new_y = robot.x + try_dx, robot.y + try_dy
                    
                    if self.grid.in_bounds(new_x, new_y):
                        cell_type = self.grid.get_cell(new_x, new_y)
                        # Don't move into permanent obstacles or other robots
                        if cell_type not in [CellType.PERMANENT_OBSTACLE, CellType.ROBOT]:
                            print(f"Emergency move: Robot {robot.id} moving to ({new_x}, {new_y})")
                            
                            # If there's a temporary obstacle, remove it
                            if cell_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                                print(f"Removing obstacle at ({new_x}, {new_y}) to allow robot movement")
                                if self.obstacle_manager:
                                    self.obstacle_manager.remove_obstacle(new_x, new_y)
                            
                            # Update grid and robot position
                            self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                            robot.x, robot.y = new_x, new_y
                            self.grid.set_cell(new_x, new_y, CellType.ROBOT)
                            robot.steps += 1
                            self.robot_stuck_time[robot.id] = 0
                            moved = True
                            break
                
                # If close to drop point, force delivery
                if not moved:
                    if abs(robot.x - drop_x) <= 2 and abs(robot.y - drop_y) <= 2:
                        print(f"EMERGENCY: Robot {robot.id} close to drop point - force delivering items")
                        robot.carrying_items = []
                        robot.current_weight = 0
                        self.robot_stuck_time[robot.id] = 0
                        moved = True
                
                # Last resort: teleport to drop point
                if not moved and self.robot_stuck_time[robot.id] > 20:
                    print(f"CRITICAL: Robot {robot.id} cannot move - teleporting to drop point")
                    self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                    robot.x, robot.y = drop_x, drop_y
                    self.grid.set_cell(drop_x, drop_y, CellType.ROBOT)
                    robot.carrying_items = []
                    robot.current_weight = 0
                    self.robot_stuck_time[robot.id] = 0

    def _check_stuck_item_paths(self, robots: List[Any]) -> None:
        """
        Check for robots that are stuck trying to reach items
        and apply interventions to help them
        
        Args:
            robots: List of all robots
        """
        for robot in robots:
            # Only check robots that are trying to reach items
            if not robot.target_items or robot.carrying_items:
                continue
                
            # Check if robot has been stuck for a while
            if robot.id in self.robot_stuck_time and self.robot_stuck_time[robot.id] >= 10:
                target_item = robot.target_items[0]
                print(f"Robot {robot.id} stuck trying to reach item #{target_item.id} for {self.robot_stuck_time[robot.id]} cycles")
                
                # Calculate distance to target item
                distance = abs(robot.x - target_item.x) + abs(robot.y - target_item.y)
                
                # If robot is close to the item but can't reach it
                if distance <= 3:
                    # Try to find a new path with a more aggressive approach
                    new_path = self.path_finder.find_path(
                        (robot.y, robot.x),
                        (target_item.y, target_item.x),
                        [],  # Don't avoid other robots for this emergency path
                        robot.id
                    )
                    
                    if new_path:
                        print(f"Found new emergency path for robot {robot.id} to item #{target_item.id}")
                        robot.path = new_path
                        self.robot_stuck_time[robot.id] = 0
                        continue
                    
                # If still stuck after 15 cycles, check if there are obstacles blocking the path
                if self.robot_stuck_time[robot.id] >= 15:
                    print(f"CRITICAL: Robot {robot.id} stuck for {self.robot_stuck_time[robot.id]} cycles - checking for blocking obstacles")
                    
                    # Look for potential blocking obstacles in a path between robot and item
                    blocking_obstacles = self._find_blocking_obstacles(robot, target_item)
                    
                    if blocking_obstacles:
                        # Remove one obstacle (the closest one)
                        obstacle_x, obstacle_y = blocking_obstacles[0]
                        print(f"Removing blocking obstacle at ({obstacle_x}, {obstacle_y}) to help robot {robot.id}")
                        
                        if self.obstacle_manager:
                            self.obstacle_manager.remove_obstacle(obstacle_x, obstacle_y)
                        else:
                            self.grid.set_cell(obstacle_x, obstacle_y, 0)
                        
                        # Try finding a path again
                        robot.path = self.path_finder.find_path(
                            (robot.y, robot.x),
                            (target_item.y, target_item.x),
                            [],
                            robot.id
                        )
                        
                        if robot.path:
                            print(f"Found path for robot {robot.id} after removing obstacle")
                            self.robot_stuck_time[robot.id] = 0
                        else:
                            print(f"Robot {robot.id} still can't find path after removing obstacle")
                
                # After 20 cycles, resort to teleportation
                if self.robot_stuck_time[robot.id] >= 20:
                    print(f"TELEPORT: Moving robot {robot.id} closer to item #{target_item.id}")
                    
                    # Update grid and robot position
                    self.grid.set_cell(robot.x, robot.y, 0)
                    
                    # Find an adjacent position to the item
                    teleport_x, teleport_y = target_item.x, target_item.y
                    directions = [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
                    
                    for dx, dy in directions:
                        test_x, test_y = target_item.x + dx, target_item.y + dy
                        if self.grid.in_bounds(test_x, test_y) and self.grid.is_cell_empty(test_x, test_y):
                            teleport_x, teleport_y = test_x, test_y
                            break
                    
                    robot.x, robot.y = teleport_x, teleport_y
                    from core.models.grid import CellType
                    self.grid.set_cell(teleport_x, teleport_y, CellType.ROBOT)
                    robot.path = []
                    self.robot_stuck_time[robot.id] = 0
    
    def _find_blocking_obstacles(self, robot: Any, item: Any) -> List[Tuple[int, int]]:
        """
        Find obstacles that might be blocking the path between robot and item
        
        Args:
            robot: The robot trying to reach an item
            item: The target item
            
        Returns:
            List of (x, y) coordinates of potential blocking obstacles
        """
        from core.models.grid import CellType
        
        # Define a bounding box between robot and item with some padding
        min_x = max(0, min(robot.x, item.x) - 1)
        max_x = min(self.grid.width - 1, max(robot.x, item.x) + 1)
        min_y = max(0, min(robot.y, item.y) - 1)
        max_y = min(self.grid.height - 1, max(robot.y, item.y) + 1)
        
        # Find obstacles within the bounding box
        obstacles = []
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                cell_type = self.grid.get_cell(x, y)
                if cell_type in [CellType.PERMANENT_OBSTACLE, 
                               CellType.TEMPORARY_OBSTACLE, 
                               CellType.SEMI_PERMANENT_OBSTACLE]:
                    # Calculate distance to both robot and item
                    dist_to_robot = abs(x - robot.x) + abs(y - robot.y)
                    dist_to_item = abs(x - item.x) + abs(y - item.y)
                    
                    # If obstacle is between robot and item
                    if dist_to_robot + dist_to_item <= abs(robot.x - item.x) + abs(robot.y - item.y) + 2:
                        obstacles.append((x, y))
        
        # Sort by distance to robot (closest first)
        obstacles.sort(key=lambda o: abs(o[0] - robot.x) + abs(o[1] - robot.y))
        
        return obstacles