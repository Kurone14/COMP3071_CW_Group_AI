from enum import IntEnum
from typing import List, Tuple, Optional, Dict, Set


class CellType(IntEnum):
    """Enumeration of cell types in the grid"""
    EMPTY = 0
    PERMANENT_OBSTACLE = 1
    ITEM = 2
    ROBOT = 3
    DROP_POINT = 4
    TEMPORARY_OBSTACLE = 5
    SEMI_PERMANENT_OBSTACLE = 6


class Grid:
    """
    Represents the warehouse environment grid.
    Manages the spatial state of all entities and obstacles.
    """
    def __init__(self, width: int, height: int):
        """Initialize grid with given dimensions"""
        self.width = width
        self.height = height
        self.cells = [[CellType.EMPTY for _ in range(width)] for _ in range(height)]
        self.drop_point: Optional[Tuple[int, int]] = None
        self._entity_positions: Dict[int, Tuple[int, int]] = {}  # id -> (x, y)
        self._position_entities: Dict[Tuple[int, int], Set[int]] = {}  # (x, y) -> {ids}

    def in_bounds(self, x: int, y: int) -> bool:
        """Check if coordinates are within grid bounds"""
        return 0 <= x < self.width and 0 <= y < self.height

    def is_cell_empty(self, x: int, y: int) -> bool:
        """Check if a cell is empty (can be moved into)"""
        if not self.in_bounds(x, y):
            return False
        return self.cells[y][x] == CellType.EMPTY
    
    def is_cell_walkable(self, x: int, y: int, include_temporary: bool = False) -> bool:
        """
        Check if a cell can be walked on
        
        Args:
            x, y: Coordinates
            include_temporary: If True, temporary obstacles are considered walkable,
                            but this should ONLY be used for path planning, not for actual movement
        """
        if not self.in_bounds(x, y):
            return False
            
        cell_type = self.cells[y][x]
        
        if cell_type == CellType.EMPTY or cell_type == CellType.DROP_POINT:
            return True
            
        # This parameter should only be used for path planning with future knowledge,
        # not for determining if a robot can actually move through now
        if include_temporary and cell_type == CellType.TEMPORARY_OBSTACLE:
            return True
            
        return False

    def get_cell(self, x: int, y: int) -> CellType:
        """Get cell type at position"""
        if not self.in_bounds(x, y):
            raise ValueError(f"Coordinates ({x}, {y}) out of bounds")
        return self.cells[y][x]

    def set_cell(self, x: int, y: int, cell_type: CellType) -> bool:
        """Set cell type at position"""
        if not self.in_bounds(x, y):
            return False
        self.cells[y][x] = cell_type
        return True

    def clear_cell(self, x: int, y: int) -> bool:
        """Clear cell (set to empty)"""
        return self.set_cell(x, y, CellType.EMPTY)
        
    def set_drop_point(self, x: int, y: int) -> bool:
        """Set the drop point location"""
        if not self.in_bounds(x, y):
            return False
            
        # Clear old drop point if it exists
        if self.drop_point:
            old_x, old_y = self.drop_point
            self.cells[old_y][old_x] = CellType.EMPTY
            
        self.drop_point = (x, y)
        self.cells[y][x] = CellType.DROP_POINT
        return True
        
    def register_entity(self, entity_id: int, x: int, y: int, cell_type: CellType) -> bool:
        """Register an entity (robot or item) at position"""
        if not self.in_bounds(x, y):
            return False
            
        # Update entity position tracking
        if entity_id in self._entity_positions:
            old_x, old_y = self._entity_positions[entity_id]
            if (old_x, old_y) in self._position_entities:
                self._position_entities[(old_x, old_y)].remove(entity_id)
                
        self._entity_positions[entity_id] = (x, y)
        
        if (x, y) not in self._position_entities:
            self._position_entities[(x, y)] = set()
        self._position_entities[(x, y)].add(entity_id)
        
        # Update grid cell
        self.cells[y][x] = cell_type
        return True
        
    def move_entity(self, entity_id: int, new_x: int, new_y: int, cell_type: CellType) -> bool:
        """Move an entity to a new position"""
        if not self.in_bounds(new_x, new_y):
            return False
            
        if entity_id not in self._entity_positions:
            return False
            
        old_x, old_y = self._entity_positions[entity_id]
        
        # Clear old position
        self.cells[old_y][old_x] = CellType.EMPTY
        if (old_x, old_y) in self._position_entities:
            self._position_entities[(old_x, old_y)].remove(entity_id)
            
        # Update to new position
        self._entity_positions[entity_id] = (new_x, new_y)
        
        if (new_x, new_y) not in self._position_entities:
            self._position_entities[(new_x, new_y)] = set()
        self._position_entities[(new_x, new_y)].add(entity_id)
        
        # Update grid cell
        self.cells[new_y][new_x] = cell_type
        return True
        
    def unregister_entity(self, entity_id: int) -> bool:
        """Remove an entity from the grid"""
        if entity_id not in self._entity_positions:
            return False
            
        x, y = self._entity_positions[entity_id]
        
        # Clear cell
        self.cells[y][x] = CellType.EMPTY
        
        # Remove from tracking
        del self._entity_positions[entity_id]
        if (x, y) in self._position_entities:
            self._position_entities[(x, y)].remove(entity_id)
            
        return True
        
    def get_entity_position(self, entity_id: int) -> Optional[Tuple[int, int]]:
        """Get the position of an entity by ID"""
        return self._entity_positions.get(entity_id)
        
    def get_entities_at_position(self, x: int, y: int) -> Set[int]:
        """Get all entity IDs at a given position"""
        return self._position_entities.get((x, y), set())
        
    def resize(self, new_width: int, new_height: int) -> bool:
        """Resize the grid, preserving existing cells"""
        print(f"Grid.resize: Resizing from {self.width}x{self.height} to {new_width}x{new_height}")
        
        if new_width <= 0 or new_height <= 0:
            print("Grid.resize: Invalid dimensions")
            return False
            
        # If reducing size, check if any entities would be lost
        if new_width < self.width or new_height < self.height:
            entities_out_of_bounds = []
            for entity_id, (x, y) in self._entity_positions.items():
                if x >= new_width or y >= new_height:
                    entities_out_of_bounds.append(entity_id)
            
            if entities_out_of_bounds:
                print(f"Grid.resize: Cannot reduce size, {len(entities_out_of_bounds)} entities would be lost")
                return False
            
            # Also check drop point
            if self.drop_point and (self.drop_point[0] >= new_width or self.drop_point[1] >= new_height):
                print("Grid.resize: Cannot reduce size, drop point would be lost")
                return False
        
        # Create new cell array
        new_cells = [[CellType.EMPTY for _ in range(new_width)] for _ in range(new_height)]
        
        # Copy existing cells
        for y in range(min(self.height, new_height)):
            for x in range(min(self.width, new_width)):
                new_cells[y][x] = self.cells[y][x]
        
        # Update the grid
        old_cells = self.cells
        self.cells = new_cells
        self.width = new_width
        self.height = new_height
        
        print(f"Grid.resize: Successfully resized to {self.width}x{self.height}")
        
        return True
        
    def generate_random_obstacles(self, density: float) -> None:
        """Generate random permanent obstacles with given density"""
        import random
        
        for y in range(self.height):
            for x in range(self.width):
                if self.cells[y][x] == CellType.EMPTY and random.random() < density:
                    self.cells[y][x] = CellType.PERMANENT_OBSTACLE