import heapq
from collections import defaultdict

class PathFinder:
    def __init__(self, grid, width, height, drop_point=None, obstacle_manager=None):
        self.grid = grid
        self.width = width
        self.height = height
        self.drop_point = drop_point
        self.obstacle_manager = obstacle_manager
    
    def heuristic(self, a, b):
        """Manhattan distance heuristic for A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def a_star_pathfinding(self, start, goal, robots, robot_id, carrying_weight=0):
        """Advanced A* pathfinding algorithm that considers obstacle classification"""
        def is_walkable(pos):
            y, x = pos
            if not (0 <= x < self.width and 0 <= y < self.height):
                return False
            
            # Check obstacle types if obstacle manager is available
            if self.obstacle_manager and self.grid[y][x] in [1, 5, 6]:
                # Permanent obstacles are never walkable
                if self.obstacle_manager.is_obstacle_permanent(x, y):
                    return False
                
                # For temporary obstacles, decide based on remaining lifespan
                if self.obstacle_manager.is_obstacle_temporary(x, y):
                    lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    # If lifespan is very short, we might consider waiting
                    if lifespan <= 3:
                        return True  # Consider as walkable if it will disappear soon
                
                # Semi-permanent obstacles are treated as non-walkable but with lower cost penalty
                if self.obstacle_manager.is_obstacle_semi_permanent(x, y):
                    return False
            elif self.grid[y][x] == 1:  # Without obstacle manager, treat 1 as permanent obstacle
                return False
            
            if pos != goal:
                for robot in robots:
                    if robot.id != robot_id and (robot.x, robot.y) == (x, y):
                        return False
            
            return True

        def get_move_cost(from_pos, to_pos):
            """Calculate the movement cost between positions based on obstacle type"""
            y, x = to_pos
            
            # Base movement cost
            base_cost = 1.0
            
            # Diagonal movement costs more
            if from_pos[0] != to_pos[0] and from_pos[1] != to_pos[1]:
                base_cost = 1.5
            
            # Add weight factor for carrying items
            weight_factor = 1 + (carrying_weight / 20)
            
            # Consider obstacle types for cost calculation
            if self.obstacle_manager and self.grid[y][x] in [5, 6]:
                if self.obstacle_manager.is_obstacle_temporary(x, y):
                    # Temporary obstacles have reduced cost penalty
                    lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan <= 3:
                        # Very short lifespan, small penalty
                        return base_cost * weight_factor * 1.5
                    else:
                        # Longer lifespan, larger penalty
                        return base_cost * weight_factor * 3.0
                
                if self.obstacle_manager.is_obstacle_semi_permanent(x, y):
                    # Semi-permanent obstacles have a higher cost penalty
                    return base_cost * weight_factor * 5.0
            
            return base_cost * weight_factor

        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal directions
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal directions
        ]
        
        if self.drop_point and goal == (self.drop_point[1], self.drop_point[0]):
            max_iterations = self.width * self.height * 4 
        else:
            max_iterations = self.width * self.height * 2
        
        open_set = []
        heapq.heappush(open_set, (0, start))  # Priority queue with (f_score, position)
        came_from = {}
        
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self.heuristic(start, goal)
        
        closed_set = set()
        iterations = 0
        
        while open_set and iterations < max_iterations:
            iterations += 1
            _, current = heapq.heappop(open_set)
            
            if current == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                return path
            
            closed_set.add(current)
            
            for dy, dx in directions:
                neighbor = (current[0] + dy, current[1] + dx)
                
                if not is_walkable(neighbor) or neighbor in closed_set:
                    continue
                
                # Calculate move cost based on obstacle type
                move_cost = get_move_cost(current, neighbor)
                tentative_g = g_score[current] + move_cost
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    
                    if neighbor not in [pos for _, pos in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        print(f"Path not found from ({start[0]},{start[1]}) to ({goal[0]},{goal[1]}) for robot {robot_id}")
        
        # Try to find alternative paths if direct path failed
        search_range = 8 if goal == (self.drop_point[1], self.drop_point[0]) else 5
        
        walkable_adjacent = []
        for dy in range(-search_range, search_range + 1):
            for dx in range(-search_range, search_range + 1):
                test_y, test_x = goal[0] + dy, goal[1] + dx
                if 0 <= test_y < self.height and 0 <= test_x < self.width:
                    test_pos = (test_y, test_x)
                    if is_walkable(test_pos) and test_pos != start:
                        h_dist = self.heuristic(start, test_pos)
                        g_dist = self.heuristic(test_pos, goal)
                        walkable_adjacent.append((test_pos, h_dist, g_dist))
        
        walkable_adjacent.sort(key=lambda x: (x[2], x[1]))
        
        for i, (alt_point, _, _) in enumerate(walkable_adjacent[:5]):
            if alt_point != start:  
                print(f"Trying alternative path to {alt_point} (attempt {i+1}/5)")
                alt_path = self.a_star_pathfinding(start, alt_point, robots, robot_id, carrying_weight)
                if alt_path:
                    print(f"Found alternative path for robot {robot_id}")
                    return alt_path
        
        # Register failed pathfinding if obstacle manager is available
        if self.obstacle_manager:
            # Check if the goal position has an obstacle
            goal_y, goal_x = goal
            if 0 <= goal_x < self.width and 0 <= goal_y < self.height:
                if self.grid[goal_y][goal_x] in [1, 5, 6]:
                    # Register that this robot failed to navigate to this obstacle
                    self.obstacle_manager.register_robot_interaction(robot_id, goal_x, goal_y, False)
        
        # Emergency path for drop point
        if self.drop_point and goal == (self.drop_point[1], self.drop_point[0]):
            print(f"CRITICAL: All paths to drop point failed for robot {robot_id}. Trying emergency movement.")
            delta_y = goal[0] - start[0]
            delta_x = goal[1] - start[1]
            dy = 1 if delta_y > 0 else (-1 if delta_y < 0 else 0)
            dx = 1 if delta_x > 0 else (-1 if delta_x < 0 else 0)
            
            emergency_directions = [
                (dy, dx),     # Toward goal
                (dy, 0),      # Vertical toward goal
                (0, dx),      # Horizontal toward goal
                (-dy, 0),     # Vertical away from goal
                (0, -dx),     # Horizontal away from goal
            ]
            
            for edy, edx in emergency_directions:
                test_y, test_x = start[0] + edy, start[1] + edx
                test_pos = (test_y, test_x)
                if 0 <= test_y < self.height and 0 <= test_x < self.width and is_walkable(test_pos):
                    print(f"Using emergency direction ({edy},{edx})")
                    return [test_pos] 
        
        print(f"All alternative paths failed for robot {robot_id}")
        return []
        
    def wait_or_navigate(self, robot, goal, robots, obstacle_pos):
        """
        Decide whether to wait for a temporary obstacle to clear or find an alternative path
        
        Args:
            robot: The robot object
            goal: The goal position (y, x)
            robots: List of all robots
            obstacle_pos: Position of the obstacle (x, y)
            
        Returns:
            wait_time: How long to wait (0 means don't wait, find alternative path)
        """
        if not self.obstacle_manager:
            return 0
        
        ox, oy = obstacle_pos
        
        # Only consider waiting for temporary obstacles
        if not self.obstacle_manager.is_obstacle_temporary(ox, oy):
            return 0
        
        # Get the remaining lifespan of the obstacle
        lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(ox, oy)
        
        # If the obstacle will clear soon, waiting might be more efficient
        if lifespan <= 5:
            # Check if waiting is more efficient than finding an alternative path
            alt_path = self.a_star_pathfinding(
                (robot.y, robot.x),
                goal,
                robots,
                robot.id,
                robot.current_weight
            )
            
            # If there's no alternative path, definitely wait
            if not alt_path:
                return lifespan
            
            # If alternative path is much longer than waiting, prefer waiting
            if len(alt_path) > lifespan * 2:
                return lifespan
        
        # Default: don't wait, find alternative path
        return 0