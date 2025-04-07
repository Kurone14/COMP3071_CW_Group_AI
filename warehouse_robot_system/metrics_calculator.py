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
        
        # Initialize metrics tracking
        self._init_robot_metrics()
        
    def _init_robot_metrics(self):
        """Initialize metrics tracking for each robot"""
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
                'path_lengths': []
            }
    
    def start_tracking(self):
        """Start tracking metrics"""
        self.start_time = time.time()
        
        # Reset metrics history
        for key in self.metrics_history:
            if key != 'strategy_usage':
                self.metrics_history[key] = []
        
        self.metrics_history['strategy_usage'] = {}
        
        # Reset robot metrics
        self._init_robot_metrics()
    
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
        
        for robot in self.simulation.robots:
            # Update robot-specific metrics
            if robot.id in self.robot_metrics:
                # Track steps
                self.robot_metrics[robot.id]['total_steps'] = robot.steps
                
                # Track state
                current_state = self._determine_robot_state(robot)
                self.robot_metrics[robot.id]['current_state'] = current_state
                self.robot_metrics[robot.id]['state_history'].append(current_state)
                
                # Count state durations
                if current_state == 'idle':
                    self.robot_metrics[robot.id]['idle_time'] += 1
                elif current_state == 'carrying':
                    self.robot_metrics[robot.id]['carrying_time'] += 1
                    carrying_robots += 1
                elif current_state == 'waiting':
                    self.robot_metrics[robot.id]['waiting_time'] += 1
                    waiting_robots += 1
                elif current_state == 'path_finding':
                    self.robot_metrics[robot.id]['path_finding_time'] += 1
                
                # Track path lengths when path is assigned
                if robot.path:
                    self.robot_metrics[robot.id]['path_lengths'].append(len(robot.path))
            
            # Count active robots (has path or carrying items)
            if robot.path or robot.carrying_items:
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
            total_steps = sum(robot.steps for robot in self.simulation.robots)
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
                self.metrics_history['strategy_usage'][strategy].append(percentage)
        
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
    
    def _determine_robot_state(self, robot):
        """Determine the current state of a robot"""
        if hasattr(robot, 'waiting') and robot.waiting:
            return 'waiting'
        elif robot.carrying_items:
            return 'carrying'
        elif robot.path:
            return 'path_finding'
        else:
            return 'idle'
    
    def calculate_overall_metrics(self):
        """
        Calculate overall metrics for the entire simulation
        
        Returns:
            dict: Dictionary of overall metrics
        """
        if not self.metrics_history['timestamp']:
            return {
                'duration': 0,
                'total_items_delivered': 0,
                'total_steps': 0,
                'avg_robot_utilization': 0,
                'steps_per_item': 0,
                'items_per_minute': 0
            }
        
        # Calculate duration
        duration = self.metrics_history['timestamp'][-1]
        
        # Get final values
        total_items_delivered = self.metrics_history['items_delivered'][-1]
        total_steps = self.metrics_history['total_steps'][-1]
        
        # Calculate average robot utilization
        avg_robot_utilization = sum(self.metrics_history['robot_utilization']) / len(self.metrics_history['robot_utilization'])
        
        # Calculate efficiency metrics
        steps_per_item = total_steps / max(1, total_items_delivered)
        
        # Items per minute
        items_per_minute = (total_items_delivered / max(1, duration)) * 60
        
        # Average robot stats
        avg_idle_time = sum(rm['idle_time'] for rm in self.robot_metrics.values()) / max(1, len(self.robot_metrics))
        avg_carrying_time = sum(rm['carrying_time'] for rm in self.robot_metrics.values()) / max(1, len(self.robot_metrics))
        avg_waiting_time = sum(rm['waiting_time'] for rm in self.robot_metrics.values()) / max(1, len(self.robot_metrics))
        
        # Strategy distribution
        strategy_distribution = {}
        if self.metrics_history['strategy_usage']:
            for strategy, usages in self.metrics_history['strategy_usage'].items():
                strategy_distribution[strategy] = sum(usages) / len(usages)
        
        # Calculate average obstacle counts
        avg_obstacles = sum(self.metrics_history['obstacle_count']) / len(self.metrics_history['obstacle_count'])
        avg_temp_obstacles = sum(self.metrics_history['temporary_obstacles']) / len(self.metrics_history['temporary_obstacles'])
        avg_semi_perm_obstacles = sum(self.metrics_history['semi_perm_obstacles']) / len(self.metrics_history['semi_perm_obstacles'])
        avg_perm_obstacles = sum(self.metrics_history['permanent_obstacles']) / len(self.metrics_history['permanent_obstacles'])
        
        return {
            'duration': duration,
            'total_items_delivered': total_items_delivered,
            'total_steps': total_steps,
            'avg_robot_utilization': avg_robot_utilization,
            'steps_per_item': steps_per_item,
            'items_per_minute': items_per_minute,
            'avg_idle_time': avg_idle_time,
            'avg_carrying_time': avg_carrying_time,
            'avg_waiting_time': avg_waiting_time,
            'strategy_distribution': strategy_distribution,
            'avg_obstacles': avg_obstacles,
            'avg_temp_obstacles': avg_temp_obstacles,
            'avg_semi_perm_obstacles': avg_semi_perm_obstacles,
            'avg_perm_obstacles': avg_perm_obstacles
        }
    
    def calculate_robot_efficiency(self):
        """
        Calculate efficiency metrics for individual robots
        
        Returns:
            dict: Dictionary of robot efficiency metrics by robot ID
        """
        robot_efficiency = {}
        
        for robot_id, metrics in self.robot_metrics.items():
            # Skip robots with no activity
            if metrics['total_steps'] == 0:
                continue
            
            # Calculate robot-specific metrics
            efficiency = {
                'total_steps': metrics['total_steps'],
                'items_delivered': metrics['items_delivered'],
                'idle_percentage': (metrics['idle_time'] / max(1, sum([
                    metrics['idle_time'], 
                    metrics['carrying_time'], 
                    metrics['waiting_time'], 
                    metrics['path_finding_time']]))) * 100,
                'carrying_percentage': (metrics['carrying_time'] / max(1, sum([
                    metrics['idle_time'], 
                    metrics['carrying_time'], 
                    metrics['waiting_time'], 
                    metrics['path_finding_time']]))) * 100,
                'waiting_percentage': (metrics['waiting_time'] / max(1, sum([
                    metrics['idle_time'], 
                    metrics['carrying_time'], 
                    metrics['waiting_time'], 
                    metrics['path_finding_time']]))) * 100,
                'path_lengths': metrics['path_lengths']
            }
            
            # Calculate average path length
            if metrics['path_lengths']:
                efficiency['avg_path_length'] = sum(metrics['path_lengths']) / len(metrics['path_lengths'])
            else:
                efficiency['avg_path_length'] = 0
            
            robot_efficiency[robot_id] = efficiency
        
        return robot_efficiency
    
    def calculate_obstacle_metrics(self):
        """
        Calculate metrics related to obstacles
        
        Returns:
            dict: Dictionary of obstacle-related metrics
        """
        if not self.metrics_history['timestamp']:
            return {
                'obstacle_count_over_time': [],
                'obstacle_type_distribution': {},
                'obstacle_density': 0
            }
        
        # Obstacle count over time
        obstacle_counts = list(zip(
            self.metrics_history['timestamp'],
            self.metrics_history['obstacle_count']
        ))
        
        # Calculate the distribution of obstacle types
        total_obstacles = (
            sum(self.metrics_history['permanent_obstacles']) + 
            sum(self.metrics_history['temporary_obstacles']) + 
            sum(self.metrics_history['semi_perm_obstacles'])
        )
        
        if total_obstacles > 0:
            type_distribution = {
                'permanent': sum(self.metrics_history['permanent_obstacles']) / total_obstacles,
                'temporary': sum(self.metrics_history['temporary_obstacles']) / total_obstacles,
                'semi_permanent': sum(self.metrics_history['semi_perm_obstacles']) / total_obstacles
            }
        else:
            type_distribution = {'permanent': 0, 'temporary': 0, 'semi_permanent': 0}
        
        # Calculate obstacle density (percentage of grid cells with obstacles)
        grid_size = self.simulation.grid.width * self.simulation.grid.height
        avg_obstacle_count = sum(self.metrics_history['obstacle_count']) / len(self.metrics_history['obstacle_count'])
        obstacle_density = (avg_obstacle_count / grid_size) * 100
        
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
        if not self.metrics_history['timestamp'] or not hasattr(self.simulation.path_finder, 'get_strategy_performance'):
            return {
                'strategy_performance': {},
                'path_lengths': [],
                'waiting_events': 0
            }
        
        # Get strategy performance if available
        strategy_performance = {}
        if hasattr(self.simulation.path_finder, 'get_strategy_performance'):
            strategy_performance = self.simulation.path_finder.get_strategy_performance()
        
        # Path lengths over time
        path_lengths = list(zip(
            self.metrics_history['timestamp'],
            self.metrics_history['path_lengths']
        ))
        
        # Count waiting events (robots that had to wait for temporary obstacles)
        waiting_events = sum(1 for count in self.metrics_history['waiting_robots'] if count > 0)
        
        return {
            'strategy_performance': strategy_performance,
            'path_lengths': path_lengths,
            'waiting_events': waiting_events
        }
    
    def generate_metrics_report(self):
        """
        Generate a comprehensive metrics report for the simulation
        
        Returns:
            str: Formatted report text
        """
        overall = self.calculate_overall_metrics()
        robot_eff = self.calculate_robot_efficiency()
        obstacle_metrics = self.calculate_obstacle_metrics()
        path_metrics = self.calculate_path_metrics()
        
        # Format the report
        report = []
        report.append("# Warehouse Robot Simulation Metrics Report")
        report.append(f"Simulation duration: {overall['duration']:.2f} seconds")
        report.append("")
        
        report.append("## Overall Performance")
        report.append(f"Total items delivered: {overall['total_items_delivered']}")
        report.append(f"Total robot steps: {overall['total_steps']}")
        report.append(f"Average robot utilization: {overall['avg_robot_utilization']:.2f}%")
        report.append(f"Steps per item: {overall['steps_per_item']:.2f}")
        report.append(f"Items delivered per minute: {overall['items_per_minute']:.2f}")
        report.append("")
        
        report.append("## Robot Time Distribution")
        report.append(f"Average idle time: {overall['avg_idle_time']:.2f} cycles")
        report.append(f"Average carrying time: {overall['avg_carrying_time']:.2f} cycles")
        report.append(f"Average waiting time: {overall['avg_waiting_time']:.2f} cycles")
        report.append("")
        
        report.append("## Pathfinding")
        if path_metrics['strategy_performance']:
            report.append("Strategy performance:")
            for strategy, perf in path_metrics['strategy_performance'].items():
                report.append(f"  - {strategy}: Success rate: {perf.get('success_rate', 0)*100:.1f}%, " +
                             f"Path quality: {perf.get('path_quality', 0)*100:.1f}%")
        
        report.append(f"Waiting events due to obstacles: {path_metrics['waiting_events']}")
        report.append("")
        
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
        # Create a DataFrame from the metrics history
        data = {
            'timestamp': self.metrics_history['timestamp'],
            'robots_active': self.metrics_history['robots_active'],
            'items_remaining': self.metrics_history['items_remaining'],
            'items_delivered': self.metrics_history['items_delivered'],
            'total_steps': self.metrics_history['total_steps'],
            'robot_utilization': self.metrics_history['robot_utilization'],
            'obstacle_count': self.metrics_history['obstacle_count'],
            'permanent_obstacles': self.metrics_history['permanent_obstacles'],
            'temporary_obstacles': self.metrics_history['temporary_obstacles'],
            'semi_perm_obstacles': self.metrics_history['semi_perm_obstacles'],
            'waiting_robots': self.metrics_history['waiting_robots'],
            'carrying_robots': self.metrics_history['carrying_robots']
        }
        
        # Add strategy usage if available
        for strategy, usage in self.metrics_history['strategy_usage'].items():
            # Ensure all strategies have same length data by filling with zeros
            if len(usage) < len(data['timestamp']):
                usage = usage + [0] * (len(data['timestamp']) - len(usage))
            data[f'strategy_{strategy}'] = usage
        
        # Create DataFrame
        df = pd.DataFrame(data)
        
        # Export to CSV
        df.to_csv(filename, index=False)
        print(f"Exported metrics to {filename}")
    
    def create_visualization_window(self):
        """
        Create a window with visualizations of the metrics
        """
        # Create a toplevel window
        metrics_window = tk.Toplevel()
        metrics_window.title("Simulation Metrics Visualization")
        metrics_window.geometry("900x700")
        
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
    
    def _create_overview_tab(self, notebook):
        """Create the overview tab with main metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Overview")
        
        # Create frame for metrics
        metrics_frame = ttk.LabelFrame(tab, text="Overall Metrics")
        metrics_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Calculate overall metrics
        overall = self.calculate_overall_metrics()
        
        # Create labels for metrics
        metrics_text = f"""
        Duration: {overall['duration']:.2f} seconds
        
        Items delivered: {overall['total_items_delivered']}
        Total steps: {overall['total_steps']}
        
        Robot utilization: {overall['avg_robot_utilization']:.2f}%
        Steps per item: {overall['steps_per_item']:.2f}
        Items per minute: {overall['items_per_minute']:.2f}
        """
        
        metrics_label = tk.Label(metrics_frame, text=metrics_text, justify=tk.LEFT)
        metrics_label.pack(padx=10, pady=10)
        
        # Create figure for graphs
        fig = plt.figure(figsize=(8, 6))
        
        # Plot 1: Items remaining vs delivered
        plt.subplot(2, 2, 1)
        if self.metrics_history['timestamp']:
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['items_remaining'], 
                    label='Remaining', color='red')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['items_delivered'], 
                    label='Delivered', color='green')
            plt.legend()
            plt.title('Item Status Over Time')
            plt.xlabel('Time (s)')
            plt.ylabel('Count')
        else:
            plt.title('No data available')
        
        # Plot 2: Robot utilization
        plt.subplot(2, 2, 2)
        if self.metrics_history['timestamp']:
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['robot_utilization'], color='blue')
            plt.title('Robot Utilization')
            plt.xlabel('Time (s)')
            plt.ylabel('Utilization (%)')
            plt.ylim(0, 100)
        else:
            plt.title('No data available')
        
        # Plot 3: Total steps over time
        plt.subplot(2, 2, 3)
        if self.metrics_history['timestamp']:
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['total_steps'], color='purple')
            plt.title('Total Steps Over Time')
            plt.xlabel('Time (s)')
            plt.ylabel('Steps')
        else:
            plt.title('No data available')
        
        # Plot 4: Strategy usage if available
        plt.subplot(2, 2, 4)
        if self.metrics_history['strategy_usage'] and any(self.metrics_history['strategy_usage'].values()):
            for strategy, usage in self.metrics_history['strategy_usage'].items():
                if usage:
                    plt.plot(self.metrics_history['timestamp'][:len(usage)], usage, label=strategy)
            plt.legend()
            plt.title('Pathfinding Strategy Usage')
            plt.xlabel('Time (s)')
            plt.ylabel('Usage (%)')
        else:
            plt.title('No strategy data available')
        
        plt.tight_layout()
        
        # Add the figure to the tab
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_robots_tab(self, notebook):
        """Create tab with robot-specific metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Robots")
        
        # Calculate robot efficiency
        robot_efficiency = self.calculate_robot_efficiency()
        
        # Create frame for robot metrics table
        table_frame = ttk.LabelFrame(tab, text="Robot Performance")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview for robot metrics
        columns = ("Robot ID", "Total Steps", "Avg Path Length", "Idle Time %", "Carrying Time %", "Waiting Time %")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings")
        
        # Set column headings
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor=tk.CENTER)
        
        # Add data
        for robot_id, metrics in robot_efficiency.items():
            tree.insert("", "end", values=(
                robot_id,
                metrics['total_steps'],
                f"{metrics.get('avg_path_length', 0):.2f}",
                f"{metrics['idle_percentage']:.2f}%",
                f"{metrics['carrying_percentage']:.2f}%",
                f"{metrics['waiting_percentage']:.2f}%"
            ))
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Create figure for graphs
        fig = plt.figure(figsize=(8, 4))
        
        # Plot 1: Robot state over time
        plt.subplot(1, 2, 1)
        if self.metrics_history['timestamp']:
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['robots_active'], 
                    label='Active', color='blue')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['waiting_robots'], 
                    label='Waiting', color='orange')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['carrying_robots'], 
                    label='Carrying', color='green')
            plt.legend()
            plt.title('Robot State Over Time')
            plt.xlabel('Time (s)')
            plt.ylabel('Count')
        else:
            plt.title('No data available')
        
        # Plot 2: Time distribution (stacked bar)
        plt.subplot(1, 2, 2)
        if robot_efficiency:
            labels = [f"Robot {rid}" for rid in robot_efficiency.keys()]
            idle = [metrics['idle_percentage'] for metrics in robot_efficiency.values()]
            carrying = [metrics['carrying_percentage'] for metrics in robot_efficiency.values()]
            waiting = [metrics['waiting_percentage'] for metrics in robot_efficiency.values()]
            
            width = 0.5
            fig, ax = plt.subplots()
            ax.bar(labels, idle, width, label='Idle', color='gray')
            ax.bar(labels, carrying, width, bottom=idle, label='Carrying', color='green')
            ax.bar(labels, waiting, width, bottom=[i+c for i, c in zip(idle, carrying)], 
                label='Waiting', color='orange')
            
            ax.set_ylabel('Percentage')
            ax.set_title('Robot Time Distribution')
            ax.legend()
        else:
            plt.title('No robot data available')
        
        plt.tight_layout()
        
        # Add the figure to the tab
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _create_obstacles_tab(self, notebook):
        """Create tab with obstacle metrics"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Obstacles")
        
        # Get obstacle metrics
        obstacle_metrics = self.calculate_obstacle_metrics()
        
        # Create frame for obstacle metrics
        metrics_frame = ttk.LabelFrame(tab, text="Obstacle Metrics")
        metrics_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Display metrics
        metrics_text = f"""
        Obstacle Density: {obstacle_metrics['obstacle_density']:.2f}%
        
        Obstacle Type Distribution:
        """
        
        for obs_type, percentage in obstacle_metrics['obstacle_type_distribution'].items():
            metrics_text += f"- {obs_type}: {percentage*100:.1f}%\n"
        
        metrics_label = tk.Label(metrics_frame, text=metrics_text, justify=tk.LEFT)
        metrics_label.pack(padx=10, pady=10)
        
        # Create figure for graphs
        fig = plt.figure(figsize=(8, 6))
        
        # Plot 1: Obstacle count over time
        plt.subplot(2, 1, 1)
        if self.metrics_history['timestamp']:
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['obstacle_count'], 
                    label='Total', color='blue')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['permanent_obstacles'], 
                    label='Permanent', color='black')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['semi_perm_obstacles'], 
                    label='Semi-Permanent', color='brown')
            plt.plot(self.metrics_history['timestamp'], self.metrics_history['temporary_obstacles'], 
                    label='Temporary', color='orange')
            plt.legend()
            plt.title('Obstacle Count Over Time')
            plt.xlabel('Time (s)')
            plt.ylabel('Count')
        else:
            plt.title('No data available')
        
        # Plot 2: Obstacle type distribution (pie chart)
        plt.subplot(2, 1, 2)
        if obstacle_metrics['obstacle_type_distribution']:
            labels = list(obstacle_metrics['obstacle_type_distribution'].keys())
            sizes = [val * 100 for val in obstacle_metrics['obstacle_type_distribution'].values()]
            colors = ['black', 'brown', 'orange']
            
            plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
            plt.axis('equal')
            plt.title('Obstacle Type Distribution')
        else:
            plt.title('No obstacle data available')
        
        plt.tight_layout()
        
        # Add the figure to the tab
        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)