from typing import List, Tuple, Dict, Optional, Any
import random
import math
import time

from core.models.grid import Grid, CellType
from simulation.pathfinding.strategies import PathStrategy, AStarStrategy
from simulation.pathfinding.advanced_strategies import AdaptiveDynamicAStarStrategy, ProximalPolicyDijkstraStrategy


class PathStrategySelector:
    """
    Dynamically selects the best pathfinding strategy based on the current environment
    and task characteristics.
    """
    
    def __init__(self, grid: Grid, obstacle_manager=None):
        """
        Initialize the strategy selector
        
        Args:
            grid: The environment grid
            obstacle_manager: Optional obstacle manager for advanced obstacle handling
        """
        self.grid = grid
        self.obstacle_manager = obstacle_manager
        
        # Initialize strategies
        self.strategies = {
            'astar': AStarStrategy(),
            'ad_star': AdaptiveDynamicAStarStrategy(),
            'pp_dijkstra': ProximalPolicyDijkstraStrategy()
        }
        
        # Performance tracking for each strategy
        self.strategy_performance = {
            'astar': {'success_rate': 0.5, 'speed': 0.5, 'path_quality': 0.5, 'used_count': 0},
            'ad_star': {'success_rate': 0.5, 'speed': 0.5, 'path_quality': 0.5, 'used_count': 0},
            'pp_dijkstra': {'success_rate': 0.5, 'speed': 0.5, 'path_quality': 0.5, 'used_count': 0}
        }
        
        # Context-specific strategy success tracking
        # Format: {context_hash: {strategy_name: success_rate}}
        self.context_performance = {}
        
        # Current strategy for each robot
        self.robot_strategies = {}  # robot_id -> strategy_name
        
        # Strategy statistics
        self.execution_times = {}  # strategy_name -> list of execution times
        self.path_lengths = {}     # strategy_name -> list of path lengths
        self.path_successes = {}   # strategy_name -> list of success flags
        
        # Initialize statistics
        for strategy in self.strategies.keys():
            self.execution_times[strategy] = []
            self.path_lengths[strategy] = []
            self.path_successes[strategy] = []
    
    def select_strategy(self, 
                       start: Tuple[int, int], 
                       goal: Tuple[int, int],
                       robot_id: Optional[int] = None,
                       carrying_weight: int = 0) -> str:
        """
        Select the best pathfinding strategy for the current situation
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            robot_id: ID of the robot requesting path
            carrying_weight: Weight being carried
            
        Returns:
            str: Name of the selected strategy
        """
        # Get the context hash
        context = self._get_context_hash(start, goal, carrying_weight)
        
        # If context has been seen before, use past performance data
        if context in self.context_performance and random.random() > 0.1:  # 10% exploration rate
            # Get performance for this context
            context_perf = self.context_performance[context]
            
            # Sort strategies by performance in this context
            sorted_strategies = sorted(context_perf.items(), key=lambda x: x[1], reverse=True)
            
            # Select the best strategy
            best_strategy = sorted_strategies[0][0]
            
            # Update robot's strategy
            if robot_id is not None:
                self.robot_strategies[robot_id] = best_strategy
                
            return best_strategy
        
        # If robot has a previous strategy, check if it should continue using it
        if robot_id is not None and robot_id in self.robot_strategies:
            current_strategy = self.robot_strategies[robot_id]
            
            # Get global performance of current strategy
            perf = self.strategy_performance[current_strategy]
            
            # If it's performing well, stick with it (80% of the time)
            if (perf['success_rate'] > 0.7 and 
                perf['path_quality'] > 0.6 and 
                random.random() < 0.8):
                return current_strategy
        
        # Otherwise, select strategy based on context
        return self._select_by_context(start, goal, carrying_weight, robot_id)
    
    def _select_by_context(self, 
                          start: Tuple[int, int], 
                          goal: Tuple[int, int],
                          carrying_weight: int,
                          robot_id: Optional[int]) -> str:
        """
        Select strategy based on environmental context and task
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            carrying_weight: Weight being carried
            robot_id: ID of the robot
            
        Returns:
            str: Name of the selected strategy
        """
        # Calculate features
        features = self._extract_context_features(start, goal, carrying_weight)
        
        # Heuristic rules for strategy selection
        
        # Feature thresholds
        long_distance = features['distance'] > 15
        complex_environment = features['obstacle_density'] > 0.2
        many_dynamic_obstacles = features['dynamic_obstacle_count'] > 3
        urgent_path = features['is_carrying'] and features['is_to_drop_point']
        path_predictability = features['path_predictability']
        repeated_traversal = features['traversal_count'] > 2
        
        # 1. For urgent paths to drop point with heavy loads, prefer AD*
        if urgent_path and carrying_weight > 5:
            strategy = 'ad_star'
        
        # 2. For areas with many dynamic obstacles, prefer PP-Dijkstra
        elif many_dynamic_obstacles:
            strategy = 'pp_dijkstra'
            
        # 3. For long distances through complex environments, prefer AD*
        elif long_distance and complex_environment:
            strategy = 'ad_star'
            
        # 4. For frequently traversed paths, prefer PP-Dijkstra to learn
        elif repeated_traversal and path_predictability > 0.7:
            strategy = 'pp_dijkstra'
            
        # 5. For simple, predictable paths, use basic A*
        elif path_predictability > 0.8 and not complex_environment:
            strategy = 'astar'
            
        # 6. If carrying items but features don't match other rules, lean toward AD*
        elif features['is_carrying']:
            strategy = 'ad_star'
            
        # 7. Default: balance based on overall performance
        else:
            # Calculate scores for each strategy based on performance metrics
            scores = {}
            for name, perf in self.strategy_performance.items():
                # Weighted score considering success rate, speed, and path quality
                scores[name] = (
                    perf['success_rate'] * 0.5 +
                    perf['speed'] * 0.25 +
                    perf['path_quality'] * 0.25
                )
            
            # Select the strategy with the highest score
            strategy = max(scores.items(), key=lambda x: x[1])[0]
            
            # Add 10% exploration rate for trying underused strategies
            if random.random() < 0.1:
                # Find least used strategy
                least_used = min(self.strategy_performance.items(), 
                                key=lambda x: x[1]['used_count'])[0]
                strategy = least_used
        
        # Update robot's strategy
        if robot_id is not None:
            self.robot_strategies[robot_id] = strategy
            
        return strategy
    
    def _extract_context_features(self, start, goal, carrying_weight):
        """
        Extract features from the current environment context
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            carrying_weight: Weight being carried
            
        Returns:
            dict: Dictionary of context features
        """
        # Calculate Manhattan distance
        distance = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
        
        # Estimate obstacle density in a bounding box between start and goal
        min_y = min(start[0], goal[0])
        max_y = max(start[0], goal[0])
        min_x = min(start[1], goal[1])
        max_x = max(start[1], goal[1])
        
        # Add padding to bounding box
        padding = 3
        min_y = max(0, min_y - padding)
        max_y = min(self.grid.height - 1, max_y + padding)
        min_x = max(0, min_x - padding)
        max_x = min(self.grid.width - 1, max_x + padding)
        
        # Count obstacles in bounding box
        obstacle_count = 0
        temporary_obstacle_count = 0
        semi_perm_obstacle_count = 0
        total_cells = 0
        
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                total_cells += 1
                cell_type = self.grid.get_cell(x, y)
                
                if cell_type == CellType.PERMANENT_OBSTACLE:
                    obstacle_count += 1
                elif cell_type == CellType.TEMPORARY_OBSTACLE:
                    obstacle_count += 1
                    temporary_obstacle_count += 1
                elif cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    obstacle_count += 1
                    semi_perm_obstacle_count += 1
        
        # Calculate obstacle density
        obstacle_density = obstacle_count / max(1, total_cells)
        
        # Determine if path is to drop point
        is_to_drop_point = False
        if self.grid.drop_point:
            drop_y, drop_x = self.grid.drop_point[1], self.grid.drop_point[0]
            is_to_drop_point = (goal[0] == drop_y and goal[1] == drop_x)
        
        # Estimate path predictability based on obstacle distribution
        # More uniform distribution = more predictable
        if obstacle_count > 0:
            # Calculate center of obstacles
            obstacle_center_y = 0
            obstacle_center_x = 0
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    cell_type = self.grid.get_cell(x, y)
                    if cell_type in [CellType.PERMANENT_OBSTACLE, 
                                    CellType.TEMPORARY_OBSTACLE, 
                                    CellType.SEMI_PERMANENT_OBSTACLE]:
                        obstacle_center_y += y
                        obstacle_center_x += x
            
            obstacle_center_y /= obstacle_count
            obstacle_center_x /= obstacle_count
            
            # Calculate variance around center
            variance = 0
            for y in range(min_y, max_y + 1):
                for x in range(min_x, max_x + 1):
                    cell_type = self.grid.get_cell(x, y)
                    if cell_type in [CellType.PERMANENT_OBSTACLE, 
                                    CellType.TEMPORARY_OBSTACLE, 
                                    CellType.SEMI_PERMANENT_OBSTACLE]:
                        variance += ((y - obstacle_center_y) ** 2 + 
                                    (x - obstacle_center_x) ** 2)
            
            variance /= obstacle_count
            
            # Normalize variance (0 = unpredictable, 1 = predictable)
            area = (max_y - min_y + 1) * (max_x - min_x + 1)
            max_variance = area / 4  # Theoretical maximum variance
            path_predictability = 1 - min(1, variance / max_variance)
        else:
            # No obstacles = very predictable
            path_predictability = 1.0
        
        # Count how many times this path has been traversed (approximation)
        path_key = (min(start[0], goal[0]), min(start[1], goal[1]), 
                   max(start[0], goal[0]), max(start[1], goal[1]))
        traversal_count = self._get_traversal_count(path_key)
        
        return {
            'distance': distance,
            'obstacle_density': obstacle_density,
            'dynamic_obstacle_count': temporary_obstacle_count + semi_perm_obstacle_count,
            'is_carrying': carrying_weight > 0,
            'is_to_drop_point': is_to_drop_point,
            'path_predictability': path_predictability,
            'traversal_count': traversal_count
        }
    
    def _get_traversal_count(self, path_key):
        """Get approximation of how many times a similar path has been traversed"""
        # In a real implementation, this would track actual path traversals
        # For now, we'll use a simplified approach
        if not hasattr(self, 'path_traversals'):
            self.path_traversals = {}
        
        if path_key in self.path_traversals:
            self.path_traversals[path_key] += 1
            return self.path_traversals[path_key]
        else:
            self.path_traversals[path_key] = 1
            return 1
    
    def _get_context_hash(self, start, goal, carrying_weight):
        """
        Generate a hash representing the current pathfinding context
        
        Args:
            start: Starting position (y, x)
            goal: Goal position (y, x)
            carrying_weight: Weight being carried
        """
        # Discretize the positions to reduce the number of unique contexts
        grid_size = max(self.grid.width, self.grid.height)
        cell_size = max(1, grid_size // 10)  # Divide grid into ~10 regions
        
        # Discretize positions
        start_disc = (start[0] // cell_size, start[1] // cell_size)
        goal_disc = (goal[0] // cell_size, goal[1] // cell_size)
        
        # Discretize carrying weight
        weight_disc = min(3, carrying_weight // 5)  # 0-4, 5-9, 10-14, 15+
        
        # Calculate a simple context hash
        context_hash = (
            f"{start_disc[0]},{start_disc[1]}_"
            f"{goal_disc[0]},{goal_disc[1]}_"
            f"{weight_disc}"
        )
        
        return context_hash
    
    def find_path(self, 
                 start: Tuple[int, int], 
                 goal: Tuple[int, int], 
                 grid: Grid,
                 obstacle_manager=None,
                 robot_id: Optional[int] = None,
                 carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """
        Find a path using the most appropriate strategy for the context
        
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
        # Select the best strategy for the current context
        strategy_name = self.select_strategy(start, goal, robot_id, carrying_weight)
        strategy = self.strategies[strategy_name]
        
        # Track execution time
        start_time = time.time()
        
        # Find path using selected strategy
        path = strategy.find_path(
            start, goal, grid, obstacle_manager, robot_id, carrying_weight
        )
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Update performance metrics
        self._update_performance_metrics(
            strategy_name, path, execution_time, start, goal, carrying_weight
        )
        
        return path
    
    def _update_performance_metrics(self, 
                                  strategy_name: str, 
                                  path: List[Tuple[int, int]], 
                                  execution_time: float,
                                  start: Tuple[int, int],
                                  goal: Tuple[int, int],
                                  carrying_weight: int):
        """
        Update performance metrics for the strategy
        
        Args:
            strategy_name: Name of the strategy used
            path: The path found (empty if no path)
            execution_time: Time taken to find the path
            start: Starting position
            goal: Goal position
            carrying_weight: Weight being carried
        """
        # Get context hash
        context = self._get_context_hash(start, goal, carrying_weight)
        
        # Update usage count
        self.strategy_performance[strategy_name]['used_count'] += 1
        
        # Update execution time history (keeping last 10)
        self.execution_times[strategy_name].append(execution_time)
        if len(self.execution_times[strategy_name]) > 10:
            self.execution_times[strategy_name].pop(0)
        
        # Update path quality metrics
        success = len(path) > 0
        self.path_successes[strategy_name].append(success)
        
        if success:
            self.path_lengths[strategy_name].append(len(path))
            if len(self.path_lengths[strategy_name]) > 10:
                self.path_lengths[strategy_name].pop(0)
        
        # Keep only the last 20 success/failure records
        if len(self.path_successes[strategy_name]) > 20:
            self.path_successes[strategy_name].pop(0)
        
        # Calculate performance metrics
        
        # Success rate (last 20 attempts)
        if self.path_successes[strategy_name]:
            success_rate = sum(self.path_successes[strategy_name]) / len(self.path_successes[strategy_name])
        else:
            success_rate = 0.5  # Default
        
        # Speed (normalized by average over all strategies)
        if self.execution_times[strategy_name]:
            avg_time = sum(self.execution_times[strategy_name]) / len(self.execution_times[strategy_name])
            
            # Get average times for all strategies
            all_times = []
            for strat, times in self.execution_times.items():
                if times:
                    all_times.append(sum(times) / len(times))
            
            if all_times:
                avg_all_time = sum(all_times) / len(all_times)
                speed = min(1.0, avg_all_time / (avg_time + 0.001))  # 0-1 scale, higher is better
            else:
                speed = 0.5  # Default
        else:
            speed = 0.5  # Default
        
        # Path quality (path length relative to Manhattan distance)
        path_quality = 0.5  # Default
        if success:
            manhattan_dist = abs(start[0] - goal[0]) + abs(start[1] - goal[1])
            # Perfect path ratio would be ~1.0-1.4 (direct path vs diagonal)
            # Higher ratio means less optimal path
            if manhattan_dist > 0:
                path_ratio = len(path) / manhattan_dist
                # Normalize to 0-1 scale, where 1.0 is perfect
                path_quality = max(0, min(1.0, 2.0 - (path_ratio / 1.5)))
        
        # Update strategy performance
        self.strategy_performance[strategy_name]['success_rate'] = success_rate
        self.strategy_performance[strategy_name]['speed'] = speed
        self.strategy_performance[strategy_name]['path_quality'] = path_quality
        
        # Update context-specific performance
        if context not in self.context_performance:
            self.context_performance[context] = {}
        
        # Calculate overall score for this strategy in this context
        overall_score = success_rate * 0.6 + speed * 0.2 + path_quality * 0.2
        
        # Update with moving average
        if strategy_name in self.context_performance[context]:
            old_score = self.context_performance[context][strategy_name]
            # 80% old, 20% new
            self.context_performance[context][strategy_name] = old_score * 0.8 + overall_score * 0.2
        else:
            self.context_performance[context][strategy_name] = overall_score
        
    def get_strategy_performance(self):
        """Get the current performance metrics for all strategies"""
        return {
            name: {
                'success_rate': data['success_rate'],
                'speed': data['speed'],
                'path_quality': data['path_quality'],
                'used_count': data['used_count']
            }
            for name, data in self.strategy_performance.items()
        }
    
    def get_strategy_usage_stats(self):
        """Get usage statistics for all strategies"""
        total_usage = sum(data['used_count'] for data in self.strategy_performance.values())
        
        if total_usage == 0:
            return {name: 0 for name in self.strategies.keys()}
            
        return {
            name: (data['used_count'] / total_usage) * 100
            for name, data in self.strategy_performance.items()
        }