"""
Updated PathFinder implementation with multiple strategy support
"""

from typing import List, Tuple, Optional, Dict, Set, Any

from core.models.grid import Grid
from simulation.pathfinding.strategies import PathStrategy, AStarStrategy
from simulation.pathfinding.advanced_strategies import AdaptiveDynamicAStarStrategy, ProximalPolicyDijkstraStrategy
from simulation.pathfinding.strategy_selector import PathStrategySelector


class PathFinder:
    """
    Enhanced PathFinder with support for multiple pathfinding strategies
    and intelligent strategy selection.
    """
    
    def __init__(self, grid: Grid, obstacle_manager=None):
        """
        Initialize the path finder
        
        Args:
            grid: The environment grid
            obstacle_manager: Optional obstacle manager for advanced obstacle handling
        """
        self.grid = grid
        self.obstacle_manager = obstacle_manager
        
        # Initialize individual strategies
        self.a_star = AStarStrategy()
        self.ad_star = AdaptiveDynamicAStarStrategy()
        self.pp_dijkstra = ProximalPolicyDijkstraStrategy()
        
        # Current active strategy (default: A*)
        self.current_strategy = self.a_star
        
        # Strategy selector for intelligently choosing algorithms
        self.strategy_selector = PathStrategySelector(grid, obstacle_manager)
        
        # Flag to enable/disable the strategy selector
        self.use_strategy_selector = True
    
    def set_strategy(self, strategy_name: str) -> None:
        """
        Manually set the pathfinding strategy to use
        
        Args:
            strategy_name: Name of the strategy ('astar', 'ad_star', or 'pp_dijkstra')
        """
        if strategy_name == 'astar':
            self.current_strategy = self.a_star
        elif strategy_name == 'ad_star':
            self.current_strategy = self.ad_star
        elif strategy_name == 'pp_dijkstra':
            self.current_strategy = self.pp_dijkstra
        else:
            raise ValueError(f"Unknown strategy: {strategy_name}")
            
        # Disable automatic strategy selection
        self.use_strategy_selector = False
    
    def enable_strategy_selector(self, enable: bool = True) -> None:
        """
        Enable or disable the automatic strategy selector
        
        Args:
            enable: True to enable, False to disable
        """
        self.use_strategy_selector = enable
    
    def find_path(self, 
                 start_pos: Tuple[int, int], 
                 goal_pos: Tuple[int, int],
                 robots: List[Any] = None,
                 robot_id: Optional[int] = None,
                 carrying_weight: int = 0) -> List[Tuple[int, int]]:
        """
        Find a path from start to goal
        
        Args:
            start_pos: Starting position (y, x)
            goal_pos: Goal position (y, x)
            robots: List of all robots (for collision avoidance)
            robot_id: ID of the robot requesting the path
            carrying_weight: Weight being carried (affects movement cost)
            
        Returns:
            List of positions forming a path from start to goal
        """
        if self.use_strategy_selector:
            # Use the strategy selector to find the best path
            return self.strategy_selector.find_path(
                start_pos, goal_pos, self.grid, self.obstacle_manager, robot_id, carrying_weight
            )
        else:
            # Use the manually selected strategy
            return self.current_strategy.find_path(
                start_pos, goal_pos, self.grid, self.obstacle_manager, robot_id, carrying_weight
            )
    
    def wait_or_navigate(self, robot, goal, robots, obstacle_pos) -> int:
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
        from core.models.grid import CellType
        if self.grid.get_cell(ox, oy) != CellType.TEMPORARY_OBSTACLE:
            return 0
        
        # Get the remaining lifespan of the obstacle
        lifespan = self.obstacle_manager.get_obstacle_remaining_lifespan(ox, oy)
        
        # If the obstacle will clear soon, waiting might be more efficient
        if lifespan <= 5:
            # Check if waiting is more efficient than finding an alternative path
            alt_path = self.find_path(
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
    
    def get_strategy_stats(self) -> Dict[str, Dict]:
        """
        Get statistics about pathfinding strategy performance
        
        Returns:
            Dict: Dictionary of strategy performance metrics
        """
        if self.use_strategy_selector:
            return self.strategy_selector.get_strategy_performance()
        else:
            return {"Current strategy": str(self.current_strategy.__class__.__name__)}
    
    def get_strategy_usage(self) -> Dict[str, float]:
        """
        Get the usage percentage of each strategy
        
        Returns:
            Dict: Dictionary of strategy usage percentages
        """
        if self.use_strategy_selector:
            return self.strategy_selector.get_strategy_usage_stats()
        else:
            return {"Current strategy": 100.0}
    
    def reset_strategy_data(self) -> None:
        """Reset all strategy performance data"""
        if hasattr(self.a_star, 'reset_cache'):
            self.a_star.reset_cache()
        
        if hasattr(self.ad_star, 'reset_cache'):
            self.ad_star.reset_cache()
        
        if hasattr(self.pp_dijkstra, 'reset'):
            self.pp_dijkstra.reset()
            
        # Create a new strategy selector
        self.strategy_selector = PathStrategySelector(self.grid, self.obstacle_manager)