"""
Main simulation coordinator for the warehouse robot system.
Manages the simulation lifecycle and coordinates all components.
"""

import random
from typing import List, Dict, Tuple, Optional, Any

from core.models.grid import Grid, CellType
from core.models.robot import Robot
from core.models.item import Item
from core.utils.logger import get_component_logger
from core.utils.event_system import get_event_bus, EventType, publish

# Import refactored components
from simulation.manager.simulation_manager import SimulationManager
from simulation.manager.reset_manager import ResetManager
from simulation.manager.robot_manager import RobotManager
from simulation.manager.item_manager import ItemManager
from simulation.manager.grid_manager import GridManager
from simulation.obstacles.obstacle_controller import ObstacleController
from simulation.controller.step_executor import StepExecutor
from simulation.controller.stall_handler import StallHandler


class WarehouseSimulation:
    """
    Main simulation class that coordinates all simulation components.
    """
    
    def __init__(self, grid: Grid, path_finder, item_assigner, movement_controller, 
                obstacle_manager=None, performance_tracker=None, stall_detector=None):
        """
        Initialize the warehouse simulation
        
        Args:
            grid: The environment grid
            path_finder: PathFinder instance for pathfinding
            item_assigner: ItemAssigner instance for assignment logic
            movement_controller: MovementController for robot movement
            obstacle_manager: Optional ObstacleManager for advanced obstacle handling
            performance_tracker: Optional PerformanceTracker for analytics
            stall_detector: Optional StallDetector for deadlock recovery
        """
        self.grid = grid
        self.path_finder = path_finder
        self.item_assigner = item_assigner
        self.movement_controller = movement_controller
        self.obstacle_manager = obstacle_manager
        self.performance_tracker = performance_tracker
        self.stall_detector = stall_detector
        
        self.robots: List[Robot] = []
        self.items: List[Item] = []
        self.robot_start_positions: Dict[int, Tuple[int, int]] = {}
        
        self.running = False
        self.paused = False
        self.gui = None
        
        # Get component logger
        self.logger = get_component_logger("WarehouseSimulation")
        
        # Get event bus
        self.event_bus = get_event_bus()
        
        # Initialize component managers
        self._init_component_managers()
        
        self.logger.info("Warehouse simulation initialized")
    
    def _init_component_managers(self) -> None:
        """Initialize all component managers"""
        # Lifecycle managers
        self.simulation_manager = SimulationManager(self)
        self.reset_manager = ResetManager(self)
        
        # Entity managers
        self.robot_manager = RobotManager(self)
        self.item_manager = ItemManager(self)
        
        # Environment managers
        self.grid_manager = GridManager(self)
        self.obstacle_controller = ObstacleController(self)
        
        # Execution managers
        self.step_executor = StepExecutor(self)
        self.stall_handler = StallHandler(self)
    
    def initialize(self, robot_count: int = 4, item_count: int = 10) -> None:
        """
        Initialize the simulation environment with robots and items
        
        Args:
            robot_count: Number of robots to create
            item_count: Number of items to create
        """
        # Clear existing robots and items
        self.robots = []
        self.items = []
        self.robot_start_positions = {}
        
        # Create robots
        for i in range(robot_count):
            self.robot_manager.create_robot(i)
        
        # Create items
        for i in range(item_count):
            self.item_manager.create_item(i)
            
        self.logger.info(f"Initialized simulation with {robot_count} robots and {item_count} items")
        
        # Publish initialization event
        publish(EventType.SIMULATION_RESET, {
            'robots': self.robots,
            'items': self.items,
            'grid': self.grid
        })
    
    def connect_gui(self, gui) -> None:
        """
        Connect a GUI to the simulation
        
        Args:
            gui: GUI instance for visualization
        """
        self.gui = gui
        
        # Connect simulation control functions to GUI
        gui.set_simulation_controller(
            start_callback=self.start,
            pause_callback=self.toggle_pause,
            reset_callback=self.reset,
            add_robot_callback=self.robot_manager.add_robot,
            add_item_callback=self.item_manager.add_item,
            edit_robot_callback=self.robot_manager.edit_robot,
            delete_robot_callback=self.robot_manager.delete_robot,
            edit_item_callback=self.item_manager.edit_item,
            delete_item_callback=self.item_manager.delete_item
        )
        
        # Connect the controller to the simulation
        # This step is crucial to make obstacle buttons work
        if hasattr(gui, 'controller'):
            gui.controller.connect_simulation(self)
        
        # Initialize GUI with current simulation state
        gui.update_environment(self.grid, self.robots, self.items)
        
        # Enable GUI controls
        gui.enable_controls(True)
        
        self.logger.info("GUI connected to simulation")

    def toggle_obstacle(self, x: int, y: int) -> bool:
        """
        Toggle an obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            
        Returns:
            bool: True if obstacle was toggled successfully
        """
        return self.obstacle_controller.toggle_obstacle(x, y)

    def add_temporary_obstacle(self, x: int, y: int, lifespan: int = 10) -> bool:
        """
        Add a temporary obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
            
        Returns:
            bool: True if obstacle was added successfully
        """
        return self.obstacle_controller.add_temporary_obstacle(x, y, lifespan)

    def add_semi_permanent_obstacle(self, x: int, y: int, lifespan: int = 30) -> bool:
        """
        Add a semi-permanent obstacle at the specified position
        
        Args:
            x, y: Obstacle coordinates
            lifespan: Obstacle lifespan in cycles
            
        Returns:
            bool: True if obstacle was added successfully
        """
        return self.obstacle_controller.add_semi_permanent_obstacle(x, y, lifespan)

    def add_roadblock(self, x: int, y: int) -> bool:
        """
        Add a roadblock during simulation
        
        Args:
            x, y: Roadblock coordinates
            
        Returns:
            bool: True if roadblock was added successfully
        """
        return self.obstacle_controller.add_roadblock(x, y)
    
    def start(self) -> None:
        """Start the simulation"""
        self.simulation_manager.start()
    
    def toggle_pause(self) -> None:
        """Pause or resume the simulation"""
        self.simulation_manager.toggle_pause()
    
    def reset(self) -> None:
        """Reset the simulation while preserving environment"""
        self.reset_manager.reset()
    
    def simulation_step(self) -> bool:
        """
        Perform one simulation step
        
        Returns:
            bool: True if simulation should continue, False if completed
        """
        return self.step_executor.execute_step()
    
    def run_headless(self) -> None:
        """Run the simulation without GUI (for testing)"""
        self.simulation_manager.run_headless()
    
    def _on_progress_made(self) -> None:
        """Called when progress is made (item delivered)"""
        if self.stall_detector:
            self.stall_detector.last_progress_at = self.stall_detector.loop_count
        
        if self.performance_tracker:
            self.performance_tracker.add_delivered_items()