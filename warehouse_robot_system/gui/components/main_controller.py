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
        if self.simulation and hasattr(self.simulation, 'resize_grid'):
            self.simulation.resize_grid(width, height)
    
    def set_drop_point(self, x: int, y: int) -> None:
        """
        Set the drop point location
        
        Args:
            x, y: Drop point coordinates
        """
        if self.simulation and hasattr(self.simulation, 'set_drop_point'):
            self.simulation.set_drop_point(x, y)
    
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