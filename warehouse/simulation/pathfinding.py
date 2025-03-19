import heapq
from collections import defaultdict

class PathFinder:
    def __init__(self, grid, width, height, drop_point=None):
        self.grid = grid
        self.width = width
        self.height = height
        self.drop_point = drop_point 
    
    def heuristic(self, a, b):
        """Manhattan distance heuristic for A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def a_star_pathfinding(self, start, goal, robots, robot_id, carrying_weight=0):
        """Advanced A* pathfinding algorithm with more robust path finding"""
        def is_walkable(pos):
            y, x = pos
            if not (0 <= x < self.width and 0 <= y < self.height):
                return False
            
            if self.grid[y][x] == 1:
                return False
            
            if pos != goal:
                for robot in robots:
                    if robot.id != robot_id and (robot.x, robot.y) == (x, y):
                        return False
            
            return True

        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  
            (-1, -1), (-1, 1), (1, -1), (1, 1) 
        ]
        
        directions_with_priority = [
            ((-1, 0), 1), ((1, 0), 1), ((0, -1), 1), ((0, 1), 1),  
            ((-1, -1), 1.5), ((-1, 1), 1.5), ((1, -1), 1.5), ((1, 1), 1.5)  
        ]
        
        if self.drop_point and goal == (self.drop_point[1], self.drop_point[0]):
            max_iterations = self.width * self.height * 4 
        else:
            max_iterations = self.width * self.height * 2
        
        open_set = []
        heapq.heappush(open_set, (0, start)) 
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
            
            for (dy, dx), base_cost in directions_with_priority:
                neighbor = (current[0] + dy, current[1] + dx)
                
                if not is_walkable(neighbor) or neighbor in closed_set:
                    continue
                
                weight_factor = 1 + (carrying_weight / 20)  
                tentative_g = g_score[current] + (base_cost * weight_factor)
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    
                    if neighbor not in [pos for _, pos in open_set]:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        print(f"Path not found from ({start[0]},{start[1]}) to ({goal[0]},{goal[1]}) for robot {robot_id}")
        
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
        
        if self.drop_point and goal == (self.drop_point[1], self.drop_point[0]):
            print(f"CRITICAL: All paths to drop point failed for robot {robot_id}. Trying emergency movement.")
            delta_y = goal[0] - start[0]
            delta_x = goal[1] - start[1]
            dy = 1 if delta_y > 0 else (-1 if delta_y < 0 else 0)
            dx = 1 if delta_x > 0 else (-1 if delta_x < 0 else 0)
            
            emergency_directions = [
                (dy, dx),     
                (dy, 0),      
                (0, dx),      
                (-dy, 0),     
                (0, -dx),     
            ]
            
            for edy, edx in emergency_directions:
                test_y, test_x = start[0] + edy, start[1] + edx
                test_pos = (test_y, test_x)
                if 0 <= test_y < self.height and 0 <= test_x < self.width and is_walkable(test_pos):
                    print(f"Using emergency direction ({edy},{edx})")
                    return [test_pos] 
        
        print(f"All alternative paths failed for robot {robot_id}")
        return []  