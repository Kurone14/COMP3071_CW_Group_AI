from typing import List, Dict, Tuple, Set, Any, Optional

from core.models.grid import CellType


class MainController:
    """
    Main controller for the GUI application.
    Handles user interactions and communicates with the simulation.
    """
    
    def __init__(self, gui):
        """
        Initialize the main controller
        
        Args:
            gui: The GUI application instance
        """
        self.gui = gui
        self.simulation = None
    
    def connect_simulation(self, simulation) -> None:
        """
        Connect the controller to a simulation
        
        Args:
            simulation: The simulation instance
        """
        self.simulation = simulation
    
    def resize_grid(self, width: int, height: int) -> None:
        """
        Resize the grid
        
        Args:
            width: New grid width
            height: New grid height
        """
        print(f"MainController: Resize grid request - {width}x{height}")
        
        if self.simulation and hasattr(self.simulation, 'grid_manager'):
            # Use grid_manager to resize
            result = self.simulation.grid_manager.resize_grid(width, height)
            print(f"MainController: Grid resize result: {result}")
            
            # Update the GUI dimensions
            if result:
                # Update GUI properties
                self.gui.width = width
                self.gui.height = height
                
                # Resize the canvas
                if hasattr(self.gui, 'canvas_view'):
                    self.gui.canvas_view.resize_canvas(width, height)
                
                # Force redraw with new dimensions
                self.gui.update_environment(
                    self.simulation.grid,
                    self.simulation.robots,
                    self.simulation.items
                )
                print(f"MainController: Updated GUI with new grid size: {width}x{height}")
        else:
            print("MainController: Simulation or grid_manager not available")
    
    def set_drop_point(self, x: int, y: int) -> None:
        """
        Set the drop point location
        
        Args:
            x, y: Drop point coordinates
        """
        if self.simulation and hasattr(self.simulation, 'grid_manager'):
            self.simulation.grid_manager.set_drop_point(x, y)
    
    def toggle_obstacle(self, x: int, y: int) -> None:
        """
        Toggle an obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
        """
        if self.simulation and hasattr(self.simulation, 'toggle_obstacle'):
            self.simulation.toggle_obstacle(x, y)
    
    def add_temporary_obstacle(self, x: int, y: int, lifespan: int = 10) -> None:
        """
        Add a temporary obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
        """
        if self.simulation and hasattr(self.simulation, 'add_temporary_obstacle'):
            self.simulation.add_temporary_obstacle(x, y, lifespan)
    
    def add_semi_permanent_obstacle(self, x: int, y: int, lifespan: int = 30) -> None:
        """
        Add a semi-permanent obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
        """
        if self.simulation and hasattr(self.simulation, 'add_semi_permanent_obstacle'):
            self.simulation.add_semi_permanent_obstacle(x, y, lifespan)
    
    def add_roadblock(self, x: int, y: int) -> None:
        """
        Add a roadblock during simulation
        
        Args:
            x, y: Roadblock coordinates
        """
        if self.simulation and hasattr(self.simulation, 'add_roadblock'):
            self.simulation.add_roadblock(x, y)

    def randomize_layout(self) -> None:
        """
        Randomize the simulation layout
        """
        if self.simulation and hasattr(self.simulation, 'randomize_layout'):
            # Default values for randomization
            obstacle_density = 0.08
            
            # Use current counts by default
            robot_count = len(self.simulation.robots) if hasattr(self.simulation, 'robots') else 4
            item_count = len(self.simulation.items) if hasattr(self.simulation, 'items') else 10
            
            print(f"MainController: Randomizing layout with {robot_count} robots, " +
                f"{item_count} items, {obstacle_density:.2f} obstacle density")
            
            self.simulation.randomize_layout(robot_count, item_count, obstacle_density)
        else:
            print("MainController: Simulation or randomize_layout not available")