from typing import List, Tuple, Optional, Dict, Set, Any
from .strategies import PathStrategy, AStarStrategy
from core.models.grid import Grid


class PathFinder:
    """
    Main pathfinding class that uses different strategies to find paths
    and manages additional functionality like wait-vs-navigate decisions.
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
        self.strategy = AStarStrategy()  # Default to A* algorithm
    
    def set_strategy(self, strategy: PathStrategy) -> None:
        """Set the pathfinding strategy to use"""
        self.strategy = strategy
        
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
        return self.strategy.find_path(
            start_pos, 
            goal_pos, 
            self.grid,
            self.obstacle_manager,
            robot_id,
            carrying_weight
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