# warehouse_robot_system/simulation/analytics/metrics_calculator.py
import time
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
import pandas as pd

class SimulationMetricsCalculator:
    """
    Calculates and visualizes metrics for warehouse robot simulation.
    Provides data for report writing and results justification.
    """

    def __init__(self, simulation):
        """
        Initialize the metrics calculator

        Args:
            simulation: The main simulation instance
        """
        self.simulation = simulation
        self.metrics_history = {
            'timestamp': [],
            'robots_active': [],
            'items_remaining': [],
            'items_delivered': [],
            'total_steps': [],
            'robot_utilization': [],
            'strategy_usage': {},
            'obstacle_count': [],
            'temporary_obstacles': [],
            'semi_perm_obstacles': [],
            'permanent_obstacles': [],
            'path_lengths': [],
            'waiting_robots': [],
            'carrying_robots': []
        }

        # Start time for measuring duration
        self.start_time = None

        # Individual robot metrics
        self.robot_metrics = {}

        # *** ADDED: Reference to the visualization window ***
        self.metrics_window: Optional[tk.Toplevel] = None

        # Initialize metrics tracking
        self._init_robot_metrics()

    def _init_robot_metrics(self):
        """Initialize metrics tracking for each robot"""
        # Clear previous metrics first
        self.robot_metrics = {}
        for robot in self.simulation.robots:
            self.robot_metrics[robot.id] = {
                'total_steps': 0,
                'items_delivered': 0,
                'idle_time': 0,
                'carrying_time': 0,
                'waiting_time': 0,
                'path_finding_time': 0,
                'current_state': 'idle',
                'state_history': [],
                'path_lengths': [],
                'previous_position': (robot.x, robot.y)  # Track previous position
            }

    def start_tracking(self):
        """Start tracking metrics and close existing visualization window"""
        self.start_time = time.time()

        # Reset metrics history
        for key in self.metrics_history:
            if key != 'strategy_usage':
                self.metrics_history[key] = []

        self.metrics_history['strategy_usage'] = {}

        # Reset robot metrics
        self._init_robot_metrics()

        # *** ADDED: Close existing metrics window if open ***
        if self.metrics_window and tk.Toplevel.winfo_exists(self.metrics_window):
            print("MetricsCalculator: Closing existing visualization window due to reset.")
            self.metrics_window.destroy()
            self.metrics_window = None
        # *** END ADDED CODE ***

    def update_metrics(self):
        """Update all metrics for the current simulation state"""
        if not self.start_time:
            self.start_time = time.time()

        current_time = time.time() - self.start_time
        self.metrics_history['timestamp'].append(current_time)

        # Count active/idle/waiting robots
        active_robots = 0
        waiting_robots = 0
        carrying_robots = 0

        # Ensure robot_metrics is initialized for all current robots
        current_robot_ids = {robot.id for robot in self.simulation.robots}
        existing_metric_ids = set(self.robot_metrics.keys())

        # Add new robots
        for robot_id in current_robot_ids - existing_metric_ids:
             robot = next((r for r in self.simulation.robots if r.id == robot_id), None)
             if robot:
                 self.robot_metrics[robot_id] = {
                    'total_steps': 0, 'items_delivered': 0, 'idle_time': 0,
                    'carrying_time': 0, 'waiting_time': 0, 'path_finding_time': 0,
                    'current_state': 'idle', 'state_history': [], 'path_lengths': [],
                    'previous_position': (robot.x, robot.y)
                 }

        # Remove metrics for deleted robots
        for robot_id in existing_metric_ids - current_robot_ids:
            if robot_id in self.robot_metrics:
                del self.robot_metrics[robot_id]


        for robot in self.simulation.robots:
             # Skip if robot metrics somehow weren't initialized (safety check)
            if robot.id not in self.robot_metrics:
                continue

            # Check if robot has moved since last update
            current_pos = (robot.x, robot.y)
            previous_pos = self.robot_metrics[robot.id]['previous_position']
            # Update previous position for next cycle
            self.robot_metrics[robot.id]['previous_position'] = current_pos

            has_moved = previous_pos is not None and current_pos != previous_pos

            # Track steps
            self.robot_metrics[robot.id]['total_steps'] = robot.steps

            # Determine current state with improved logic
            current_state = self._determine_robot_state(robot, has_moved)
            last_state = self.robot_metrics[robot.id].get('current_state', 'idle')

            # Update state history only if state changed or first update
            if current_state != last_state or not self.robot_metrics[robot.id]['state_history']:
                 self.robot_metrics[robot.id]['current_state'] = current_state
                 self.robot_metrics[robot.id]['state_history'].append(current_state)


            # Count state durations (simplified: count occurrences per update cycle)
            if current_state == 'idle':
                self.robot_metrics[robot.id]['idle_time'] += 1
            elif current_state == 'carrying':
                self.robot_metrics[robot.id]['carrying_time'] += 1
                carrying_robots += 1
                # active_robots += 1 # Carrying robots are active - Handled below
            elif current_state == 'waiting':
                self.robot_metrics[robot.id]['waiting_time'] += 1
                waiting_robots += 1
                # active_robots += 1 # Waiting robots are considered active - Handled below
            elif current_state == 'path_finding':
                self.robot_metrics[robot.id]['path_finding_time'] += 1
                # active_robots += 1 # Path finding robots are active - Handled below

            # Track path lengths when path is assigned (and potentially changed)
            if robot.path and (not self.robot_metrics[robot.id]['path_lengths'] or len(robot.path) != self.robot_metrics[robot.id]['path_lengths'][-1]):
                 self.robot_metrics[robot.id]['path_lengths'].append(len(robot.path))


            # Count active robots (revised logic: not idle)
            if current_state != 'idle':
                active_robots += 1


        # Update global metrics
        self.metrics_history['robots_active'].append(active_robots)
        self.metrics_history['waiting_robots'].append(waiting_robots)
        self.metrics_history['carrying_robots'].append(carrying_robots)

        # Count items
        items_remaining = len([item for item in self.simulation.items if not item.picked])
        items_delivered = len(self.simulation.items) - items_remaining

        self.metrics_history['items_remaining'].append(items_remaining)
        self.metrics_history['items_delivered'].append(items_delivered)

        # Track total steps across all robots
        if self.simulation.performance_tracker:
            total_steps = self.simulation.performance_tracker.total_robot_steps
            self.metrics_history['total_steps'].append(total_steps)
        else:
            # Fallback if no performance tracker
            total_steps = sum(self.robot_metrics[rid]['total_steps'] for rid in self.robot_metrics)
            self.metrics_history['total_steps'].append(total_steps)

        # Track robot utilization (percentage of robots active)
        utilization = (active_robots / max(1, len(self.simulation.robots))) * 100
        self.metrics_history['robot_utilization'].append(utilization)

        # Track strategy usage if available
        if hasattr(self.simulation.path_finder, 'get_strategy_usage'):
            strategy_usage = self.simulation.path_finder.get_strategy_usage()

            for strategy, percentage in strategy_usage.items():
                if strategy not in self.metrics_history['strategy_usage']:
                    self.metrics_history['strategy_usage'][strategy] = []
                 # Ensure data aligns with timestamps
                target_len = len(self.metrics_history['timestamp'])
                current_len = len(self.metrics_history['strategy_usage'][strategy])
                if current_len < target_len:
                     # Pad with last known value or 0
                     padding_value = self.metrics_history['strategy_usage'][strategy][-1] if current_len > 0 else 0
                     self.metrics_history['strategy_usage'][strategy].extend([padding_value] * (target_len - 1 - current_len))
                     self.metrics_history['strategy_usage'][strategy].append(percentage)
                elif current_len == target_len:
                     self.metrics_history['strategy_usage'][strategy][-1] = percentage # Update last value


        # Count obstacles by type
        permanent_count = 0
        temporary_count = 0
        semi_perm_count = 0

        for y in range(self.simulation.grid.height):
            for x in range(self.simulation.grid.width):
                cell_type = self.simulation.grid.get_cell(x, y)
                if cell_type == 1:  # PERMANENT_OBSTACLE
                    permanent_count += 1
                elif cell_type == 5:  # TEMPORARY_OBSTACLE
                    temporary_count += 1
                elif cell_type == 6:  # SEMI_PERMANENT_OBSTACLE
                    semi_perm_count += 1

        self.metrics_history['obstacle_count'].append(permanent_count + temporary_count + semi_perm_count)
        self.metrics_history['permanent_obstacles'].append(permanent_count)
        self.metrics_history['temporary_obstacles'].append(temporary_count)
        self.metrics_history['semi_perm_obstacles'].append(semi_perm_count)

        # Track average path length for active robots
        active_path_lengths = [len(robot.path) for robot in self.simulation.robots if robot.path]
        if active_path_lengths:
            avg_path_length = sum(active_path_lengths) / len(active_path_lengths)
        else:
            avg_path_length = 0
        self.metrics_history['path_lengths'].append(avg_path_length)

    def _determine_robot_state(self, robot, has_moved):
        """
        Determine the current state of a robot with improved logic

        Args:
            robot: The robot object
            has_moved: Boolean indicating if robot moved since last update

        Returns:
            str: Current state ('idle', 'waiting', 'carrying', 'path_finding')
        """
        # Check for waiting state first (highest priority)
        if hasattr(robot, 'waiting') and robot.waiting:
            return 'waiting'

        # Check for carrying state
        if robot.carrying_items:
            # If robot has a path or just moved, it's actively carrying
            if robot.path or has_moved:
                 return 'carrying'
            else:
                 # Carrying but no path and hasn't moved -> likely waiting or stuck
                 # Check if near drop point
                 if self.simulation.grid.drop_point:
                     drop_x, drop_y = self.simulation.grid.drop_point
                     # If at drop point or adjacent, consider it 'carrying' (at destination)
                     if abs(robot.x - drop_x) <= 1 and abs(robot.y - drop_y) <= 1:
                         return 'carrying'
                 # Otherwise, consider it waiting/stuck
                 return 'waiting'


        # Check for path finding state (not carrying items but has a path)
        if robot.path:
            # If robot moved, it's actively path finding
            if has_moved:
                return 'path_finding'
            else:
                # Has path but hasn't moved -> likely waiting for collision/obstacle
                return 'waiting'

        # Default to idle state (no path, not carrying items)
        return 'idle'

    def calculate_overall_metrics(self):
        """
        Calculate overall metrics for the entire simulation

        Returns:
            dict: Dictionary of overall metrics
        """
        # (Implementation remains the same as provided previously)
        if not self.metrics_history['timestamp']:
            return {
                'duration': 0, 'total_items_delivered': 0, 'total_steps': 0,
                'avg_robot_utilization': 0, 'steps_per_item': 0, 'items_per_minute': 0,
                'avg_idle_percentage': 100.0, 'avg_carrying_percentage': 0.0, 'avg_waiting_percentage': 0.0,
                'strategy_distribution': {}, 'avg_obstacles': 0, 'avg_temp_obstacles': 0,
                'avg_semi_perm_obstacles': 0, 'avg_perm_obstacles': 0
            }

        duration = self.metrics_history['timestamp'][-1]
        total_items_delivered = self.metrics_history['items_delivered'][-1] if self.metrics_history['items_delivered'] else 0
        total_steps = self.metrics_history['total_steps'][-1] if self.metrics_history['total_steps'] else 0
        avg_robot_utilization = np.mean(self.metrics_history['robot_utilization']) if self.metrics_history['robot_utilization'] else 0
        steps_per_item = total_steps / max(1, total_items_delivered)
        items_per_minute = (total_items_delivered / max(1e-6, duration)) * 60

        total_time_slices = 0
        total_idle_time = 0
        total_carrying_time = 0
        total_waiting_time = 0
        total_path_finding_time = 0

        for robot_id, metrics in self.robot_metrics.items():
             time_slices = metrics['idle_time'] + metrics['carrying_time'] + metrics['waiting_time'] + metrics.get('path_finding_time', 0)
             if time_slices > 0:
                 total_time_slices += time_slices
                 total_idle_time += metrics['idle_time']
                 total_carrying_time += metrics['carrying_time']
                 total_waiting_time += metrics['waiting_time']
                 total_path_finding_time += metrics.get('path_finding_time', 0)


        if total_time_slices > 0:
            avg_idle_percentage = (total_idle_time / total_time_slices) * 100
            avg_carrying_percentage = (total_carrying_time / total_time_slices) * 100
            avg_waiting_percentage = (total_waiting_time / total_time_slices) * 100
        else:
            avg_idle_percentage = 100.0
            avg_carrying_percentage = 0.0
            avg_waiting_percentage = 0.0

        strategy_distribution = {}
        if self.metrics_history['strategy_usage']:
            for strategy, usages in self.metrics_history['strategy_usage'].items():
                if usages: # Check if list is not empty
                     strategy_distribution[strategy] = np.mean(usages)


        avg_obstacles = np.mean(self.metrics_history['obstacle_count']) if self.metrics_history['obstacle_count'] else 0
        avg_temp_obstacles = np.mean(self.metrics_history['temporary_obstacles']) if self.metrics_history['temporary_obstacles'] else 0
        avg_semi_perm_obstacles = np.mean(self.metrics_history['semi_perm_obstacles']) if self.metrics_history['semi_perm_obstacles'] else 0
        avg_perm_obstacles = np.mean(self.metrics_history['permanent_obstacles']) if self.metrics_history['permanent_obstacles'] else 0


        return {
            'duration': duration, 'total_items_delivered': total_items_delivered, 'total_steps': total_steps,
            'avg_robot_utilization': avg_robot_utilization, 'steps_per_item': steps_per_item, 'items_per_minute': items_per_minute,
            'avg_idle_percentage': avg_idle_percentage, 'avg_carrying_percentage': avg_carrying_percentage, 'avg_waiting_percentage': avg_waiting_percentage,
            'strategy_distribution': strategy_distribution, 'avg_obstacles': avg_obstacles, 'avg_temp_obstacles': avg_temp_obstacles,
            'avg_semi_perm_obstacles': avg_semi_perm_obstacles, 'avg_perm_obstacles': avg_perm_obstacles
        }


    def calculate_robot_efficiency(self):
        """
        Calculate efficiency metrics for individual robots

        Returns:
            dict: Dictionary of robot efficiency metrics by robot ID
        """
        # (Implementation remains the same as provided previously)
        robot_efficiency = {}
        for robot_id, metrics in self.robot_metrics.items():
            total_time = metrics['idle_time'] + metrics['carrying_time'] + metrics['waiting_time'] + metrics.get('path_finding_time', 0)
            if total_time == 0: continue

            efficiency = {
                'total_steps': metrics['total_steps'],
                'items_delivered': metrics['items_delivered'], # Note: This needs to be tracked per robot
                'idle_percentage': (metrics['idle_time'] / total_time) * 100,
                'carrying_percentage': (metrics['carrying_time'] / total_time) * 100,
                'waiting_percentage': (metrics['waiting_time'] / total_time) * 100,
                'path_finding_percentage': (metrics.get('path_finding_time', 0) / total_time) * 100,
                'path_lengths': metrics['path_lengths']
            }
            efficiency['avg_path_length'] = np.mean(metrics['path_lengths']) if metrics['path_lengths'] else 0
            robot_efficiency[robot_id] = efficiency
        return robot_efficiency


    def calculate_obstacle_metrics(self):
        """
        Calculate metrics related to obstacles

        Returns:
            dict: Dictionary of obstacle-related metrics
        """
        # (Implementation remains the same as provided previously)
        if not self.metrics_history['timestamp']:
             return {'obstacle_count_over_time': [], 'obstacle_type_distribution': {}, 'obstacle_density': 0}

        obstacle_counts = list(zip(self.metrics_history['timestamp'], self.metrics_history['obstacle_count'])) if self.metrics_history['obstacle_count'] else []

        total_perm = sum(self.metrics_history['permanent_obstacles'])
        total_temp = sum(self.metrics_history['temporary_obstacles'])
        total_semi = sum(self.metrics_history['semi_perm_obstacles'])
        total_obstacles = total_perm + total_temp + total_semi

        if total_obstacles > 0:
            type_distribution = {
                'permanent': total_perm / total_obstacles,
                'temporary': total_temp / total_obstacles,
                'semi_permanent': total_semi / total_obstacles
            }
        else:
             type_distribution = {'permanent': 0, 'temporary': 0, 'semi_permanent': 0}

        grid_size = self.simulation.grid.width * self.simulation.grid.height
        avg_obstacle_count = np.mean(self.metrics_history['obstacle_count']) if self.metrics_history['obstacle_count'] else 0
        obstacle_density = (avg_obstacle_count / max(1, grid_size)) * 100

        return {
            'obstacle_count_over_time': obstacle_counts,
            'obstacle_type_distribution': type_distribution,
            'obstacle_density': obstacle_density
        }


    def calculate_path_metrics(self):
        """
        Calculate metrics related to pathfinding

        Returns:
            dict: Dictionary of path-related metrics
        """
        # (Implementation remains the same as provided previously)
        strategy_performance = {}
        if hasattr(self.simulation.path_finder, 'get_strategy_performance'):
             strategy_performance = self.simulation.path_finder.get_strategy_performance()

        path_lengths = list(zip(self.metrics_history['timestamp'], self.metrics_history['path_lengths'])) if self.metrics_history['path_lengths'] else []
        waiting_events = sum(1 for count in self.metrics_history['waiting_robots'] if count > 0) if self.metrics_history['waiting_robots'] else 0

        return {'strategy_performance': strategy_performance, 'path_lengths': path_lengths, 'waiting_events': waiting_events}


    def generate_metrics_report(self):
        """
        Generate a comprehensive metrics report for the simulation

        Returns:
            str: Formatted report text
        """
        # (Implementation remains the same as provided previously)
        overall = self.calculate_overall_metrics()
        robot_eff = self.calculate_robot_efficiency()
        obstacle_metrics = self.calculate_obstacle_metrics()
        path_metrics = self.calculate_path_metrics()

        report = ["# Warehouse Robot Simulation Metrics Report", f"Simulation duration: {overall['duration']:.2f} seconds\n"]
        report.append("## Overall Performance")
        report.append(f"Total items delivered: {overall['total_items_delivered']}")
        report.append(f"Total robot steps: {overall['total_steps']}")
        report.append(f"Average robot utilization: {overall['avg_robot_utilization']:.2f}%")
        report.append(f"Steps per item: {overall['steps_per_item']:.2f}")
        report.append(f"Items delivered per minute: {overall['items_per_minute']:.2f}\n")

        report.append("## Robot Time Distribution")
        report.append(f"Average idle time: {overall['avg_idle_percentage']:.2f}%")
        report.append(f"Average carrying time: {overall['avg_carrying_percentage']:.2f}%")
        report.append(f"Average waiting time: {overall['avg_waiting_percentage']:.2f}%\n")

        report.append("## Pathfinding")
        if path_metrics['strategy_performance']:
             report.append("Strategy performance:")
             for strategy, perf in path_metrics['strategy_performance'].items():
                 report.append(f"  - {strategy}: Success rate: {perf.get('success_rate', 0)*100:.1f}%, Speed: {perf.get('speed',0)*100:.1f}%, Path quality: {perf.get('path_quality', 0)*100:.1f}%") # Adjusted formatting
        report.append(f"Waiting events due to obstacles: {path_metrics['waiting_events']}\n")

        report.append("## Obstacle Metrics")
        report.append(f"Average obstacle count: {overall['avg_obstacles']:.2f}")
        report.append(f"Obstacle density: {obstacle_metrics['obstacle_density']:.2f}%")
        report.append("Obstacle type distribution:")
        for obs_type, percentage in obstacle_metrics['obstacle_type_distribution'].items():
            report.append(f"  - {obs_type}: {percentage*100:.1f}%")
        report.append("")

        report.append("## Individual Robot Performance")
        for robot_id, metrics in robot_eff.items():
            report.append(f"Robot {robot_id}:")
            report.append(f"  - Total steps: {metrics['total_steps']}")
            report.append(f"  - Average path length: {metrics.get('avg_path_length', 0):.2f}")
            report.append(f"  - Idle time: {metrics['idle_percentage']:.2f}%")
            report.append(f"  - Carrying time: {metrics['carrying_percentage']:.2f}%")
            report.append(f"  - Waiting time: {metrics['waiting_percentage']:.2f}%")

        return "\n".join(report)


    def export_metrics_to_csv(self, filename: str):
        """
        Export metrics history to CSV file

        Args:
            filename: Name of the CSV file to create
        """
        # (Implementation remains the same as provided previously)
        # Create a DataFrame ensuring all lists have the same length
        max_len = len(self.metrics_history['timestamp'])
        data = {}
        for key, values in self.metrics_history.items():
             if key == 'strategy_usage':
                 for strat_key, strat_values in values.items():
                     # Pad strategy usage lists
                     padded_values = strat_values + [strat_values[-1] if strat_values else 0] * (max_len - len(strat_values))
                     data[f'strategy_{strat_key}'] = padded_values[:max_len] # Ensure exact length
             else:
                 # Pad other lists
                 padded_values = values + [values[-1] if values else 0] * (max_len - len(values))
                 data[key] = padded_values[:max_len] # Ensure exact length


        try:
             df = pd.DataFrame(data)
             df.to_csv(filename, index=False)
             print(f"Exported metrics to {filename}")
             # Use messagebox if Tkinter is available (might be better in GUI context)
             try:
                 from tkinter import messagebox
                 messagebox.showinfo("Export Successful", f"Metrics exported to {filename}")
             except ImportError:
                 pass # Handle cases where tkinter is not available or not desired
        except ValueError as e:
             print(f"Error creating DataFrame for CSV export: {e}")
             print("Lengths of arrays:")
             for key, values in data.items():
                 print(f"  {key}: {len(values)}")
             # Consider showing an error message to the user via messagebox if appropriate


    def create_visualization_window(self):
        """
        Create a window with visualizations of the metrics
        """
        # *** ADDED: Check if window already exists ***
        if self.metrics_window and tk.Toplevel.winfo_exists(self.metrics_window):
            print("MetricsCalculator: Visualization window already open. Bringing to front.")
            self.metrics_window.lift()
            return
        # *** END ADDED CODE ***

        # Create a toplevel window
        metrics_window = tk.Toplevel()
        metrics_window.title("Simulation Metrics Visualization")
        metrics_window.geometry("900x700")

        # *** ADDED: Store reference and handle closing ***
        self.metrics_window = metrics_window
        def on_close():
            print("MetricsCalculator: Visualization window closed by user.")
            self.metrics_window.destroy()
            self.metrics_window = None
        metrics_window.protocol("WM_DELETE_WINDOW", on_close)
        # *** END ADDED CODE ***

        # Create a notebook with tabs
        notebook = ttk.Notebook(metrics_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create tabs
        self._create_overview_tab(notebook)
        self._create_robots_tab(notebook)
        self._create_obstacles_tab(notebook)
        self._create_pathfinding_tab(notebook)

        # Add export button
        export_frame = tk.Frame(metrics_window)
        export_frame.pack(fill=tk.X, padx=10, pady=5)

        export_button = tk.Button(
            export_frame,
            text="Export to CSV",
            command=lambda: self.export_metrics_to_csv("simulation_metrics.csv")
        )
        export_button.pack(side=tk.RIGHT, padx=5, pady=5)

        report_button = tk.Button(
            export_frame,
            text="Generate Report",
            command=self._show_metrics_report
        )
        report_button.pack(side=tk.RIGHT, padx=5, pady=5)

    # --- Methods for creating tabs remain the same ---
    def _create_overview_tab(self, notebook):
        """Create the overview tab with main metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Overview")

        fig, axes = plt.subplots(2, 2, figsize=(8, 6)) # Use subplots for better control
        axes = axes.ravel() # Flatten axes array

        # Plot 1: Items remaining vs delivered
        ax = axes[0]
        if self.metrics_history['timestamp'] and self.metrics_history['items_remaining'] and self.metrics_history['items_delivered']:
            min_len = min(len(self.metrics_history['timestamp']), len(self.metrics_history['items_remaining']), len(self.metrics_history['items_delivered']))
            ax.plot(self.metrics_history['timestamp'][:min_len], self.metrics_history['items_remaining'][:min_len], label='Remaining', color='red')
            ax.plot(self.metrics_history['timestamp'][:min_len], self.metrics_history['items_delivered'][:min_len], label='Delivered', color='green')
            ax.legend()
            ax.set_title('Item Status Over Time')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Count')
        else:
            ax.set_title('Item Status (No data)')

        # Plot 2: Robot utilization
        ax = axes[1]
        if self.metrics_history['timestamp'] and self.metrics_history['robot_utilization']:
             min_len = min(len(self.metrics_history['timestamp']), len(self.metrics_history['robot_utilization']))
             ax.plot(self.metrics_history['timestamp'][:min_len], self.metrics_history['robot_utilization'][:min_len], color='blue')
             ax.set_title('Robot Utilization')
             ax.set_xlabel('Time (s)')
             ax.set_ylabel('Utilization (%)')
             ax.set_ylim(0, 100)
        else:
             ax.set_title('Robot Utilization (No data)')


        # Plot 3: Total steps over time
        ax = axes[2]
        if self.metrics_history['timestamp'] and self.metrics_history['total_steps']:
             min_len = min(len(self.metrics_history['timestamp']), len(self.metrics_history['total_steps']))
             ax.plot(self.metrics_history['timestamp'][:min_len], self.metrics_history['total_steps'][:min_len], color='purple')
             ax.set_title('Total Steps Over Time')
             ax.set_xlabel('Time (s)')
             ax.set_ylabel('Steps')
        else:
             ax.set_title('Total Steps (No data)')


        # Plot 4: Strategy usage if available
        ax = axes[3]
        if self.metrics_history['strategy_usage'] and any(self.metrics_history['strategy_usage'].values()):
             plotted = False
             min_ts_len = len(self.metrics_history['timestamp'])
             for strategy, usage in self.metrics_history['strategy_usage'].items():
                 if usage:
                     # Ensure usage data aligns with timestamp length
                     current_len = len(usage)
                     plot_len = min(min_ts_len, current_len)
                     if plot_len > 0:
                         ax.plot(self.metrics_history['timestamp'][:plot_len], usage[:plot_len], label=strategy)
                         plotted = True
             if plotted:
                 ax.legend()
                 ax.set_title('Pathfinding Strategy Usage')
                 ax.set_xlabel('Time (s)')
                 ax.set_ylabel('Usage (%)')
                 ax.set_ylim(0, 100) # Ensure consistent scale
             else:
                 ax.set_title('Strategy Usage (No valid data)')
        else:
             ax.set_title('Strategy Usage (No data)')


        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_obstacles_tab(self, notebook):
        """Create tab with obstacle metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Obstacles")

        obstacle_metrics = self.calculate_obstacle_metrics()

        metrics_frame = ttk.LabelFrame(tab, text="Obstacle Metrics")
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)

        metrics_text = f"Obstacle Density: {obstacle_metrics['obstacle_density']:.2f}%\n\nObstacle Type Distribution:\n"
        for obs_type, percentage in obstacle_metrics['obstacle_type_distribution'].items():
            metrics_text += f"- {obs_type}: {percentage*100:.1f}%\n"

        metrics_label = tk.Label(metrics_frame, text=metrics_text, justify=tk.LEFT)
        metrics_label.pack(padx=10, pady=10)

        fig, axes = plt.subplots(2, 1, figsize=(8, 6)) # Adjusted layout to 2 rows

        # Plot 1: Obstacle count over time
        ax = axes[0]
        if self.metrics_history['timestamp'] and self.metrics_history['obstacle_count']:
             times = self.metrics_history['timestamp']
             min_len = len(times)
             # Ensure all obstacle lists have the same length as timestamp
             obs_count = self.metrics_history['obstacle_count'][:min_len]
             perm_obs = self.metrics_history['permanent_obstacles'][:min_len]
             semi_obs = self.metrics_history['semi_perm_obstacles'][:min_len]
             temp_obs = self.metrics_history['temporary_obstacles'][:min_len]

             if len(obs_count) == min_len: ax.plot(times, obs_count, label='Total', color='blue')
             if len(perm_obs) == min_len: ax.plot(times, perm_obs, label='Permanent', color='black')
             if len(semi_obs) == min_len: ax.plot(times, semi_obs, label='Semi-Permanent', color='brown')
             if len(temp_obs) == min_len: ax.plot(times, temp_obs, label='Temporary', color='orange')

             ax.legend()
             ax.set_title('Obstacle Count Over Time')
             ax.set_xlabel('Time (s)')
             ax.set_ylabel('Count')
        else:
             ax.set_title('Obstacle Count (No data)')


        # Plot 2: Obstacle type distribution (pie chart)
        ax = axes[1]
        if obstacle_metrics['obstacle_type_distribution'] and sum(obstacle_metrics['obstacle_type_distribution'].values()) > 0:
            labels = list(obstacle_metrics['obstacle_type_distribution'].keys())
            sizes = [val * 100 for val in obstacle_metrics['obstacle_type_distribution'].values()]
            colors = {'permanent': 'black', 'semi_permanent': 'brown', 'temporary': 'orange'}
            pie_colors = [colors.get(label, 'gray') for label in labels] # Use defined colors

            ax.pie(sizes, labels=labels, colors=pie_colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Avg Obstacle Type Distribution')
        else:
            ax.set_title('Obstacle Distribution (No data)')

        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_pathfinding_tab(self, notebook):
        """Create tab with pathfinding metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Pathfinding")

        metrics_frame = ttk.LabelFrame(tab, text="Pathfinding Metrics")
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        path_metrics = self.calculate_path_metrics()
        metrics_text = f"Waiting Events (due to temp obstacles): {path_metrics['waiting_events']}"
        metrics_label = tk.Label(metrics_frame, text=metrics_text, justify=tk.LEFT)
        metrics_label.pack(padx=10, pady=10)


        fig, axes = plt.subplots(1, 2, figsize=(8, 4)) # 1 row, 2 cols

        # Plot 1: Strategy usage over time
        ax = axes[0]
        if self.metrics_history['strategy_usage'] and any(self.metrics_history['strategy_usage'].values()):
             plotted = False
             min_ts_len = len(self.metrics_history['timestamp'])
             for strategy, usage in self.metrics_history['strategy_usage'].items():
                 if usage:
                     plot_len = min(min_ts_len, len(usage))
                     if plot_len > 0:
                         ax.plot(self.metrics_history['timestamp'][:plot_len], usage[:plot_len], label=strategy)
                         plotted = True
             if plotted:
                 ax.legend()
                 ax.set_title('Strategy Usage Over Time')
                 ax.set_xlabel('Time (s)')
                 ax.set_ylabel('Usage (%)')
                 ax.set_ylim(0, 100)
             else:
                  ax.set_title('Strategy Usage (No valid data)')
        else:
             ax.set_title('Strategy Usage (No data)')

        # Plot 2: Average Path Length Over Time
        ax = axes[1]
        if self.metrics_history['timestamp'] and self.metrics_history['path_lengths']:
             min_len = min(len(self.metrics_history['timestamp']), len(self.metrics_history['path_lengths']))
             # Filter out zero path lengths before plotting mean
             valid_paths = [p for p in self.metrics_history['path_lengths'][:min_len] if p > 0]
             if valid_paths:
                 # Calculate moving average for smoother plot
                 window_size = 5
                 path_series = pd.Series(self.metrics_history['path_lengths'][:min_len])
                 moving_avg = path_series.rolling(window=window_size, min_periods=1).mean()
                 ax.plot(self.metrics_history['timestamp'][:min_len], moving_avg, color='teal')
                 ax.set_title('Avg Path Length Over Time (Moving Avg)')
                 ax.set_xlabel('Time (s)')
                 ax.set_ylabel('Avg Steps')
             else:
                 ax.set_title('Avg Path Length (No valid paths)')
        else:
             ax.set_title('Avg Path Length (No data)')


        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _show_metrics_report(self):
        """Show metrics report in a new window"""
        # (Implementation remains the same as provided previously)
        report_window = tk.Toplevel()
        report_window.title("Simulation Metrics Report")
        report_window.geometry("800x600")

        report_text = tk.Text(report_window, wrap=tk.WORD, padx=10, pady=10, font=("Courier New", 9)) # Use fixed-width font
        scrollbar = tk.Scrollbar(report_text, command=report_text.yview)
        report_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        report_text.pack(fill=tk.BOTH, expand=True)


        report = self.generate_metrics_report()
        report_text.insert(tk.END, report)
        report_text.config(state=tk.DISABLED)

    def _create_robots_tab(self, notebook):
        """Create tab with robot-specific metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Robots")

        robot_efficiency = self.calculate_robot_efficiency()

        table_frame = ttk.LabelFrame(tab, text="Robot Performance Summary")
        table_frame.pack(fill=tk.X, padx=10, pady=10) # Changed to fill X only

        columns = ("Robot ID", "Total Steps", "Avg Path Len", "Idle %", "Carrying %", "Waiting %", "PathFind %") # Shortened headers
        tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=5) # Fixed height

        # Set column headings and widths
        tree.column("Robot ID", width=60, anchor=tk.CENTER)
        tree.column("Total Steps", width=80, anchor=tk.CENTER)
        tree.column("Avg Path Len", width=80, anchor=tk.CENTER)
        tree.column("Idle %", width=80, anchor=tk.CENTER)
        tree.column("Carrying %", width=80, anchor=tk.CENTER)
        tree.column("Waiting %", width=80, anchor=tk.CENTER)
        tree.column("PathFind %", width=80, anchor=tk.CENTER)

        for col in columns:
            tree.heading(col, text=col)

        # Add data
        for robot_id, metrics in robot_efficiency.items():
            tree.insert("", "end", values=(
                robot_id,
                metrics['total_steps'],
                f"{metrics.get('avg_path_length', 0):.1f}", # Adjusted precision
                f"{metrics['idle_percentage']:.1f}", # Adjusted precision
                f"{metrics['carrying_percentage']:.1f}", # Adjusted precision
                f"{metrics['waiting_percentage']:.1f}", # Adjusted precision
                f"{metrics.get('path_finding_percentage', 0):.1f}" # Adjusted precision
            ))

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.X, expand=True) # Changed to fill X only


        # Create figure for graphs below the table
        graph_frame = tk.Frame(tab)
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        fig, axes = plt.subplots(1, 2, figsize=(8, 3.5)) # Adjusted figure size

        # Plot 1: Robot state counts over time
        ax = axes[0]
        if self.metrics_history['timestamp']:
            times = self.metrics_history['timestamp']
            min_len = len(times)
            active = self.metrics_history['robots_active'][:min_len]
            waiting = self.metrics_history['waiting_robots'][:min_len]
            carrying = self.metrics_history['carrying_robots'][:min_len]

            if len(active) == min_len: ax.plot(times, active, label='Active', color='blue')
            if len(waiting) == min_len: ax.plot(times, waiting, label='Waiting', color='orange')
            if len(carrying) == min_len: ax.plot(times, carrying, label='Carrying', color='green')

            ax.legend()
            ax.set_title('Robot State Counts')
            ax.set_xlabel('Time (s)')
            ax.set_ylabel('Count')
        else:
             ax.set_title('Robot State (No data)')


        # Plot 2: Avg Time distribution (pie chart instead of stacked bar)
        ax = axes[1]
        overall_metrics = self.calculate_overall_metrics()
        labels = ['Idle', 'Carrying', 'Waiting']
        sizes = [
            overall_metrics.get('avg_idle_percentage', 0),
            overall_metrics.get('avg_carrying_percentage', 0),
            overall_metrics.get('avg_waiting_percentage', 0)
        ]
        # Add path finding if tracked, otherwise sum should be close to 100
        if 'avg_path_finding_percentage' in overall_metrics: # Check if key exists
             labels.append('Path Finding')
             sizes.append(overall_metrics['avg_path_finding_percentage'])


        colors = ['gray', 'green', 'orange', 'blue']
        valid_sizes = [s for s in sizes if s > 0.1] # Filter out tiny slices
        valid_labels = [labels[i] for i, s in enumerate(sizes) if s > 0.1]
        valid_colors = [colors[i] for i, s in enumerate(sizes) if s > 0.1]


        if valid_sizes:
            ax.pie(valid_sizes, labels=valid_labels, colors=valid_colors, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')
            ax.set_title('Avg Robot Time Dist.')
        else:
            ax.set_title('Time Dist. (No data)')


        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)