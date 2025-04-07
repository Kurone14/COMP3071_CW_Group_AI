#!/usr/bin/env python3
"""
Autonomous Warehouse Robot Simulation
Main entry point for the application
"""

import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.models.grid import Grid, CellType
from core.models.robot import Robot
from core.models.item import Item

# Import enhanced pathfinding components
from simulation.pathfinding.path_finder import PathFinder
from simulation.pathfinding.strategies import AStarStrategy
from simulation.pathfinding.advanced_strategies import AdaptiveDynamicAStarStrategy, ProximalPolicyDijkstraStrategy
from simulation.pathfinding.strategy_selector import PathStrategySelector
from simulation.controller.item_assigner import ItemAssigner
from simulation.controller.movement_controller import MovementController
from simulation.obstacles.obstacle_manager import ObstacleManager
from simulation.analytics.performance_tracker import PerformanceTracker
from simulation.analytics.stall_detector import StallDetector

from gui.application import WarehouseGUI
from gui.components.pathfinding_monitor import PathfindingMonitor

# Import the metrics components
from metrics_calculator import SimulationMetricsCalculator
from metrics_monitor import add_metrics_monitor_to_gui


def create_simulation():
    """
    Create and initialize the simulation components
    
    Returns:
        tuple: (simulation, gui, metrics_monitor) tuple with all components
    """
    # Default configuration
    width = 15
    height = 15
    robot_count = 4
    item_count = 10
    obstacle_density = 0.06
    
    print(f"Creating simulation with size {width}x{height}")
    print(f"Robots: {robot_count}, Items: {item_count}, Obstacle density: {obstacle_density}")
    
    # Create the environment grid
    grid = Grid(width, height)
    
    # We're not using the default grid.generate_random_obstacles here
    # Instead, we'll manually place mixed obstacles
    
    # Set up drop point
    drop_x = width - 3
    drop_y = height - 3
    grid.set_drop_point(drop_x, drop_y)
    
    # Create obstacle manager (always enabled)
    obstacle_manager = ObstacleManager(grid)
    
    # Create enhanced pathfinding component with multiple strategies
    path_finder = PathFinder(grid, obstacle_manager)
    # Enable strategy selector by default - this will automatically choose the best algorithm
    path_finder.enable_strategy_selector(True)
    
    # Create item assignment component
    item_assigner = ItemAssigner(grid, path_finder)
    
    # Create movement controller
    movement_controller = MovementController(grid, path_finder, obstacle_manager)
    
    # Create performance tracking components
    performance_tracker = PerformanceTracker()
    stall_detector = StallDetector(grid, path_finder)
    
    # Initialize GUI
    gui = WarehouseGUI(width, height, grid, path_finder, 
                      obstacle_manager=obstacle_manager)
    
    # Create simulation
    from simulation.warehouse import WarehouseSimulation
    simulation = WarehouseSimulation(
        grid=grid,
        path_finder=path_finder,
        item_assigner=item_assigner,
        movement_controller=movement_controller,
        obstacle_manager=obstacle_manager,
        performance_tracker=performance_tracker,
        stall_detector=stall_detector
    )
    
    # Initialize environment with mixed obstacles
    initialize_with_mixed_obstacles(simulation, robot_count, item_count, obstacle_density)
    
    # Connect simulation with GUI
    simulation.connect_gui(gui)
    
    # Connect controller to simulation
    if hasattr(gui, 'controller'):
        gui.controller.connect_simulation(simulation)
    
    # Add metrics monitoring
    metrics_monitor = add_metrics_monitor_to_gui(gui, simulation)
    
    return simulation, gui, metrics_monitor

