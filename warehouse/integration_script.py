"""
Integration script for Intelligent Obstacle Classification

This script demonstrates how to use the new obstacle classification features
in the warehouse simulation.
"""

import os
import sys
import random
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.warehouse import WarehouseSimulation
from simulation.pathfinding import PathFinder
from simulation.assignment import ItemAssigner
from simulation.obstacle_manager import ObstacleManager
from gui.main_window import WarehouseGUI

def main():
    width = 15
    height = 15
    robot_count = 4
    item_count = 10
    obstacle_density = 0.06  
    
    gui = WarehouseGUI(width, height)
    
    temp_grid = [[0 for _ in range(width)] for _ in range(height)]
    temp_drop_point = (width-3, height-3)  
    
    # Initialize PathFinder with None for ObstacleManager (will be set later)
    path_finder = PathFinder(temp_grid, width, height, temp_drop_point, obstacle_manager=None)
    
    item_assigner = ItemAssigner(temp_grid, path_finder)
    
    simulation = WarehouseSimulation(
        width=width,
        height=height,
        robot_count=robot_count,
        item_count=item_count,
        obstacle_density=obstacle_density,
        gui=gui,
        path_finder=path_finder,
        item_assigner=item_assigner
    )
    
    # Create buttons for the new obstacle types
    create_obstacle_type_buttons(gui, simulation)
    
    # Add a few test temporary obstacles after initialization
    add_test_obstacles(simulation)
    
    gui.run()

def create_obstacle_type_buttons(gui, simulation):
    """Create buttons for adding different types of obstacles"""
    import tkinter as tk
    
    # Create a new frame for obstacle type buttons
    obstacle_frame = tk.Frame(gui.control_frame)
    obstacle_frame.pack(side=tk.RIGHT, padx=10)
    
    # Add label
    tk.Label(obstacle_frame, text="Obstacle Types:").pack(side=tk.LEFT, padx=2)
    
    # Add button for temporary obstacles
    temp_button = tk.Button(
        obstacle_frame, 
        text="Temporary", 
        background="#FFA500",
        foreground="white",
        command=lambda: enter_obstacle_mode(gui, simulation, "temporary")
    )
    temp_button.pack(side=tk.LEFT, padx=2)
    
    # Add button for semi-permanent obstacles
    semi_button = tk.Button(
        obstacle_frame, 
        text="Semi-Perm", 
        background="#8B4513",
        foreground="white",
        command=lambda: enter_obstacle_mode(gui, simulation, "semi_permanent")
    )
    semi_button.pack(side=tk.LEFT, padx=2)
    
    # Add button for permanent obstacles
    perm_button = tk.Button(
        obstacle_frame, 
        text="Permanent", 
        background="gray",
        foreground="white",
        command=lambda: enter_obstacle_mode(gui, simulation, "permanent")
    )
    perm_button.pack(side=tk.LEFT, padx=2)
    
    # Store the buttons in the GUI for reference
    gui.temp_obstacle_button = temp_button
    gui.semi_perm_obstacle_button = semi_button
    gui.perm_obstacle_button = perm_button
    
    # Add obstacle legend
    create_obstacle_legend(gui)

def create_obstacle_legend(gui):
    """Create a legend for obstacle types"""
    import tkinter as tk
    
    legend_frame = tk.LabelFrame(gui.right_panel, text="Obstacle Types")
    legend_frame.pack(fill=tk.X, padx=10, pady=5, before=gui.status_frame)
    
    types = [
        ("Permanent", "gray", "white", "Never disappears"),
        ("Semi-Permanent", "#8B4513", "white", "Disappears after ~30 cycles"),
        ("Temporary", "#FFA500", "white", "Disappears after ~10 cycles")
    ]
    
    for label, bg, fg, desc in types:
        type_frame = tk.Frame(legend_frame)
        type_frame.pack(fill=tk.X, pady=2)
        
        sample = tk.Label(type_frame, text="  ", background=bg, width=2)
        sample.pack(side=tk.LEFT, padx=5)
        
        name = tk.Label(type_frame, text=label, width=15, anchor="w")
        name.pack(side=tk.LEFT, padx=5)
        
        description = tk.Label(type_frame, text=desc, anchor="w")
        description.pack(side=tk.LEFT, fill=tk.X, expand=True)

def enter_obstacle_mode(gui, simulation, obstacle_type):
    """Enter a mode for adding a specific type of obstacle"""
    import tkinter.messagebox as messagebox
    
    # Reset all buttons
    gui.temp_obstacle_button.config(relief="raised")
    gui.semi_perm_obstacle_button.config(relief="raised")
    gui.perm_obstacle_button.config(relief="raised")
    
    if obstacle_type == "temporary":
        gui.temp_obstacle_button.config(relief="sunken")
        gui.add_entity_mode = "temp_obstacle"
        messagebox.showinfo("Add Temporary Obstacle", 
                            "Click on the grid to place temporary obstacles. These will disappear after ~10 cycles.")
    elif obstacle_type == "semi_permanent":
        gui.semi_perm_obstacle_button.config(relief="sunken")
        gui.add_entity_mode = "semi_perm_obstacle"
        messagebox.showinfo("Add Semi-Permanent Obstacle", 
                            "Click on the grid to place semi-permanent obstacles. These will disappear after ~30 cycles.")
    elif obstacle_type == "permanent":
        gui.perm_obstacle_button.config(relief="sunken")
        gui.add_entity_mode = "perm_obstacle"
        messagebox.showinfo("Add Permanent Obstacle", 
                            "Click on the grid to place permanent obstacles. These will not disappear.")
    
    # Handle existing click handler
    old_click_handler = gui.canvas_view.canvas.bind("<Button-1>")
    
    # Define new click handler
    def obstacle_click_handler(event):
        x = event.x // gui.canvas_view.cell_size
        y = event.y // gui.canvas_view.cell_size
        
        if obstacle_type == "temporary":
            simulation.add_temporary_obstacle(x, y, lifespan=10)
        elif obstacle_type == "semi_permanent":
            simulation.add_semi_permanent_obstacle(x, y, lifespan=30)
        elif obstacle_type == "permanent":
            simulation.toggle_obstacle(x, y)
    
    # Bind the new click handler
    gui.canvas_view.canvas.bind("<Button-1>", obstacle_click_handler)
    
    # Add escape key to exit mode
    gui.root.bind("<Escape>", lambda e: exit_obstacle_mode(gui))

def exit_obstacle_mode(gui):
    """Exit obstacle placement mode"""
    gui.add_entity_mode = None
    gui.temp_obstacle_button.config(relief="raised")
    gui.semi_perm_obstacle_button.config(relief="raised")
    gui.perm_obstacle_button.config(relief="raised")
    gui.canvas_view.canvas.config(cursor="")

def add_test_obstacles(simulation):
    """Add some test obstacles of different types for demonstration"""
    # Only add test obstacles if we have an obstacle manager
    if simulation.obstacle_manager:
        # Add a few temporary obstacles
        for _ in range(3):
            x = random.randint(2, simulation.width-3)
            y = random.randint(2, simulation.height//2)
            simulation.add_temporary_obstacle(x, y, lifespan=10)
        
        # Add a few semi-permanent obstacles
        for _ in range(2):
            x = random.randint(2, simulation.width-3)
            y = random.randint(2, simulation.height//2)
            simulation.add_semi_permanent_obstacle(x, y, lifespan=30)

        print("Added test obstacles for demonstration")

if __name__ == "__main__":
    main()