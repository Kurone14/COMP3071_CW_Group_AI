from typing import List, Tuple, Dict, Set, Optional, Protocol, Callable
import heapq
from collections import defaultdict
from abc import ABC, abstractmethod

from core.models.grid import Grid, CellType


class PathStrategy(ABC):
    """Abstract base class for pathfinding strategies"""
    
    @abstractmethod
    def find_path(self, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int], 
                 grid: Grid,
                 obstacle_manager=None,
                 robot_id: Optional[int] = None,
                 carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """Find a path from start to goal"""
        pass


class AStarStrategy(PathStrategy):
    """A* pathfinding algorithm implementation"""
    
    def __init__(self):
        self.max_iterations = 1000  # Default iteration limit
        
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> int:
        """Manhattan distance heuristic for A*"""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def find_path(self, 
             start: Tuple[int, int], 
             goal: Tuple[int, int], 
             grid: Grid,
             obstacle_manager=None,
             robot_id: Optional[int] = None,
             carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """
        Find a path using A* algorithm
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            grid: Grid object representing the environment
            obstacle_manager: Optional obstacle manager for advanced obstacle handling
            robot_id: ID of the robot requesting the path (for collision avoidance)
            carrying_weight: Weight being carried (affects movement cost)
            
        Returns:
            List of positions forming a path from start to goal
        """
        def is_walkable(pos: Tuple[int, int]) -> bool:
            """Check if a position is walkable"""
            y, x = pos
            if not grid.in_bounds(x, y):
                return False
                
            cell_type = grid.get_cell(x, y)
            
            # Consider obstacle types if obstacle manager is available
            if obstacle_manager and cell_type in [CellType.PERMANENT_OBSTACLE, 
                                                CellType.TEMPORARY_OBSTACLE, 
                                                CellType.SEMI_PERMANENT_OBSTACLE]:
                # Permanent obstacles are never walkable
                if cell_type == CellType.PERMANENT_OBSTACLE:
                    return False
                
                # For temporary obstacles, decide based on remaining lifespan
                if cell_type == CellType.TEMPORARY_OBSTACLE:
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    # Only consider it walkable for path planning if it will disappear very soon
                    # This is different from actual movement - robots won't move through obstacles 
                    # until they're completely gone
                    if lifespan <= 2:  # Very short lifespan for planning purposes
                        return True
                    return False
                
                # Semi-permanent obstacles are treated as non-walkable but with lower cost penalty
                if cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    return False
            elif cell_type == CellType.PERMANENT_OBSTACLE:
                return False
            
            # Avoid other robots except at goal
            if pos != goal:
                entities = grid.get_entities_at_position(x, y)
                for entity_id in entities:
                    if entity_id != robot_id:  # Don't avoid self
                        return False
            
            return True
        
        def get_move_cost(from_pos: Tuple[int, int], to_pos: Tuple[int, int]) -> float:
            """Calculate movement cost between positions based on obstacle type"""
            y, x = to_pos
            
            # Base movement cost
            base_cost = 1.0
            
            # Diagonal movement costs more
            if from_pos[0] != to_pos[0] and from_pos[1] != to_pos[1]:
                base_cost = 1.5
            
            # Add weight factor for carrying items
            weight_factor = 1 + (carrying_weight / 20)
            
            # Consider obstacle types for cost calculation
            cell_type = grid.get_cell(x, y)
            if obstacle_manager and cell_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                if cell_type == CellType.TEMPORARY_OBSTACLE:
                    # Temporary obstacles have reduced cost penalty
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan <= 2:
                        # Very short lifespan, small penalty
                        return base_cost * weight_factor * 1.5
                    else:
                        # Longer lifespan, larger penalty
                        return base_cost * weight_factor * 3.0
                
                if cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    # Semi-permanent obstacles have a higher cost penalty
                    return base_cost * weight_factor * 5.0
            
            return base_cost * weight_factor
        
        # A* algorithm implementation
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal directions
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal directions
        ]
        
        # Increase iterations for important paths (e.g., to drop point)
        if grid.drop_point and goal == (grid.drop_point[1], grid.drop_point[0]):
            max_iterations = grid.width * grid.height * 4
        else:
            max_iterations = grid.width * grid.height * 2
            
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
                    
                    in_open_set = False
                    for _, pos in open_set:
                        if pos == neighbor:
                            in_open_set = True
                            break
                            
                    if not in_open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        # If no path found, try to find alternative paths
        search_range = 8 if grid.drop_point and goal == (grid.drop_point[1], grid.drop_point[0]) else 5
        
        walkable_adjacent = []
        for dy in range(-search_range, search_range + 1):
            for dx in range(-search_range, search_range + 1):
                test_pos = (goal[0] + dy, goal[1] + dx)
                test_y, test_x = test_pos
                
                if grid.in_bounds(test_x, test_y):
                    if is_walkable(test_pos) and test_pos != start:
                        h_dist = self.heuristic(start, test_pos)
                        g_dist = self.heuristic(test_pos, goal)
                        walkable_adjacent.append((test_pos, h_dist, g_dist))
        
        walkable_adjacent.sort(key=lambda x: (x[2], x[1]))
        
        for i, (alt_point, _, _) in enumerate(walkable_adjacent[:5]):
            if alt_point != start:  
                alt_path = self.find_path(start, alt_point, grid, obstacle_manager, robot_id, carrying_weight)
                if alt_path:
                    return alt_path
        
        # Register failed pathfinding if obstacle manager is available
        if obstacle_manager:
            # Check if the goal position has an obstacle
            goal_y, goal_x = goal
            if grid.in_bounds(goal_x, goal_y):
                cell_type = grid.get_cell(goal_x, goal_y)
                if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                    # Register that this robot failed to navigate to this obstacle
                    obstacle_manager.register_robot_interaction(robot_id, goal_x, goal_y, False)
        
        # Emergency path for drop point
        if grid.drop_point and goal == (grid.drop_point[1], grid.drop_point[0]):
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
                test_pos = (start[0] + edy, start[1] + edx)
                test_y, test_x = test_pos
                if grid.in_bounds(test_x, test_y) and is_walkable(test_pos):
                    return [test_pos]
        
        return []  # No path found