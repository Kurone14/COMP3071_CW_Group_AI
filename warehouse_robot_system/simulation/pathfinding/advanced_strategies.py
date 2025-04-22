from typing import List, Tuple, Dict, Set, Optional, Any
import heapq
from collections import defaultdict
import math
import random

from core.models.grid import Grid, CellType
from simulation.pathfinding.strategies import PathStrategy


class AdaptiveDynamicAStarStrategy(PathStrategy):
    """
    Adaptive Dynamic A* (AD*) implementation - Fixed version
    
    Features:
    - Dynamically updates heuristic values based on environment changes
    - Adapts search parameters based on urgency and obstacle density
    - Handles complex environments with improved efficiency
    """
    
    def __init__(self):
        """Initialize the AD* strategy"""
        self.max_iterations = 1500
        self.heuristic_cache = {}
        self.last_path = []
        self.inflation_factor = 1.0
        
    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Calculate heuristic distance between two points
        Uses a weighted Manhattan distance with dynamic inflation
        """
        # Check cache first
        key = (a, b)
        if key in self.heuristic_cache:
            return self.heuristic_cache[key] * self.inflation_factor
        
        # Calculate Manhattan distance
        manhattan = abs(a[0] - b[0]) + abs(a[1] - b[1])
        
        # Add slight diagonal preference
        diagonal = min(abs(a[0] - b[0]), abs(a[1] - b[1]))
        h_value = manhattan - 0.5 * diagonal
        
        # Cache the value
        self.heuristic_cache[key] = h_value
        
        # Apply inflation factor
        return h_value * self.inflation_factor
    
    def _adjust_search_params(self, start: Tuple[int, int], goal: Tuple[int, int], 
                            obstacle_density: float, carrying_weight: int):
        """
        Adjust search parameters based on the current context
        
        Args:
            start: Start position
            goal: Goal position
            obstacle_density: Obstacle density in the search area
            carrying_weight: Weight being carried
        """
        # Distance factor
        distance = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        
        # Adjust inflation factor based on distance and obstacle density
        base_inflation = 1.0
        
        # Longer distances benefit from higher inflation
        if distance > 15:
            base_inflation += min(0.5, distance / 50)
            
        # Higher obstacle density requires more careful search
        if obstacle_density > 0.2:
            base_inflation -= obstacle_density * 0.5
            
        # Carrying weight makes accuracy more important
        if carrying_weight > 0:
            base_inflation -= min(0.3, carrying_weight / 30)
            
        # Ensure inflation factor stays in reasonable range
        self.inflation_factor = max(1.0, min(2.0, base_inflation))
        
        print(f"AD*: Adjusted inflation factor to {self.inflation_factor:.2f} " +
              f"(distance={distance}, density={obstacle_density:.2f}, weight={carrying_weight})")
    
    def find_path(self, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int], 
                 grid: Grid,
                 obstacle_manager=None,
                 robot_id: Optional[int] = None,
                 carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """
        Find a path using Adaptive Dynamic A* algorithm
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            grid: Grid environment
            obstacle_manager: Optional obstacle manager
            robot_id: ID of the robot requesting the path
            carrying_weight: Weight being carried
            
        Returns:
            List of positions forming a path from start to goal
        """
        print(f"AD* starting path search from {start} to {goal}")
        
        # Check for trivial case - start is goal
        if start == goal:
            print("AD*: Start is goal, returning empty path")
            return []
        
        # Setup helper functions for the algorithm
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
                    # Consider very short lifespans walkable for planning
                    if lifespan <= 3:
                        return True
                    return False
                
                # Semi-permanent obstacles are not walkable
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
            """Calculate movement cost between positions"""
            y, x = to_pos
            
            # Base movement cost
            base_cost = 1.0
            
            # Diagonal movement costs more
            if from_pos[0] != to_pos[0] and from_pos[1] != to_pos[1]:
                base_cost = 1.4
            
            # Add weight factor for carrying items
            weight_factor = 1 + (carrying_weight / 20)
            
            # Consider obstacle types for cost calculation
            cell_type = grid.get_cell(x, y)
            if obstacle_manager and cell_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                if cell_type == CellType.TEMPORARY_OBSTACLE:
                    # Temporary obstacles: cost based on remaining lifespan
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan <= 2:
                        # Very short lifespan: small penalty
                        return base_cost * weight_factor * 1.5
                    else:
                        return base_cost * weight_factor * 3.0
                
                if cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    # Semi-permanent obstacles have a higher cost penalty
                    return base_cost * weight_factor * 5.0
            
            return base_cost * weight_factor
        
        # Estimate obstacle density around path area
        buffer = 5
        min_x = max(0, min(start[1], goal[1]) - buffer)
        max_x = min(grid.width-1, max(start[1], goal[1]) + buffer)
        min_y = max(0, min(start[0], goal[0]) - buffer)
        max_y = min(grid.height-1, max(start[0], goal[0]) + buffer)
        
        # Count obstacles in area
        obstacle_count = 0
        total_cells = 0
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                total_cells += 1
                cell_type = grid.get_cell(x, y)
                if cell_type in [CellType.PERMANENT_OBSTACLE, 
                              CellType.TEMPORARY_OBSTACLE, 
                              CellType.SEMI_PERMANENT_OBSTACLE]:
                    obstacle_count += 1
        
        obstacle_density = obstacle_count / max(1, total_cells)
        
        # Adjust search parameters based on context
        self._adjust_search_params(start, goal, obstacle_density, carrying_weight)
        
        # Priority directions - prefer moving toward goal
        goal_dy = 1 if goal[0] > start[0] else (-1 if goal[0] < start[0] else 0)
        goal_dx = 1 if goal[1] > start[1] else (-1 if goal[1] < start[1] else 0)
        
        # Define all possible directions (8-connected grid)
        all_directions = [
            (goal_dy, goal_dx),  # Goal direction first (can be diagonal)
            (goal_dy, 0), (0, goal_dx),  # Cardinal directions toward goal
            (-goal_dy, 0), (0, -goal_dx),  # Cardinal directions away from goal
            (-goal_dy, goal_dx), (goal_dy, -goal_dx), (-goal_dy, -goal_dx)  # Other diagonals
        ]
        
        # Remove duplicates from directions
        directions = []
        for d in all_directions:
            if d not in directions:
                directions.append(d)
        
        # Main AD* algorithm
        open_set = []
        heapq.heappush(open_set, (0, start))  # Priority queue with (f_score, position)
        came_from = {}
        
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = self.heuristic(start, goal)
        
        closed_set = set()
        iterations = 0
        
        # Debug info
        expanded_nodes = 0
        
        # Main loop
        while open_set and iterations < self.max_iterations:
            iterations += 1
            
            # Get node with lowest f_score
            current_f, current = heapq.heappop(open_set)
            
            # Skip if already processed
            if current in closed_set:
                continue
                
            # Check if reached goal
            if current == goal:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.reverse()
                
                print(f"AD*: Path found with {len(path)} steps, explored {expanded_nodes} nodes in {iterations} iterations")
                return path
            
            # Mark as processed
            closed_set.add(current)
            expanded_nodes += 1
            
            # Process neighbors
            for dy, dx in directions:
                neighbor = (current[0] + dy, current[1] + dx)
                
                # Skip if not walkable or already processed
                if not is_walkable(neighbor) or neighbor in closed_set:
                    continue
                
                # Calculate tentative g_score
                move_cost = get_move_cost(current, neighbor)
                tentative_g = g_score[current] + move_cost
                
                if tentative_g < g_score[neighbor]:
                    # This is a better path to neighbor
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)
                    
                    # Add to open set if not already there
                    in_open_set = False
                    for _, pos in open_set:
                        if pos == neighbor:
                            in_open_set = True
                            break
                            
                    if not in_open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        print(f"AD*: No path found after {iterations} iterations, explored {expanded_nodes} nodes")
        
        # If no path found to goal, try to find path to alternate goal
        if iterations >= self.max_iterations:
            print("AD*: Search iteration limit reached, trying alternate goals")
        
        return self._find_alternate_path(start, goal, grid, obstacle_manager, robot_id, carrying_weight)
    
    def _find_alternate_path(self, start, goal, grid, obstacle_manager, robot_id, carrying_weight):
        """Find a path to an alternate goal when direct path fails"""
        print("AD*: Looking for alternative path")
        
        # Maximum search radius for alternate goals
        max_radius = 10
        
        # Collect candidate alternate goals
        candidates = []
        
        # Try all positions in increasing radius until we find walkable cells
        for radius in range(1, max_radius + 1):
            candidates_at_radius = []
            
            # Check all positions at this radius
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    # Only consider positions exactly at radius
                    if abs(dy) + abs(dx) == radius:
                        alt_y = goal[0] + dy
                        alt_x = goal[1] + dx
                        
                        # Check if position is valid
                        if grid.in_bounds(alt_x, alt_y):
                            cell_type = grid.get_cell(alt_x, alt_y)
                            
                            # Check if position is walkable
                            if cell_type not in [CellType.PERMANENT_OBSTACLE, 
                                               CellType.TEMPORARY_OBSTACLE, 
                                               CellType.SEMI_PERMANENT_OBSTACLE]:
                                # Calculate priority score (lower is better)
                                # Distance to original goal + distance from start
                                dist_to_goal = abs(alt_y - goal[0]) + abs(alt_x - goal[1])
                                dist_from_start = abs(alt_y - start[0]) + abs(alt_x - start[1])
                                
                                # Weighted score
                                score = dist_to_goal * 0.7 + dist_from_start * 0.3
                                
                                candidates_at_radius.append((score, (alt_y, alt_x)))
            
            # If we found candidates at this radius, sort and try them
            if candidates_at_radius:
                candidates_at_radius.sort()  # Sort by score
                candidates.extend(candidates_at_radius)
                
                # If we have enough candidates, break
                if len(candidates) >= 5:
                    break
        
        # If no candidates found
        if not candidates:
            print("AD*: No alternative goals found")
            return []
        
        # Try paths to top candidates
        print(f"AD*: Trying {len(candidates)} alternative goals")
        
        for _, alt_goal in candidates[:5]:  # Try up to 5 candidates
            # Use a simpler search to avoid recursion
            path = self._simple_astar(start, alt_goal, grid, obstacle_manager, robot_id, carrying_weight)
            
            if path:
                print(f"AD*: Found alternative path to {alt_goal} with {len(path)} steps")
                return path
        
        # No path found
        print("AD*: Could not find any path")
        return []
    
    def _simple_astar(self, start, goal, grid, obstacle_manager, robot_id, carrying_weight):
        """Simplified A* search for finding paths to alternate goals"""
        def is_walkable(y, x):
            if not grid.in_bounds(x, y):
                return False
            cell_type = grid.get_cell(x, y)
            return cell_type not in [CellType.PERMANENT_OBSTACLE, 
                                    CellType.TEMPORARY_OBSTACLE, 
                                    CellType.SEMI_PERMANENT_OBSTACLE]
        
        # Define directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        # A* data structures
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        
        g_score = defaultdict(lambda: float('inf'))
        g_score[start] = 0
        
        f_score = defaultdict(lambda: float('inf'))
        f_score[start] = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        
        closed_set = set()
        max_iterations = 500
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
                y, x = neighbor
                
                if not is_walkable(y, x) or neighbor in closed_set:
                    continue
                
                # Diagonal movement costs more
                move_cost = 1.4 if (dy != 0 and dx != 0) else 1.0
                
                tentative_g = g_score[current] + move_cost
                
                if tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + abs(y - goal[0]) + abs(x - goal[1])
                    
                    in_open_set = False
                    for _, pos in open_set:
                        if pos == neighbor:
                            in_open_set = True
                            break
                            
                    if not in_open_set:
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []


class ProximalPolicyDijkstraStrategy:
    """
    Proximal Policy-Dijkstra (PP-D) pathfinding strategy
    
    Features:
    - Combines Dijkstra's algorithm with a learned policy for next node selection
    - Uses obstacle type knowledge to make informed decisions
    - Excellent for environments with dynamic obstacles
    """
    
    def __init__(self):
        self.max_iterations = 2000  # Higher limit for thorough exploration
        self.policy_weights = {}    # Weights for the proximal policy
        self.exploration_factor = 0.1  # Exploration factor for learning
        self.direction_priors = {}  # Prior weights for directions
        self.successful_paths = []  # Record of successful paths
        self.policy_updates = 0     # Count of policy updates
        
    def reset(self):
        """Reset the strategy state"""
        self.policy_weights = {}
        self.direction_priors = {}
        self.successful_paths = []
        self.policy_updates = 0
        self.exploration_factor = 0.1
    
    def _initialize_policy(self, grid_width, grid_height):
        """Initialize policy weights if not already done"""
        if not self.policy_weights:
            # Initialize with small random values
            for y in range(grid_height):
                for x in range(grid_width):
                    self.policy_weights[(y, x)] = {
                        (-1, 0): 0.125,  # North
                        (1, 0): 0.125,   # South
                        (0, -1): 0.125,  # West
                        (0, 1): 0.125,   # East
                        (-1, -1): 0.125, # Northwest
                        (-1, 1): 0.125,  # Northeast
                        (1, -1): 0.125,  # Southwest
                        (1, 1): 0.125,   # Southeast
                    }
    
    def _update_policy(self, path, grid, success_factor=1.0):
        """
        Update policy weights based on path success/failure
        
        Args:
            path: The path that was taken
            grid: The grid environment
            success_factor: How successful the path was (1.0 = fully successful)
        """
        if not path or len(path) < 2:
            return
            
        # Update count
        self.policy_updates += 1
        
        # Reduce exploration factor over time
        self.exploration_factor = max(0.01, 0.1 * math.exp(-self.policy_updates / 50))
        
        # Only update for successful paths
        if success_factor > 0:
            # Compute directions taken along path
            for i in range(len(path) - 1):
                pos = path[i]
                next_pos = path[i + 1]
                
                direction = (next_pos[0] - pos[0], next_pos[1] - pos[1])
                
                # Update policy weights for this position and direction
                if pos in self.policy_weights:
                    # Increase weight for the direction taken
                    for d in self.policy_weights[pos]:
                        if d == direction:
                            # Increase weight for successful direction
                            self.policy_weights[pos][d] += 0.05 * success_factor
                        else:
                            # Slightly decrease other directions
                            self.policy_weights[pos][d] = max(0.01, self.policy_weights[pos][d] - 0.01)
                    
                    # Normalize weights
                    total = sum(self.policy_weights[pos].values())
                    for d in self.policy_weights[pos]:
                        self.policy_weights[pos][d] /= total
            
            # Store successful path
            self.successful_paths.append(path)
            if len(self.successful_paths) > 10:
                self.successful_paths.pop(0)  # Keep only the most recent 10 paths
    
    def _get_direction_weight(self, current, direction, goal):
        """
        Get weight for a direction based on policy and goal direction
        
        Args:
            current: Current position
            direction: Direction to check
            goal: Goal position
            
        Returns:
            float: Weight for this direction
        """
        # Policy weight
        policy_weight = 0.5
        if current in self.policy_weights and direction in self.policy_weights[current]:
            policy_weight = self.policy_weights[current][direction]
        
        # Goal direction component
        dy = goal[0] - current[0]
        dx = goal[1] - current[1]
        
        # Normalize direction
        if dy != 0:
            dy = dy // abs(dy)
        if dx != 0:
            dx = dx // abs(dx)
        
        goal_dir = (dy, dx)
        
        # Goal direction weight
        goal_weight = 0.5
        if direction == goal_dir:
            goal_weight = 1.0
        elif direction[0] == goal_dir[0] or direction[1] == goal_dir[1]:
            goal_weight = 0.75
        
        # Combined weight
        return policy_weight * 0.6 + goal_weight * 0.4
    
    def find_path(self, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int], 
                 grid: Grid,
                 obstacle_manager=None,
                 robot_id: Optional[int] = None,
                 carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """
        Find a path using Proximal Policy-Dijkstra (PP-D) algorithm
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            grid: Grid object representing the environment
            obstacle_manager: Optional obstacle manager for advanced obstacle handling
            robot_id: ID of the robot requesting the path
            carrying_weight: Weight being carried (affects movement cost)
            
        Returns:
            List of positions forming a path from start to goal
        """
        # Initialize policy weights if needed
        self._initialize_policy(grid.width, grid.height)
        
        # Check if a similar path exists in successful paths
        for path in self.successful_paths:
            if path[0] == start and path[-1] == goal:
                # Check if path is still valid
                valid = True
                for pos in path:
                    y, x = pos
                    if not grid.is_cell_walkable(x, y, include_temporary=True):
                        valid = False
                        break
                
                if valid:
                    # Return a copy of the cached path
                    return path[1:].copy()  # Exclude the start position
        
        # Helper function for checking if a position is walkable
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
                
                # PP-D is more aggressive with temporary obstacles
                if cell_type == CellType.TEMPORARY_OBSTACLE:
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    # More aggressive with temporary obstacles
                    if lifespan <= 4:  # Higher threshold than other algorithms
                        return True
                    return False
                
                # Semi-permanent obstacles are avoided but with special handling
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
        
        # Get cost of moving between positions
        def get_move_cost(from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                        direction_weight: float) -> float:
            """
            Calculate movement cost between positions, influenced by policy
            
            Args:
                from_pos: Starting position
                to_pos: Target position
                direction_weight: Weight for this direction from policy
            """
            y, x = to_pos
            
            # Base movement cost
            base_cost = 1.0
            
            # Diagonal movement costs more
            if from_pos[0] != to_pos[0] and from_pos[1] != to_pos[1]:
                base_cost = 1.4
            
            # Add weight factor for carrying items (logarithmic scale)
            weight_factor = 1 + math.log1p(carrying_weight / 15)  # Less penalty than other algorithms
            
            # Cost multiplier based on cell type
            cell_type = grid.get_cell(x, y)
            cell_multiplier = 1.0
            
            if obstacle_manager and cell_type in [CellType.TEMPORARY_OBSTACLE, 
                                                 CellType.SEMI_PERMANENT_OBSTACLE]:
                if cell_type == CellType.TEMPORARY_OBSTACLE:
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan <= 2:
                        cell_multiplier = 1.2  # Small penalty
                    else:
                        cell_multiplier = 2.0  # Larger penalty
                elif cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    cell_multiplier = 3.0  # Even larger penalty
            
            # Factor in direction weight from policy (inverted: higher weight = lower cost)
            policy_factor = 1.0 / (direction_weight + 0.01)
            
            # Combined cost
            return base_cost * weight_factor * cell_multiplier * policy_factor
        
        # Main PP-D algorithm
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),  # Cardinal directions
            (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonal directions
        ]
        
        # Priority queue for Dijkstra's algorithm
        dist = {start: 0}
        prev = {}
        queue = [(0, start)]
        visited = set()
        
        # Main loop
        iterations = 0
        while queue and iterations < self.max_iterations:
            iterations += 1
            
            # Get node with lowest distance
            current_dist, current = heapq.heappop(queue)
            
            # Skip if already visited
            if current in visited:
                continue
                
            # Mark as visited
            visited.add(current)
            
            # Check if found goal
            if current == goal:
                # Reconstruct path
                path = []
                while current in prev:
                    path.append(current)
                    current = prev[current]
                path.reverse()
                
                # Update policy with successful path
                full_path = [start] + path
                self._update_policy(full_path, grid, success_factor=1.0)
                
                return path
            
            # Process neighbors with policy influence
            for direction in directions:
                # Get direction weight from policy
                direction_weight = self._get_direction_weight(current, direction, goal)
                
                # Include exploration factor
                if random.random() < self.exploration_factor:
                    direction_weight = random.uniform(0.5, 1.0)
                
                # Calculate neighbor position
                dy, dx = direction
                neighbor = (current[0] + dy, current[1] + dx)
                
                # Skip if not walkable
                if not is_walkable(neighbor) or neighbor in visited:
                    continue
                
                # Calculate cost to neighbor
                cost = get_move_cost(current, neighbor, direction_weight)
                new_dist = dist[current] + cost
                
                # Update if better path found
                if neighbor not in dist or new_dist < dist[neighbor]:
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(queue, (new_dist, neighbor))
        
        # Path not found - try to find an alternate goal
        alternate_paths = self._find_alternatives(start, goal, grid, obstacle_manager, robot_id)
        
        if alternate_paths:
            # If found an alternate path, update policy with partial success
            self._update_policy(alternate_paths, grid, success_factor=0.5)
            return alternate_paths
            
        # No path found - update policy with failure
        self._update_policy([start], grid, success_factor=0)
        return []
    
    def _find_alternatives(self, start, goal, grid, obstacle_manager, robot_id):
        """Find alternate paths when direct path fails"""
        # Try to find paths to nearby points instead
        max_radius = 8
        
        # Get candidate alternate goals
        alternate_goals = []
        for radius in range(1, max_radius + 1):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    # Only consider points at exactly radius distance
                    if abs(dy) + abs(dx) != radius:
                        continue
                        
                    alt_y, alt_x = goal[0] + dy, goal[1] + dx
                    
                    if not grid.in_bounds(alt_x, alt_y):
                        continue
                        
                    # Check if this position is walkable
                    if grid.is_cell_walkable(alt_x, alt_y, include_temporary=True):
                        # Calculate priority based on distance
                        distance = abs(alt_y - goal[0]) + abs(alt_x - goal[1])
                        alternate_goals.append((distance, (alt_y, alt_x)))
            
            # If found some candidates at this radius, stop expanding
            if alternate_goals:
                break
        
        # Sort by distance to original goal
        alternate_goals.sort()
        
        # Try paths to top 3 alternate goals
        for _, alt_goal in alternate_goals[:3]:
            # Use a simpler strategy for alternate goals to avoid deep recursion
            path = self._simple_dijkstra(start, alt_goal, grid)
            
            if path:
                return path
                
        return []
    
    def _simple_dijkstra(self, start, goal, grid):
        """Simple Dijkstra's algorithm for finding paths to alternate goals"""
        # This is a basic Dijkstra implementation to avoid recursion
        
        def is_walkable(y, x):
            if not grid.in_bounds(x, y):
                return False
            return grid.is_cell_walkable(x, y, include_temporary=True)
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        dist = {start: 0}
        prev = {}
        queue = [(0, start)]
        visited = set()
        
        while queue:
            current_dist, current = heapq.heappop(queue)
            
            if current in visited:
                continue
                
            visited.add(current)
            
            if current == goal:
                path = []
                while current in prev:
                    path.append(current)
                    current = prev[current]
                path.reverse()
                return path
            
            for dy, dx in directions:
                neighbor = (current[0] + dy, current[1] + dx)
                ny, nx = neighbor
                
                if not is_walkable(ny, nx) or neighbor in visited:
                    continue
                
                cost = 1.4 if dy != 0 and dx != 0 else 1.0
                new_dist = dist[current] + cost
                
                if neighbor not in dist or new_dist < dist[neighbor]:
                    dist[neighbor] = new_dist
                    prev[neighbor] = current
                    heapq.heappush(queue, (new_dist, neighbor))
        
        return []