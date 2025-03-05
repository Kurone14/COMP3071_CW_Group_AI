"""
Performance Metrics Module
Tracks and analyzes the performance of robots during simulation
"""
import time
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from collections import deque
import config

class PerformanceEvaluator:
    def __init__(self):
        """Initialize the performance evaluator"""
        self.adaptation_times = []
        self.path_efficiencies = []
        self.mapping_accuracies = []
        self.collision_counts = 0
        self.collision_near_misses = 0
        self.start_time = None
        self.layout_change_times = []
        self.task_completion_times = []
        self.robot_utilization = {}
        
        # For real-time metrics
        self.recent_collisions = deque(maxlen=100)
        self.recent_path_efficiencies = deque(maxlen=100)
        self.recent_task_times = deque(maxlen=100)
        
    def start_evaluation(self):
        """Start performance evaluation"""
        self.start_time = time.time()
        
    def record_layout_change(self):
        """Record when a layout change occurred"""
        if self.start_time:
            self.layout_change_times.append(time.time() - self.start_time)
        
    def record_adaptation(self, detection_time):
        """Record time taken to adapt to layout change"""
        self.adaptation_times.append(detection_time)
        
    def record_path_efficiency(self, robot_id, actual_path_length, optimal_path_length):
        """Calculate and record path efficiency"""
        if optimal_path_length > 0:
            efficiency = optimal_path_length / max(1, actual_path_length)
            self.path_efficiencies.append(efficiency)
            self.recent_path_efficiencies.append(efficiency)
            
            # Record per-robot efficiency
            if robot_id not in self.robot_utilization:
                self.robot_utilization[robot_id] = {'path_efficiencies': []}
            self.robot_utilization[robot_id]['path_efficiencies'].append(efficiency)
        
    def record_mapping_accuracy(self, predicted_map, actual_map):
        """Calculate mapping accuracy by comparing predicted environment map with ground truth"""
        # This is a simplified implementation
        total_cells = len(actual_map)
        matching_cells = sum(1 for p, a in zip(predicted_map, actual_map) if p == a)
        accuracy = matching_cells / total_cells if total_cells > 0 else 0
        self.mapping_accuracies.append(accuracy)
        
    def record_collision_event(self, robot_id, is_near_miss=False):
        """Record a collision event"""
        if is_near_miss:
            self.collision_near_misses += 1
        else:
            self.collision_counts += 1
            self.recent_collisions.append(time.time())
            
            # Record per-robot collision
            if robot_id not in self.robot_utilization:
                self.robot_utilization[robot_id] = {'collisions': 0}
            elif 'collisions' not in self.robot_utilization[robot_id]:
                self.robot_utilization[robot_id]['collisions'] = 0
            self.robot_utilization[robot_id]['collisions'] += 1
    
    def record_task_completion(self, robot_id, task_type, start_time, end_time):
        """Record task completion metrics"""
        completion_time = end_time - start_time
        self.task_completion_times.append((task_type, completion_time))
        self.recent_task_times.append(completion_time)
        
        # Record per-robot task completion
        if robot_id not in self.robot_utilization:
            self.robot_utilization[robot_id] = {
                'tasks_completed': 0, 
                'avg_task_time': 0,
                'pickup_tasks': 0,
                'dropoff_tasks': 0
            }
        elif 'tasks_completed' not in self.robot_utilization[robot_id]:
            self.robot_utilization[robot_id]['tasks_completed'] = 0
            self.robot_utilization[robot_id]['avg_task_time'] = 0
            self.robot_utilization[robot_id]['pickup_tasks'] = 0
            self.robot_utilization[robot_id]['dropoff_tasks'] = 0
                
        # Update robot's task statistics
        current_count = self.robot_utilization[robot_id]['tasks_completed']
        current_avg = self.robot_utilization[robot_id]['avg_task_time']
        
        # Calculate new average
        new_count = current_count + 1
        new_avg = (current_avg * current_count + completion_time) / new_count
        
        self.robot_utilization[robot_id]['tasks_completed'] = new_count
        self.robot_utilization[robot_id]['avg_task_time'] = new_avg
        
        # Track task types
        if task_type == 'pickup':
            self.robot_utilization[robot_id]['pickup_tasks'] += 1
        elif task_type == 'dropoff':
            self.robot_utilization[robot_id]['dropoff_tasks'] += 1
            
    def get_collision_rate(self):
        """Calculate collisions per minute over recent history"""
        if not self.recent_collisions or self.start_time is None:
            return 0
        
        now = time.time()
        recent_window = now - max(self.start_time, now - 60)  # Last minute or since start
        recent_count = sum(1 for t in self.recent_collisions if now - t <= recent_window)
        
        return recent_count / (recent_window / 60)  # Collisions per minute
    
    def get_average_recent_efficiency(self):
        """Get the average path efficiency over recent history"""
        if not self.recent_path_efficiencies:
            return 0
        return sum(self.recent_path_efficiencies) / len(self.recent_path_efficiencies)
    
    def get_average_recent_task_time(self):
        """Get the average task completion time over recent history"""
        if not self.recent_task_times:
            return 0
        return sum(self.recent_task_times) / len(self.recent_task_times)
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        total_time = time.time() - self.start_time if self.start_time else 0
        
        # Calculate throughput metrics
        total_pickup_tasks = sum(
            data.get('pickup_tasks', 0) 
            for rid, data in self.robot_utilization.items()
        )
        total_dropoff_tasks = sum(
            data.get('dropoff_tasks', 0) 
            for rid, data in self.robot_utilization.items()
        )
        
        # Total completed logistics cycles (pickup + dropoff)
        completed_cycles = min(total_pickup_tasks, total_dropoff_tasks)
        
        # Cycles per minute
        cycles_per_minute = completed_cycles / (total_time / 60) if total_time > 0 else 0
        
        # Calculate robot utilization percentage
        robot_count = len(self.robot_utilization)
        total_task_time = sum(
            data.get('tasks_completed', 0) * data.get('avg_task_time', 0)
            for rid, data in self.robot_utilization.items()
        )
        
        # Overall utilization percentage (time spent on tasks / total available time)
        utilization_percentage = (total_task_time / (robot_count * total_time)) * 100 if total_time > 0 and robot_count > 0 else 0
        
        report = {
            "total_runtime_seconds": total_time,
            "total_collisions": self.collision_counts,
            "collision_near_misses": self.collision_near_misses,
            "collisions_per_minute": self.collision_counts / (total_time / 60) if total_time > 0 else 0,
            "avg_path_efficiency": np.mean(self.path_efficiencies) if self.path_efficiencies else 0,
            "avg_mapping_accuracy": np.mean(self.mapping_accuracies) if self.mapping_accuracies else 0,
            "avg_task_completion_time": np.mean([t[1] for t in self.task_completion_times]) if self.task_completion_times else 0,
            "total_pickup_tasks": total_pickup_tasks,
            "total_dropoff_tasks": total_dropoff_tasks,
            "completed_logistics_cycles": completed_cycles,
            "logistics_throughput_per_minute": cycles_per_minute,
            "robot_utilization_percentage": utilization_percentage,
            "layout_changes": len(self.layout_change_times),
            "avg_adaptation_time": np.mean(self.adaptation_times) if self.adaptation_times else 0,
            "robot_performance": self.robot_utilization
        }
        
        # Generate performance graphs
        self.generate_performance_graphs()
        
        return report
    
    def generate_performance_graphs(self):
        """Generate and save performance visualization graphs"""
        # Create a figure with multiple subplots for a more comprehensive visualization
        plt.figure(figsize=(15, 12))
        
        # Plot task completion times
        if self.task_completion_times:
            plt.subplot(2, 2, 1)
            times = [t[1] for t in self.task_completion_times]
            plt.plot(times, 'b-', label='Completion Time')
            
            # Add moving average line
            window_size = min(10, len(times))
            if window_size > 0:
                moving_avg = np.convolve(times, np.ones(window_size)/window_size, mode='valid')
                plt.plot(range(window_size-1, len(times)), moving_avg, 'r-', label='Moving Avg')
                
            plt.title('Task Completion Times')
            plt.xlabel('Task')
            plt.ylabel('Time (seconds)')
            plt.grid(True)
            plt.legend()
        
        # Plot robot utilization
        if self.robot_utilization:
            plt.subplot(2, 2, 2)
            robot_ids = list(self.robot_utilization.keys())
            
            pickup_tasks = [self.robot_utilization[rid].get('pickup_tasks', 0) for rid in robot_ids]
            dropoff_tasks = [self.robot_utilization[rid].get('dropoff_tasks', 0) for rid in robot_ids]
            
            x = np.arange(len(robot_ids))
            width = 0.35
            
            plt.bar(x - width/2, pickup_tasks, width, label='Pickup Tasks')
            plt.bar(x + width/2, dropoff_tasks, width, label='Dropoff Tasks')
            
            plt.title('Tasks Completed by Robot')
            plt.xlabel('Robot ID')
            plt.ylabel('Number of Tasks')
            plt.xticks(x, robot_ids)
            plt.legend()
        
        # Plot throughput over time
        if self.task_completion_times and self.start_time:
            plt.subplot(2, 2, 3)
            
            # Create time bins
            total_time = time.time() - self.start_time
            bin_size = max(60, total_time / 20)  # Either 1-minute bins or 20 bins total
            bins = np.arange(0, total_time + bin_size, bin_size)
            
            # Count tasks in each time bin
            task_bins = [0] * (len(bins) - 1)
            
            for task_type, completion_time in self.task_completion_times:
                # Estimate task completion time based on task duration
                task_completion = self.start_time + completion_time
                bin_index = int((task_completion - self.start_time) / bin_size)
                if 0 <= bin_index < len(task_bins):
                    task_bins[bin_index] += 1
            
            # Plot task throughput histogram
            plt.bar(bins[:-1], task_bins, width=bin_size * 0.8, alpha=0.7)
            
            # Mark layout change times with vertical lines
            for change_time in self.layout_change_times:
                plt.axvline(x=change_time, color='r', linestyle='--', alpha=0.7)
            
            plt.title('Task Throughput Over Time')
            plt.xlabel('Time (seconds)')
            plt.ylabel('Tasks Completed')
            plt.grid(True)
        
        # Plot adaptation metrics - recovery time after layout changes
        if self.layout_change_times and self.task_completion_times:
            plt.subplot(2, 2, 4)
            
            # Create a timeline of task completions
            task_times = []
            for _, completion_time in self.task_completion_times:
                task_times.append(completion_time)
            
            # Calculate moving average of task completion rate
            window_size = min(5, len(task_times))
            if window_size > 0 and len(task_times) > window_size:
                # Convert to completion rate (tasks/minute)
                completion_rates = []
                for i in range(len(task_times) - window_size + 1):
                    window_time = sum(task_times[i:i+window_size])
                    rate = (window_size / window_time) * 60 if window_time > 0 else 0
                    completion_rates.append(rate)
                
                # Plot completion rate over time
                x_values = np.linspace(0, total_time, len(completion_rates))
                plt.plot(x_values, completion_rates, 'g-', label='Task Rate')
                
                # Highlight layout changes
                for change_time in self.layout_change_times:
                    plt.axvline(x=change_time, color='r', linestyle='--', alpha=0.7)
                
                plt.title('Task Completion Rate Over Time')
                plt.xlabel('Time (seconds)')
                plt.ylabel('Tasks Per Minute')
                plt.grid(True)
        
        # Add a title for the entire figure
        plt.suptitle('Warehouse Robot Performance Metrics', fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.95])  # Adjust for the suptitle
        
        # Save the figure
        plt.savefig(config.REPORT_FILE)
        print(f"Performance graphs saved to '{config.REPORT_FILE}'")
        
        # Close the figure to free memory
        plt.close()