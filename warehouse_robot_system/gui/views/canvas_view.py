import tkinter as tk
from typing import List, Dict, Tuple, Set, Any, Optional, Callable

from core.models.grid import Grid, CellType


class CanvasView:
    """
    Canvas view for displaying the simulation environment.
    Handles rendering of grid, robots, items and obstacles.
    """
    
    def __init__(self, parent, width: int, height: int):
        """
        Initialize the canvas view
        
        Args:
            parent: Parent widget
            width: Grid width in cells
            height: Grid height in cells
        """
        self.width = width
        self.height = height
        self.cell_size = 30  # Size of each grid cell in pixels
        
        # Create frame for canvas
        self.canvas_frame = tk.Frame(parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create canvas
        self.canvas = tk.Canvas(
            self.canvas_frame, 
            width=width*self.cell_size, 
            height=height*self.cell_size, 
            bg="white"
        )
        self.canvas.pack()
        
        # Selected entities
        self.selected_robot_id = None
        self.selected_item_id = None
        
        # Click handler
        self.click_handler = None
    
    def set_click_handler(self, handler: Callable) -> None:
        """
        Set the handler for canvas clicks
        
        Args:
            handler: Function to call when canvas is clicked
        """
        self.canvas.bind("<Button-1>", handler)
    
    def set_selected_robot(self, robot_id: Optional[int]) -> None:
        """
        Set the currently selected robot
        
        Args:
            robot_id: ID of the selected robot or None
        """
        self.selected_robot_id = robot_id
    
    def set_selected_item(self, item_id: Optional[int]) -> None:
        """
        Set the currently selected item
        
        Args:
            item_id: ID of the selected item or None
        """
        self.selected_item_id = item_id
    
    def draw_environment(self, grid: Grid, width: int, height: int, 
                        drop_point: Tuple[int, int], robots: List[Any], 
                        items: List[Any], selected_robot_id: Optional[int] = None, 
                        selected_item_id: Optional[int] = None, 
                        obstacle_manager = None) -> None:
        """
        Draw the simulation environment on the canvas
        
        Args:
            grid: Grid model
            width: Grid width in cells
            height: Grid height in cells
            drop_point: Drop point coordinates (x, y)
            robots: List of robots
            items: List of items
            selected_robot_id: ID of the selected robot or None
            selected_item_id: ID of the selected item or None
            obstacle_manager: Optional obstacle manager for advanced visualization
        """
        self.selected_robot_id = selected_robot_id
        self.selected_item_id = selected_item_id
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Draw grid lines
        self._draw_grid_lines(width, height)
        
        # Draw obstacles with different visualizations based on type
        self._draw_obstacles(grid, width, height, obstacle_manager)
        
        # Draw drop point
        if drop_point:
            self._draw_drop_point(drop_point)
        
        # Draw items
        for item in items:
            if not item.picked:
                self._draw_item(item)
        
        # Draw robots
        for robot in robots:
            self._draw_robot(robot)
    
    def _draw_grid_lines(self, width: int, height: int) -> None:
        """Draw grid lines"""
        cell_size = self.cell_size
        
        # Draw vertical lines
        for x in range(0, width+1):
            self.canvas.create_line(
                x*cell_size, 0, 
                x*cell_size, height*cell_size, 
                fill="#DDDDDD"
            )
        
        # Draw horizontal lines
        for y in range(0, height+1):
            self.canvas.create_line(
                0, y*cell_size, 
                width*cell_size, y*cell_size, 
                fill="#DDDDDD"
            )
    
    def _draw_obstacles(self, grid: Grid, width: int, height: int, obstacle_manager) -> None:
        """Draw obstacles with different visualizations based on type"""
        cell_size = self.cell_size
        
        for y in range(height):
            for x in range(width):
                cell_type = grid.get_cell(x, y)
                
                if cell_type == CellType.PERMANENT_OBSTACLE:
                    # Permanent obstacle (gray)
                    self.canvas.create_rectangle(
                        x*cell_size, y*cell_size, 
                        (x+1)*cell_size, (y+1)*cell_size, 
                        fill="gray", outline="black"
                    )
                
                elif cell_type == CellType.TEMPORARY_OBSTACLE and obstacle_manager:
                    # Temporary obstacle (orange)
                    self.canvas.create_rectangle(
                        x*cell_size, y*cell_size, 
                        (x+1)*cell_size, (y+1)*cell_size, 
                        fill="#FFA500", outline="black"
                    )
                    
                    # Add lifespan indicator
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan > 0:
                        self.canvas.create_text(
                            x*cell_size + cell_size//2, 
                            y*cell_size + cell_size//2, 
                            text=str(lifespan), 
                            fill="white", 
                            font=("Arial", 8, "bold")
                        )
                
                elif cell_type == CellType.SEMI_PERMANENT_OBSTACLE and obstacle_manager:
                    # Semi-permanent obstacle (brown)
                    self.canvas.create_rectangle(
                        x*cell_size, y*cell_size, 
                        (x+1)*cell_size, (y+1)*cell_size, 
                        fill="#8B4513", outline="black"
                    )
                    
                    # Add lifespan indicator
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan > 0:
                        self.canvas.create_text(
                            x*cell_size + cell_size//2, 
                            y*cell_size + cell_size//2, 
                            text=str(lifespan), 
                            fill="white", 
                            font=("Arial", 8, "bold")
                        )
    
    def _draw_drop_point(self, drop_point: Tuple[int, int]) -> None:
        """Draw drop point"""
        cell_size = self.cell_size
        x, y = drop_point
        
        self.canvas.create_rectangle(
            x*cell_size, y*cell_size, 
            (x+1)*cell_size, (y+1)*cell_size, 
            fill="green", outline="black"
        )
        self.canvas.create_text(
            x*cell_size + cell_size//2, 
            y*cell_size + cell_size//2, 
            text="DROP", fill="white", 
            font=("Arial", 8, "bold")
        )
    
    def _draw_item(self, item) -> None:
        """Draw an item"""
        cell_size = self.cell_size
        
        # Highlight selected items
        extra_highlight = 0
        fill_color = "blue"
        
        if self.selected_item_id == item.id:
            extra_highlight = -2
            fill_color = "dark blue"
        
        self.canvas.create_rectangle(
            item.x*cell_size + 5 + extra_highlight, 
            item.y*cell_size + 5 + extra_highlight, 
            (item.x+1)*cell_size - 5 - extra_highlight, 
            (item.y+1)*cell_size - 5 - extra_highlight, 
            fill=fill_color, outline="black"
        )
        self.canvas.create_text(
            item.x*cell_size + cell_size//2, 
            item.y*cell_size + cell_size//2, 
            text=f"{item.weight}kg", 
            fill="white", 
            font=("Arial", 8, "bold")
        )
    
    def _draw_robot(self, robot) -> None:
        """Draw a robot"""
        cell_size = self.cell_size
        
        # Highlight selected robots
        extra_highlight = 0
        fill_color = "red"
        
        if self.selected_robot_id == robot.id:
            extra_highlight = -2
            fill_color = "dark red"
        
        # Draw robot body
        self.canvas.create_oval(
            robot.x*cell_size + 2 + extra_highlight, 
            robot.y*cell_size + 2 + extra_highlight, 
            (robot.x+1)*cell_size - 2 - extra_highlight, 
            (robot.y+1)*cell_size - 2 - extra_highlight, 
            fill=fill_color, outline="black"
        )
        
        # Draw robot ID
        self.canvas.create_text(
            robot.x*cell_size + cell_size//2, 
            robot.y*cell_size + cell_size//2, 
            text=f"R{robot.id}", 
            fill="white", 
            font=("Arial", 8, "bold")
        )
        
        # Draw waiting indicator for robots waiting for temporary obstacles
        if hasattr(robot, 'waiting') and robot.waiting:
            self.canvas.create_text(
                robot.x*cell_size + cell_size//2,
                robot.y*cell_size + cell_size//4,
                text="WAIT",
                fill="yellow",
                font=("Arial", 6, "bold")
            )

    def resize_canvas(self, width: int, height: int) -> None:
        """
        Resize the canvas to match new grid dimensions
        
        Args:
            width: New grid width in cells
            height: New grid height in cells
        """
        self.width = width
        self.height = height
        
        # Update canvas size
        self.canvas.config(
            width=width*self.cell_size,
            height=height*self.cell_size
        )
        
        # Force redraw
        self.canvas.update()