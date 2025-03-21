"""
Generates random layouts for the warehouse simulation.
"""

import random
from typing import Tuple, List, Optional

from core.models.grid import Grid, CellType


class RandomLayoutGenerator:
    """
    Generates random layouts for the warehouse simulation environment.
    Handles obstacle placement, robot positions, item positions, and drop point placement.
    """
    
    @staticmethod
    def generate_layout(grid: Grid, robot_count: int, item_count: int, 
                      obstacle_density: float = 0.1) -> Tuple[Grid, List[Tuple[int, int]], List[Tuple[int, int, int]]]:
        """
        Generate a completely random layout
        
        Args:
            grid: Grid to modify (will be cleared)
            robot_count: Number of robots to place
            item_count: Number of items to place
            obstacle_density: Density of obstacles (0.0 to 1.0)
            
        Returns:
            Tuple of (grid, robot_positions, item_positions)
            - robot_positions: List of (x, y) tuples for robot positions
            - item_positions: List of (x, y, weight) tuples for item positions
        """
        width, height = grid.width, grid.height
        
        # Create clean grid
        for y in range(height):
            for x in range(width):
                grid.set_cell(x, y, CellType.EMPTY)
        
        # Place drop point
        drop_x, drop_y = RandomLayoutGenerator._place_drop_point(grid)
        grid.set_drop_point(drop_x, drop_y)
        
        # Generate and place obstacles
        RandomLayoutGenerator._place_obstacles(grid, obstacle_density)
        
        # Place robots
        robot_positions = RandomLayoutGenerator._place_robots(grid, robot_count)
        
        # Place items
        item_positions = RandomLayoutGenerator._place_items(grid, item_count)
        
        return grid, robot_positions, item_positions
    
    @staticmethod
    def _place_drop_point(grid: Grid) -> Tuple[int, int]:
        """
        Place drop point in a random location, preferably in the bottom half
        
        Args:
            grid: Grid to modify
            
        Returns:
            Tuple of (x, y) coordinates for drop point
        """
        width, height = grid.width, grid.height
        
        # Prefer placing drop point in bottom half of grid
        drop_y = random.randint(height // 2, height - 2)
        drop_x = random.randint(1, width - 2)
        
        return drop_x, drop_y
    
    @staticmethod
    def _place_obstacles(grid: Grid, density: float) -> None:
        """
        Place obstacles randomly throughout the grid
        
        Args:
            grid: Grid to modify
            density: Density of obstacles (0.0 to 1.0)
        """
        width, height = grid.width, grid.height
        
        # Calculate number of obstacles
        total_cells = width * height
        obstacle_count = int(total_cells * density)
        
        # Get drop point to avoid blocking it
        drop_point = grid.drop_point
        
        # Place obstacles
        placed = 0
        while placed < obstacle_count:
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            
            # Don't place on drop point
            if drop_point and (x, y) == drop_point:
                continue
            
            # Don't place on existing obstacle
            if grid.get_cell(x, y) != CellType.EMPTY:
                continue
            
            # Place obstacle
            grid.set_cell(x, y, CellType.PERMANENT_OBSTACLE)
            placed += 1
            
            # Check path exists from bottom to top
            if placed % 5 == 0 and not RandomLayoutGenerator._verify_path(grid):
                # Remove last obstacle if it blocks all paths
                grid.set_cell(x, y, CellType.EMPTY)
                placed -= 1
    
    @staticmethod
    def _verify_path(grid: Grid) -> bool:
        """
        Basic verification that a path exists from bottom to top
        Uses a simple flood fill algorithm
        
        Args:
            grid: Grid to check
            
        Returns:
            bool: True if a path exists, False otherwise
        """
        width, height = grid.width, grid.height
        
        # Start from middle bottom
        start_x = width // 2
        start_y = height - 1
        
        # Find an empty cell at the bottom
        for x in range(width):
            if grid.is_cell_empty(x, height - 1):
                start_x = x
                break
        
        # Target is top row
        visited = set()
        queue = [(start_x, start_y)]
        
        while queue:
            x, y = queue.pop(0)
            
            if y == 0:  # Reached top
                return True
                
            if (x, y) in visited:
                continue
                
            visited.add((x, y))
            
            # Try each direction
            for dx, dy in [(0, -1), (1, 0), (0, 1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if grid.in_bounds(nx, ny) and grid.is_cell_empty(nx, ny) and (nx, ny) not in visited:
                    queue.append((nx, ny))
        
        return False
    
    @staticmethod
    def _place_robots(grid: Grid, robot_count: int) -> List[Tuple[int, int]]:
        """
        Place robots in valid positions, preferring the bottom of the grid
        
        Args:
            grid: Grid to modify
            robot_count: Number of robots to place
            
        Returns:
            List of (x, y) tuples for robot positions
        """
        width, height = grid.width, grid.height
        robot_positions = []
        
        # Try to place robots along the bottom rows
        for i in range(robot_count):
            placed = False
            attempts = 0
            
            # Start from bottom rows
            while not placed and attempts < 100:
                row = height - 1 - (attempts // width)
                if row < 0:
                    row = random.randint(0, height - 1)
                    
                col = random.randint(0, width - 1)
                
                if grid.is_cell_empty(col, row):
                    grid.set_cell(col, row, CellType.ROBOT)
                    robot_positions.append((col, row))
                    placed = True
                
                attempts += 1
            
            # Fallback: find any empty cell
            if not placed:
                for y in range(height - 1, -1, -1):
                    for x in range(width):
                        if grid.is_cell_empty(x, y):
                            grid.set_cell(x, y, CellType.ROBOT)
                            robot_positions.append((x, y))
                            placed = True
                            break
                    if placed:
                        break
        
        return robot_positions
    
    @staticmethod
    def _place_items(grid: Grid, item_count: int) -> List[Tuple[int, int, int]]:
        """
        Place items in valid positions, preferring the top half of the grid
        
        Args:
            grid: Grid to modify
            item_count: Number of items to place
            
        Returns:
            List of (x, y, weight) tuples for item positions
        """
        width, height = grid.width, grid.height
        item_positions = []
        
        # Try to place items in top half of grid
        for i in range(item_count):
            placed = False
            attempts = 0
            
            while not placed and attempts < 100:
                row = random.randint(0, height // 2)
                col = random.randint(0, width - 1)
                
                if grid.is_cell_empty(col, row):
                    # Random weight between 1 and 8
                    weight = random.randint(1, 8)
                    
                    grid.set_cell(col, row, CellType.ITEM)
                    item_positions.append((col, row, weight))
                    placed = True
                
                attempts += 1
            
            # Fallback: find any empty cell
            if not placed:
                for y in range(height):
                    for x in range(width):
                        if grid.is_cell_empty(x, y):
                            weight = random.randint(1, 8)
                            grid.set_cell(x, y, CellType.ITEM)
                            item_positions.append((x, y, weight))
                            placed = True
                            break
                    if placed:
                        break
        
        return item_positions