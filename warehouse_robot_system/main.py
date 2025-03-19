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

from simulation.pathfinding.path_finder import PathFinder
from simulation.pathfinding.strategies import AStarStrategy
from simulation.controller.item_assigner import ItemAssigner
from simulation.controller.movement_controller import MovementController
from simulation.obstacles.obstacle_manager import ObstacleManager
from simulation.analytics.performance_tracker import PerformanceTracker
from simulation.analytics.stall_detector import StallDetector

from gui.application import WarehouseGUI


def create_simulation():
    """
    Create and initialize the simulation components
    
    Returns:
        tuple: (simulation, gui) tuple
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
    grid.generate_random_obstacles(obstacle_density)
    
    # Set up drop point
    drop_x = width - 3
    drop_y = height - 3
    grid.set_drop_point(drop_x, drop_y)
    
    # Create obstacle manager (always enabled)
    obstacle_manager = ObstacleManager(grid)
    
    # Create pathfinding component
    path_finder = PathFinder(grid, obstacle_manager)
    path_finder.set_strategy(AStarStrategy())
    
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
    
    # Initialize environment with robots and items
    simulation.initialize(robot_count=robot_count, item_count=item_count)
    
    # Connect simulation with GUI
    simulation.connect_gui(gui)
    
    # Connect controller to simulation
    if hasattr(gui, 'controller'):
        gui.controller.connect_simulation(simulation)
    
    return simulation, gui


def main():
    """Main entry point"""
    # Create simulation and GUI
    simulation, gui = create_simulation()
    
    # Run GUI application
    gui.run()


if __name__ == "__main__":
    main()