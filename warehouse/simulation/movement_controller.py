from simulation.collision_resolver import CollisionResolver

class MovementController:
    """Controls robot movement, pathfinding, and interactions with items"""
    def __init__(self, grid, width, height, drop_point, path_finder, obstacle_manager=None):
        self.grid = grid
        self.width = width
        self.height = height
        self.drop_point = drop_point
        self.path_finder = path_finder
        self.collision_resolver = CollisionResolver()
        self.obstacle_manager = obstacle_manager
        
        self.robot_stuck_time = {}
        self.last_progress_at = 0
        self.robot_waiting = {}  # Track robots waiting for temporary obstacles
    
    def update_grid(self, grid):
        """Update the grid reference"""
        self.grid = grid

    def handle_temporary_obstacles(self, robot, goal):
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
    
    def move_robots(self, robots, progress_callback=None):
        """Move robots and handle interactions with items and drop points"""
        next_positions = {}
        total_steps_taken = 0
        
        for robot in robots:
            if robot.path:
                # Skip robots that are waiting for temporary obstacles
                if self.obstacle_manager and robot.id in self.robot_waiting:
                    continue
                    
                next_y, next_x = robot.path[0]
                next_positions[robot.id] = (next_x, next_y)
        
        robots_to_skip = self.collision_resolver.resolve_collisions(
            robots, next_positions, self.robot_stuck_time
        )
        
        for robot in robots:
            # Check if robot should be waiting for a temporary obstacle
            if robot.target_items and not robot.carrying_items:
                goal = (robot.target_items[0].y, robot.target_items[0].x)
                if self.handle_temporary_obstacles(robot, goal):
                    continue
            elif robot.carrying_items:
                goal = (self.drop_point[1], self.drop_point[0])
                if self.handle_temporary_obstacles(robot, goal):
                    continue
            
            if not robot.path:
                if robot.carrying_items:
                    self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            if robot.id in robots_to_skip:
                self.robot_stuck_time[robot.id] = self.robot_stuck_time.get(robot.id, 0) + 1
                continue
                    
            self.robot_stuck_time[robot.id] = 0
            
            self.grid[robot.y][robot.x] = 0
            
            next_y, next_x = robot.path.pop(0)
            
            # Register robot successfully navigating to this position
            if self.obstacle_manager and self.grid[next_y][next_x] in [5, 6]:
                self.obstacle_manager.register_robot_interaction(robot.id, next_x, next_y, True)
            
            robot.x, robot.y = next_x, next_y
            robot.steps += 1
            total_steps_taken += 1
            
            self.grid[robot.y][robot.x] = 3
            
            if robot.target_items and not robot.carrying_items:
                target_item = robot.target_items[0]
                if (robot.x, robot.y) == (target_item.x, target_item.y):
                    print(f"Robot {robot.id} picking up item #{target_item.id}")
                    picked_item = robot.target_items.pop(0)
                    robot.carrying_items.append(picked_item)
                    picked_item.picked = True
                    robot.current_weight = sum(item.weight for item in robot.carrying_items)
                    
                    self._continue_picking_items(robot, robots)
                    
            elif robot.target_items and robot.carrying_items:
                target_item = robot.target_items[0]
                if (robot.x, robot.y) == (target_item.x, target_item.y):
                    if robot.current_weight + target_item.weight <= robot.capacity:
                        print(f"Robot {robot.id} picking up additional item #{target_item.id}")
                        picked_item = robot.target_items.pop(0)
                        robot.carrying_items.append(picked_item)
                        picked_item.picked = True
                        robot.current_weight = sum(item.weight for item in robot.carrying_items)
                        
                        self._continue_picking_items(robot, robots)
                    else:
                        print(f"Robot {robot.id} at item #{target_item.id} but capacity exceeded")
                        robot.path = self.path_finder.a_star_pathfinding(
                            (robot.y, robot.x), 
                            (self.drop_point[1], self.drop_point[0]), 
                            robots,
                            robot.id,
                            robot.current_weight
                        )
                    
            elif robot.carrying_items and (robot.x, robot.y) == self.drop_point:
                print(f"Robot {robot.id} successfully delivered {len(robot.carrying_items)} items!")
                robot.carrying_items = []
                robot.current_weight = 0
                robot.path = []  
                
                if progress_callback:
                    progress_callback()
        
        self.handle_stuck_robots(robots)
        
        return total_steps_taken
    
    def _continue_picking_items(self, robot, robots):
        """Helper method to handle continuation of item picking"""
        if robot.target_items:
            next_item = robot.target_items[0]
            if robot.current_weight + next_item.weight <= robot.capacity:
                print(f"Robot {robot.id} heading to next item #{next_item.id}")
                robot.path = self.path_finder.a_star_pathfinding(
                    (robot.y, robot.x), 
                    (next_item.y, next_item.x), 
                    robots,
                    robot.id
                )
                
                if not robot.path:
                    print(f"WARNING: Robot {robot.id} can't find path to next item. Heading to drop point.")
                    robot.path = self.path_finder.a_star_pathfinding(
                        (robot.y, robot.x), 
                        (self.drop_point[1], self.drop_point[0]), 
                        robots,
                        robot.id,
                        robot.current_weight
                    )
            else:
                print(f"Robot {robot.id} at capacity limit. Next item too heavy. Heading to drop point.")
                robot.path = self.path_finder.a_star_pathfinding(
                    (robot.y, robot.x), 
                    (self.drop_point[1], self.drop_point[0]), 
                    robots,
                    robot.id,
                    robot.current_weight
                )
        else:
            print(f"Robot {robot.id} heading to drop point with all items")
            robot.path = self.path_finder.a_star_pathfinding(
                (robot.y, robot.x), 
                (self.drop_point[1], self.drop_point[0]), 
                robots,
                robot.id,
                robot.current_weight
            )
    
    def handle_stuck_robots(self, robots):
        """Handle robots that have been stuck for too long"""
        stuck_threshold = 10  
        
        for robot in robots:
            if robot.carrying_items and not robot.path and self.robot_stuck_time.get(robot.id, 0) >= stuck_threshold:
                print(f"CRITICAL: Robot {robot.id} has been stuck carrying items for {self.robot_stuck_time[robot.id]} cycles")
                print(f"Attempting emergency movement toward drop point")
                
                dx = self.drop_point[0] - robot.x
                dy = self.drop_point[1] - robot.y
                
                dx = 1 if dx > 0 else (-1 if dx < 0 else 0)
                dy = 1 if dy > 0 else (-1 if dy < 0 else 0)
                
                directions_to_try = [
                    (dx, dy),     
                    (dx, 0),    
                    (0, dy),     
                    (-dx, 0),    
                    (0, -dy),     
                    (1, 0), (-1, 0), (0, 1), (0, -1)  
                ]
                
                moved = False
                for try_dx, try_dy in directions_to_try:
                    new_x, new_y = robot.x + try_dx, robot.y + try_dy
                    
                    if (0 <= new_x < self.width and 0 <= new_y < self.height and 
                        self.grid[new_y][new_x] not in [1, 3]):  
                        print(f"Emergency move: Robot {robot.id} moving to ({new_x}, {new_y})")
                        
                        self.grid[robot.y][robot.x] = 0
                        robot.x, robot.y = new_x, new_y
                        self.grid[robot.y][robot.x] = 3
                        robot.steps += 1
                        self.robot_stuck_time[robot.id] = 0
                        moved = True
                        break
                
                if not moved:
                    print(f"CRITICAL: Robot {robot.id} cannot move in any direction!")
                    if self.robot_stuck_time[robot.id] > 30: 
                        print(f"EMERGENCY: Robot {robot.id} dropping items to allow simulation to continue")
                        for item in robot.carrying_items:
                            item.picked = False
                            item.assigned = False
                        robot.carrying_items = []
                        robot.current_weight = 0