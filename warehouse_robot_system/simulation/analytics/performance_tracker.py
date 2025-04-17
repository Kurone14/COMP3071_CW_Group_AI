"""
Tracks simulation performance metrics like time, steps, and delivery efficiency.
"""

import time
from typing import List, Dict, Any


class PerformanceTracker:
    """
    Tracks simulation performance metrics like time, steps, and delivery efficiency.
    """
    
    def __init__(self):
        """Initialize the performance tracker"""
        self.start_time = None
        self.end_time = None
        self.is_running = False
        
        self.total_robot_steps = 0
        self.total_items_delivered = 0
        
        # Additional tracking for robot activity
        self.active_robots = 0
        self.total_robots = 0
        self.robot_states = {}  # robot_id -> {'state': state, 'start_time': time}
    
    def start(self) -> None:
        """Start tracking performance"""
        self.start_time = time.time()
        self.is_running = True
        self.total_robot_steps = 0
        self.total_items_delivered = 0
        
        # Reset robot activity tracking
        self.active_robots = 0
        self.robot_states = {}
    
    def stop(self) -> None:
        """Stop tracking performance"""
        if self.is_running:
            self.end_time = time.time()
            self.is_running = False
    
    def reset(self) -> None:
        """Reset all tracking data"""
        self.start_time = None
        self.end_time = None
        self.is_running = False
        self.total_robot_steps = 0
        self.total_items_delivered = 0
        self.active_robots = 0
        self.robot_states = {}
    
    def add_steps(self, steps: int) -> None:
        """
        Add robot steps to total
        
        Args:
            steps: Number of steps to add
        """
        self.total_robot_steps += steps
    
    def add_delivered_items(self, count: int = 1) -> None:
        """
        Add delivered items to total
        
        Args:
            count: Number of delivered items to add
        """
        self.total_items_delivered += count

    def sync_delivered_items_count(self, total_items: int, remaining_items: int) -> None:
        """
        Sync the delivered items count with the actual simulation state
        
        Args:
            total_items: Total number of items in the simulation
            remaining_items: Number of remaining unpicked items
        """
        self.total_items_delivered = total_items - remaining_items
    
    def update_robot_states(self, robots: List[Any]) -> None:
        """
        Update robot activity states for utilization tracking
        
        Args:
            robots: List of robot objects
        """
        self.total_robots = len(robots)
        self.active_robots = 0
        
        current_time = time.time()
        
        for robot in robots:
            # Determine current state
            if robot.carrying_items:
                state = 'carrying'
                self.active_robots += 1
            elif robot.path:
                state = 'path_finding'
                self.active_robots += 1
            elif hasattr(robot, 'waiting') and robot.waiting:
                state = 'waiting'
                self.active_robots += 1
            else:
                state = 'idle'
            
            # Store state info
            if robot.id not in self.robot_states:
                self.robot_states[robot.id] = {
                    'state': state,
                    'start_time': current_time,
                    'durations': {
                        'idle': 0,
                        'carrying': 0,
                        'path_finding': 0,
                        'waiting': 0
                    }
                }
            elif self.robot_states[robot.id]['state'] != state:
                # Robot state changed - update duration counters
                old_state = self.robot_states[robot.id]['state']
                time_in_state = current_time - self.robot_states[robot.id]['start_time']
                self.robot_states[robot.id]['durations'][old_state] += time_in_state
                
                # Set new state
                self.robot_states[robot.id]['state'] = state
                self.robot_states[robot.id]['start_time'] = current_time
    
    def get_robot_utilization(self) -> float:
        """
        Get the current robot utilization percentage
        
        Returns:
            float: Percentage of robots that are active (0-100)
        """
        if self.total_robots == 0:
            return 0.0
        return (self.active_robots / self.total_robots) * 100.0
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time in seconds
        
        Returns:
            float: Elapsed time in seconds
        """
        if not self.start_time:
            return 0
        
        if self.is_running:
            return time.time() - self.start_time
        else:
            return self.end_time - self.start_time if self.end_time else 0
    
    def get_statistics(self) -> Dict[str, float]:
        """
        Get all performance statistics
        
        Returns:
            Dict: Dictionary with performance statistics
        """
        elapsed_time = self.get_elapsed_time()
        
        # Calculate time distribution across all robots
        total_time = 0
        total_idle_time = 0
        total_carrying_time = 0
        total_waiting_time = 0
        total_path_finding_time = 0
        
        current_time = time.time()
        
        for robot_id, state_info in self.robot_states.items():
            # Add current state duration
            time_in_current_state = current_time - state_info['start_time']
            state_durations = state_info['durations'].copy()
            state_durations[state_info['state']] += time_in_current_state
            
            # Sum all durations
            robot_total_time = sum(state_durations.values())
            total_time += robot_total_time
            
            # Add to category totals
            total_idle_time += state_durations['idle']
            total_carrying_time += state_durations['carrying']
            total_waiting_time += state_durations['waiting']
            total_path_finding_time += state_durations['path_finding']
        
        # Calculate percentages
        if total_time > 0:
            idle_percentage = (total_idle_time / total_time) * 100
            carrying_percentage = (total_carrying_time / total_time) * 100
            waiting_percentage = (total_waiting_time / total_time) * 100
            path_finding_percentage = (total_path_finding_time / total_time) * 100
        else:
            idle_percentage = 100.0
            carrying_percentage = 0.0
            waiting_percentage = 0.0
            path_finding_percentage = 0.0
        
        return {
            "elapsed_time": elapsed_time,
            "total_robot_steps": self.total_robot_steps,
            "total_items_delivered": self.total_items_delivered,
            "steps_per_second": self.total_robot_steps / elapsed_time if elapsed_time > 0 else 0,
            "items_per_minute": (self.total_items_delivered / elapsed_time) * 60 if elapsed_time > 0 else 0,
            "steps_per_item": self.total_robot_steps / self.total_items_delivered if self.total_items_delivered > 0 else 0,
            "robot_utilization": self.get_robot_utilization(),
            "idle_percentage": idle_percentage,
            "carrying_percentage": carrying_percentage,
            "waiting_percentage": waiting_percentage,
            "path_finding_percentage": path_finding_percentage
        }
    
    def format_statistics(self) -> List[str]:
        """
        Format statistics for display
        
        Returns:
            List[str]: Formatted statistics strings
        """
        stats = self.get_statistics()
        
        minutes = int(stats["elapsed_time"] // 60)
        seconds = int(stats["elapsed_time"] % 60)
        formatted_time = f"{minutes:02d}:{seconds:02d}"
        
        # Include robot utilization in the stats
        # This should now properly show the utilization in the main UI
        return [
            f"Time: {formatted_time}",
            f"Total steps: {stats['total_robot_steps']}",
            f"Items delivered: {stats['total_items_delivered']}",
            f"Robot utilization: {stats['robot_utilization']:.1f}%",  # Make sure this is included
            f"Steps/item: {stats['steps_per_item']:.1f}",
            f"Items/minute: {stats['items_per_minute']:.1f}"
        ]