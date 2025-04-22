"""
Obstacle legend component for the warehouse robot simulation GUI.
Displays a legend explaining different obstacle types.
"""

import tkinter as tk


class ObstacleLegend:
    """Legend explaining different obstacle types"""
    
    def __init__(self, parent):
        """
        Initialize the obstacle legend
        
        Args:
            parent: Parent widget
        """
        # Obstacle legend frame
        self.obstacle_legend_frame = tk.LabelFrame(parent, text="Obstacle Types")
        self.obstacle_legend_frame.pack(fill=tk.X, pady=5)
        
        # Create a frame for each obstacle type
        self._create_permanent_obstacle_legend()
        self._create_semi_permanent_obstacle_legend()
        self._create_temporary_obstacle_legend()
    
    def _create_permanent_obstacle_legend(self) -> None:
        """Create permanent obstacle legend item"""
        perm_frame = tk.Frame(self.obstacle_legend_frame)
        perm_frame.pack(fill=tk.X, pady=2)
        
        perm_sample = tk.Label(perm_frame, text="  ", background="gray", width=2)
        perm_sample.pack(side=tk.LEFT, padx=5)
        
        perm_name = tk.Label(perm_frame, text="Permanent", width=15, anchor="w")
        perm_name.pack(side=tk.LEFT, padx=5)
        
        perm_desc = tk.Label(perm_frame, text="Never disappears", anchor="w")
        perm_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_semi_permanent_obstacle_legend(self) -> None:
        """Create semi-permanent obstacle legend item"""
        semi_frame = tk.Frame(self.obstacle_legend_frame)
        semi_frame.pack(fill=tk.X, pady=2)
        
        semi_sample = tk.Label(semi_frame, text="  ", background="#8B4513", width=2)  # Brown
        semi_sample.pack(side=tk.LEFT, padx=5)
        
        semi_name = tk.Label(semi_frame, text="Semi-Permanent", width=15, anchor="w")
        semi_name.pack(side=tk.LEFT, padx=5)
        
        semi_desc = tk.Label(semi_frame, text="Disappears after ~30 cycles", anchor="w")
        semi_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def _create_temporary_obstacle_legend(self) -> None:
        """Create temporary obstacle legend item"""
        temp_frame = tk.Frame(self.obstacle_legend_frame)
        temp_frame.pack(fill=tk.X, pady=2)
        
        temp_sample = tk.Label(temp_frame, text="  ", background="#FFA500", width=2)  # Orange
        temp_sample.pack(side=tk.LEFT, padx=5)
        
        temp_name = tk.Label(temp_frame, text="Temporary", width=15, anchor="w")
        temp_name.pack(side=tk.LEFT, padx=5)
        
        temp_desc = tk.Label(temp_frame, text="Disappears after ~10 cycles", anchor="w")
        temp_desc.pack(side=tk.LEFT, fill=tk.X, expand=True)