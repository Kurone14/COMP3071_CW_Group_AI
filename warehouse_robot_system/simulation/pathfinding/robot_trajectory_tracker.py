"""
Enhanced robot trajectory tracking for visualization.
"""

from typing import Dict, List, Tuple, Optional, Set
import collections


class RobotTrajectoryTracker:
    """
    Tracks and stores robot movement trajectories for visualization.
    Shows the path from robot to current target (item or drop point).
    """
    
    def __init__(self, max_history: int = 50):
        """
        Initialize the trajectory tracker
        
        Args:
            max_history: Maximum number of positions to store per robot
        """
        self.max_history = max_history
        # Dict of robot_id -> deque of (x, y) positions
        self.trajectories: Dict[int, collections.deque] = {}
        # Dict of robot_id -> target type ('item' or 'drop')
        self.target_types: Dict[int, str] = {}
        # Dict of robot_id -> target position (x, y)
        self.target_positions: Dict[int, Tuple[int, int]] = {}
        self.enabled = True
        
    def reset(self):
        """Clear all trajectory data"""
        self.trajectories.clear()
        self.target_types.clear()
        self.target_positions.clear()
        
    def toggle(self, enable: Optional[bool] = None):
        """
        Toggle trajectory tracking on/off
        
        Args:
            enable: If provided, explicitly set enabled state
        """
        if enable is None:
            self.enabled = not self.enabled
        else:
            self.enabled = enable
            
    def is_enabled(self) -> bool:
        """Check if trajectory tracking is enabled"""
        return self.enabled
    
    def set_robot_target(self, robot_id: int, target_type: str, target_position: Tuple[int, int]):
        """
        Set the current target for a robot
        
        Args:
            robot_id: ID of the robot
            target_type: 'item' or 'drop'
            target_position: (x, y) coordinates of the target
        """
        if not self.enabled:
            return
            
        # Initialize trajectory for this robot if not exists
        if robot_id not in self.trajectories:
            self.trajectories[robot_id] = collections.deque(maxlen=self.max_history)
        
        # If target type or position changed, clear previous trajectory
        if (robot_id in self.target_types and self.target_types[robot_id] != target_type) or \
           (robot_id in self.target_positions and self.target_positions[robot_id] != target_position):
            self.trajectories[robot_id].clear()
        
        self.target_types[robot_id] = target_type
        self.target_positions[robot_id] = target_position
            
    def update_robot_position(self, robot_id: int, x: int, y: int):
        """
        Update a robot's position in the trajectory
        
        Args:
            robot_id: ID of the robot
            x, y: New position coordinates
        """
        if not self.enabled:
            return
            
        # Only track positions if we know the target
        if robot_id not in self.target_types:
            return
            
        # Initialize trajectory for this robot if not exists
        if robot_id not in self.trajectories:
            self.trajectories[robot_id] = collections.deque(maxlen=self.max_history)
            
        # Only add position if it's different from the last one
        if not self.trajectories[robot_id] or (x, y) != self.trajectories[robot_id][-1]:
            self.trajectories[robot_id].append((x, y))
            
    def get_trajectory(self, robot_id: int) -> List[Tuple[int, int]]:
        """
        Get the trajectory for a specific robot
        
        Args:
            robot_id: ID of the robot
            
        Returns:
            List of (x, y) coordinates representing the robot's trajectory
        """
        if robot_id in self.trajectories:
            return list(self.trajectories[robot_id])
        return []
    
    def get_target_position(self, robot_id: int) -> Optional[Tuple[int, int]]:
        """
        Get the target position for a robot
        
        Args:
            robot_id: ID of the robot
            
        Returns:
            Target position or None if not set
        """
        return self.target_positions.get(robot_id)
    
    def get_target_type(self, robot_id: int) -> Optional[str]:
        """
        Get the target type for a robot
        
        Args:
            robot_id: ID of the robot
            
        Returns:
            Target type ('item' or 'drop') or None if not set
        """
        return self.target_types.get(robot_id)
        
    def get_all_trajectories(self) -> Dict[int, List[Tuple[int, int]]]:
        """
        Get trajectories for all robots
        
        Returns:
            Dict mapping robot_id to list of (x, y) coordinates
        """
        return {robot_id: list(positions) for robot_id, positions in self.trajectories.items()}