def initialize_with_mixed_obstacles(simulation, robot_count, item_count, obstacle_density):
    """
    Initialize the simulation with mixed obstacle types
    
    Args:
        simulation: The simulation instance
        robot_count: Number of robots
        item_count: Number of items
        obstacle_density: Overall obstacle density
    """
    import random
    from core.models.grid import CellType
    from simulation.obstacles.random_layout_generator import RandomLayoutGenerator
    
    # Generate a basic layout with robots and items, but no obstacles yet
    # We'll use the standard layout generator but with 0 obstacle density
    grid, robot_positions, item_positions = RandomLayoutGenerator.generate_layout(
        simulation.grid, robot_count, item_count, 0.0
    )
    
    # Calculate obstacle distribution
    width, height = grid.width, grid.height
    total_cells = width * height
    obstacle_count = int(total_cells * obstacle_density)
    
    # Distribution: 40% temporary, 30% semi-permanent, 30% permanent
    temp_count = int(obstacle_count * 0.4)
    semi_perm_count = int(obstacle_count * 0.3)
    perm_count = obstacle_count - temp_count - semi_perm_count
    
    print(f"Placing mixed obstacles: {obstacle_count} total")
    print(f"  - Permanent: {perm_count}")
    print(f"  - Semi-permanent: {semi_perm_count}")
    print(f"  - Temporary: {temp_count}")
    
    # Get drop point to avoid blocking it
    drop_point = grid.drop_point
    
    # Place obstacles of each type
    obstacle_types = [
        (CellType.PERMANENT_OBSTACLE, perm_count),
        (CellType.SEMI_PERMANENT_OBSTACLE, semi_perm_count),
        (CellType.TEMPORARY_OBSTACLE, temp_count)
    ]
    
    for obstacle_type, count in obstacle_types:
        placed = 0
        attempts = 0
        
        while placed < count and attempts < 1000:
            attempts += 1
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            
            # Avoid drop point
            if drop_point and (x, y) == drop_point:
                continue
            
            # Avoid existing obstacles or entities
            if grid.get_cell(x, y) != CellType.EMPTY:
                continue
            
            # Place the obstacle
            grid.set_cell(x, y, obstacle_type)
            placed += 1
            
            # Register with obstacle manager
            if simulation.obstacle_manager:
                if obstacle_type == CellType.PERMANENT_OBSTACLE:
                    lifespan = -1  # Unlimited
                elif obstacle_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    lifespan = random.randint(25, 35)
                else:  # Temporary
                    lifespan = random.randint(8, 12)
                
                simulation.obstacle_manager.add_obstacle(
                    x, y, obstacle_type=obstacle_type, lifespan=lifespan
                )
                
            # Check path exists from bottom to top periodically
            if placed % 5 == 0 and not RandomLayoutGenerator._verify_path(grid):
                # Remove last obstacle if it blocks all paths
                grid.set_cell(x, y, CellType.EMPTY)
                
                # Also remove from obstacle manager
                if simulation.obstacle_manager and (x, y) in simulation.obstacle_manager.obstacles:
                    del simulation.obstacle_manager.obstacles[(x, y)]
                
                placed -= 1
    
    # Place robots
    for i, (x, y) in enumerate(robot_positions):
        # Create robot with some capacity variation
        capacity = 10 + (i * 2) % 6
        robot = simulation.robot_manager.create_robot(i)
        simulation.robot_start_positions[i] = (x, y)
    
    # Place items
    for i, (x, y, weight) in enumerate(item_positions):
        item = simulation.item_manager.create_item(i)


def add_pathfinding_monitor(gui, path_finder):
    """
    Add the pathfinding monitor component to the GUI
    
    Args:
        gui: WarehouseGUI instance
        path_finder: Enhanced PathFinder instance
    """
    # Check if right panel exists
    if not hasattr(gui, 'right_panel'):
        print("Warning: Cannot add pathfinding monitor, GUI structure not compatible")
        return
    
    # Create a new frame for the pathfinding monitor
    import tkinter as tk
    monitor_frame = tk.Frame(gui.right_panel)
    monitor_frame.pack(fill=tk.BOTH, expand=False, pady=10)
    
    # Create and add the pathfinding monitor
    pathfinding_monitor = PathfindingMonitor(monitor_frame, path_finder)
    
    # Store reference to the monitor
    gui.pathfinding_monitor = pathfinding_monitor
    
    # Set up periodic updates for the monitor
    def update_monitor():
        """Update the pathfinding monitor periodically"""
        if hasattr(gui, 'pathfinding_monitor'):
            gui.pathfinding_monitor.update_monitor()
        
        # Schedule next update
        gui.root.after(2000, update_monitor)  # Update every 2 seconds
    
    # Start updates
    update_monitor()

def add_trajectory_panel(gui, simulation):
    """
    Add trajectory control panel to the GUI
    
    Args:
        gui: The GUI instance
        simulation: The simulation instance with trajectory tracker
    """
    if not hasattr(simulation, 'trajectory_tracker') or simulation.trajectory_tracker is None:
        print("Warning: Trajectory tracker not available in simulation")
        return
        
    # Import the trajectory control panel
    from simulation.controller.trajectory_control_panel import TrajectoryControlPanel
    
    # Find the right panel to add it to (status panel)
    if hasattr(gui, 'right_panel'):
        # Create the control panel
        trajectory_panel = TrajectoryControlPanel(gui.right_panel, simulation.trajectory_tracker)
        
        # Store reference to the panel
        gui.trajectory_panel = trajectory_panel
    else:
        print("Warning: Right panel not found in GUI")


def main():
    """Main entry point"""
    # Create simulation, GUI, and metrics monitor
    simulation, gui, metrics_monitor = create_simulation()

    add_trajectory_panel(gui, simulation)
    
    # Add pathfinding monitor to GUI
    add_pathfinding_monitor(gui, simulation.path_finder)
    
    # Run GUI application
    gui.run()


if __name__ == "__main__":
    main()