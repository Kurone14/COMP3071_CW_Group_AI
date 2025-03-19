"""
Menu bar component for the warehouse robot simulation GUI.
"""

import tkinter as tk
from core.models.grid import CellType
from gui.handlers.menu_handlers import MenuHandlers


class MainMenuBar:
    """Main menu bar with file, environment, and help menus"""
    
    def __init__(self, app):
        """
        Initialize the main menu bar
        
        Args:
            app: The main application instance
        """
        self.app = app
        self.menu = tk.Menu(app.root)
        app.root.config(menu=self.menu)
        
        # Create menu handlers
        self.handlers = MenuHandlers(app)
        
        # Create menus
        self._create_file_menu()
        self._create_environment_menu()
        self._create_obstacle_menu()
        self._create_help_menu()
    
    def _create_file_menu(self) -> None:
        """Create the file menu"""
        file_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Simulation", command=self.handlers.on_new_simulation)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.app._on_close)
    
    def _create_environment_menu(self) -> None:
        """Create the environment menu"""
        env_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Environment", menu=env_menu)
        env_menu.add_command(label="Set Grid Size", command=self.handlers.on_set_grid_size)
        env_menu.add_command(label="Set Drop Point", command=self.handlers.on_set_drop_point)
        env_menu.add_command(label="Toggle Obstacle", command=self.handlers.on_toggle_obstacle)
    
    def _create_obstacle_menu(self) -> None:
        """Create the obstacle menu if obstacle manager is available"""
        if self.app.obstacle_manager:
            obstacle_menu = tk.Menu(self.menu, tearoff=0)
            self.menu.add_cascade(label="Obstacles", menu=obstacle_menu)
            obstacle_menu.add_command(label="Add Temporary Obstacle", 
                                    command=lambda: self.handlers.on_add_obstacle(CellType.TEMPORARY_OBSTACLE))
            obstacle_menu.add_command(label="Add Semi-Permanent Obstacle", 
                                    command=lambda: self.handlers.on_add_obstacle(CellType.SEMI_PERMANENT_OBSTACLE))
            obstacle_menu.add_command(label="Add Permanent Obstacle", 
                                    command=lambda: self.handlers.on_add_obstacle(CellType.PERMANENT_OBSTACLE))
    
    def _create_help_menu(self) -> None:
        """Create the help menu"""
        help_menu = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.handlers.on_about)