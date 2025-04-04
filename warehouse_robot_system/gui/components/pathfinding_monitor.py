"""
Improved UI component for monitoring pathfinding strategy performance
with fixed table display that doesn't get cut off
"""

import tkinter as tk
from tkinter import ttk
import time
from typing import Dict, Any


class PathfindingMonitor:
    """
    UI component for monitoring and visualizing pathfinding strategy performance.
    Displays strategy usage, success rates, and allows for manual strategy selection.
    """
    
    def __init__(self, parent, path_finder):
        """
        Initialize the pathfinding monitor
        
        Args:
            parent: Parent widget
            path_finder: PathFinder instance
        """
        self.path_finder = path_finder
        
        # Create main frame
        self.frame = ttk.LabelFrame(parent, text="Pathfinding Strategy Monitor")
        self.frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Strategy selector
        self.strategy_frame = ttk.Frame(self.frame)
        self.strategy_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(self.strategy_frame, text="Strategy:").pack(side=tk.LEFT, padx=5)
        
        self.strategy_var = tk.StringVar()
        self.strategy_var.set("auto")
        
        strategy_options = ["auto", "astar", "ad_star", "pp_dijkstra"]
        self.strategy_dropdown = ttk.Combobox(
            self.strategy_frame, 
            textvariable=self.strategy_var,
            values=strategy_options,
            width=15,
            state="readonly"
        )
        self.strategy_dropdown.pack(side=tk.LEFT, padx=5)
        
        # Button frame to ensure buttons don't get cut off
        self.button_frame = ttk.Frame(self.strategy_frame)
        self.button_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)
        
        # Reset button
        self.reset_button = ttk.Button(
            self.button_frame,
            text="Reset Data",
            command=self._on_reset_data,
            width=10
        )
        self.reset_button.pack(side=tk.RIGHT, padx=5)
        
        # Apply button
        self.apply_button = ttk.Button(
            self.button_frame,
            text="Apply",
            command=self._on_apply_strategy,
            width=8
        )
        self.apply_button.pack(side=tk.RIGHT, padx=5)
        
        # Strategy status
        self.status_frame = ttk.Frame(self.frame)
        self.status_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create a more compact table with appropriate sizing
        columns = ("Algorithm", "Usage %", "Success %", "Speed", "Path Quality")
        self.tree = ttk.Treeview(
            self.status_frame,
            columns=columns,
            show="headings",
            height=3
        )
        
        # Set column headings with shorter text
        for col in columns:
            self.tree.heading(col, text=col)
        
        # Set column widths - adjusted to be much narrower
        self.tree.column("Algorithm", width=60, anchor=tk.W)  # Reduced from 90
        self.tree.column("Usage %", width=55, anchor=tk.CENTER)  # Reduced from 65
        self.tree.column("Success %", width=55, anchor=tk.CENTER)  # Reduced from 65
        self.tree.column("Speed", width=45, anchor=tk.CENTER)  # Reduced from 55
        self.tree.column("Path Quality", width=65, anchor=tk.CENTER)  # Reduced from 80

        # Algorithm display names (even shorter)
        algorithm_display = {
            "astar": "A*",
            "ad_star": "AD*",
            "pp_dijkstra": "PP-D"  # Shortened from PP-Dijkstra
        }
        
        # Add rows for each strategy with shortened display names
        for strategy_id, display_name in algorithm_display.items():
            self.tree.insert("", tk.END, iid=strategy_id, values=(display_name, "0.0%", "50.0%", "50.0%", "50.0%"))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.status_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Current strategy label
        self.current_strategy_var = tk.StringVar(value="Current: Auto (Strategy Selector)")
        self.current_strategy_label = ttk.Label(
            self.frame,
            textvariable=self.current_strategy_var,
            font=("Arial", 9, "bold")
        )
        self.current_strategy_label.pack(pady=5)
        
        # Last updated timestamp
        self.update_time_var = tk.StringVar(value="Last update: Never")
        self.update_time_label = ttk.Label(
            self.frame,
            textvariable=self.update_time_var,
            font=("Arial", 8)
        )
        self.update_time_label.pack(pady=2)
        
        # Algorithm names for display
        self.algorithm_names = {
            "astar": "A*",
            "ad_star": "AD*",
            "pp_dijkstra": "PP-Dijkstra"
        }
        
        # Set initial values
        self.update_monitor()
    
    def _on_apply_strategy(self):
        """Handle apply strategy button click"""
        strategy = self.strategy_var.get()
        
        if strategy == "auto":
            # Enable automatic strategy selection
            self.path_finder.enable_strategy_selector(True)
            self.current_strategy_var.set("Current: Auto (Strategy Selector)")
        else:
            # Set specific strategy
            self.path_finder.set_strategy(strategy)
            self.path_finder.enable_strategy_selector(False)
            
            # Update current strategy label with shortened names
            strategy_names = {
                "astar": "A* (Manual)",
                "ad_star": "AD* (Manual)",
                "pp_dijkstra": "PP-Dijkstra (Manual)"
            }
            self.current_strategy_var.set(f"Current: {strategy_names.get(strategy, strategy)}")
    
    def _on_reset_data(self):
        """Handle reset data button click"""
        # Reset strategy data
        self.path_finder.reset_strategy_data()
        
        # Update the display
        self.update_monitor()
    
    def update_monitor(self):
        """Update the monitor with current strategy statistics"""
        # Get strategy usage stats
        usage_stats = self.path_finder.get_strategy_usage()
        
        # Get strategy performance stats
        performance_stats = self.path_finder.get_strategy_stats()
        
        # Update tree view with current statistics
        for strategy in ["astar", "ad_star", "pp_dijkstra"]:
            usage = usage_stats.get(strategy, 0)
            
            if strategy in performance_stats:
                perf = performance_stats[strategy]
                success_rate = perf.get('success_rate', 0) * 100
                speed = perf.get('speed', 0) * 100
                path_quality = perf.get('path_quality', 0) * 100
                
                # Update tree item
                self.tree.item(
                    strategy,
                    values=(
                        self.algorithm_names.get(strategy, strategy),
                        f"{usage:.1f}%",
                        f"{success_rate:.1f}%",
                        f"{speed:.1f}%",
                        f"{path_quality:.1f}%"
                    )
                )
            else:
                # Default values if no stats available
                self.tree.item(
                    strategy,
                    values=(
                        self.algorithm_names.get(strategy, strategy),
                        "0.0%", 
                        "50.0%", 
                        "50.0%", 
                        "50.0%"
                    )
                )
        
        # Update timestamp
        current_time = time.strftime("%H:%M:%S")
        self.update_time_var.set(f"Last update: {current_time}")
    
    def get_frame(self):
        """Get the main frame for this component"""
        return self.frame