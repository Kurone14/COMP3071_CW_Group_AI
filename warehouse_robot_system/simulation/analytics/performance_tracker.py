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
    
    def start(self) -> None:
        """Start tracking performance"""
        self.start_time = time.time()
        self.is_running = True
        self.total_robot_steps = 0
        self.total_items_delivered = 0
    
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
        
        return {
            "elapsed_time": elapsed_time,
            "total_robot_steps": self.total_robot_steps,
            "total_items_delivered": self.total_items_delivered,
            "steps_per_second": self.total_robot_steps / elapsed_time if elapsed_time > 0 else 0,
            "items_per_minute": (self.total_items_delivered / elapsed_time) * 60 if elapsed_time > 0 else 0,
            "steps_per_item": self.total_robot_steps / self.total_items_delivered if self.total_items_delivered > 0 else 0
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
        
        return [
            f"Time: {formatted_time}",
            f"Total steps: {stats['total_robot_steps']}",
            f"Items delivered: {stats['total_items_delivered']}",
            f"Steps/item: {stats['steps_per_item']:.1f}",
            f"Items/minute: {stats['items_per_minute']:.1f}"
        ]