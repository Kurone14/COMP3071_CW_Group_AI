from typing import Dict, Tuple, Optional, Set, List
from core.models.grid import Grid, CellType


class ObstacleManager:
    """
    Manages obstacles in the warehouse environment, including classification,
    tracking, and lifecycle management of different obstacle types.
    """
    
    def __init__(self, grid: Grid):
        """Initialize the obstacle manager with the grid reference"""
        self.grid = grid
        
        # Store obstacle metadata including type, confidence, and lifespan
        # Key: (x, y) coordinates, Value: {'type': int, 'confidence': float, 'lifespan': int, 'age': int}
        self.obstacles: Dict[Tuple[int, int], Dict] = {}
        
        # Track obstacle interactions for each robot
        # Key: robot_id, Value: {(x, y): {'attempts': int, 'successes': int, 'last_seen': int}}
        self.robot_interactions: Dict[int, Dict[Tuple[int, int], Dict]] = {}
        
        # Track removed obstacles to prevent re-reporting
        self.recently_removed: Set[Tuple[int, int]] = set()
        
        # Initialize obstacle classification from the grid
        self._initialize_from_grid()
    
    def _initialize_from_grid(self) -> None:
        """Initialize obstacle tracking from the current grid state"""
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                cell_type = self.grid.get_cell(x, y)
                if cell_type == CellType.PERMANENT_OBSTACLE:
                    self.obstacles[(x, y)] = {
                        'type': CellType.PERMANENT_OBSTACLE,
                        'confidence': 0.8,  # Initial confidence level
                        'lifespan': -1,  # -1 means unlimited/permanent
                        'age': 0
                    }
                elif cell_type == CellType.TEMPORARY_OBSTACLE:
                    self.obstacles[(x, y)] = {
                        'type': CellType.TEMPORARY_OBSTACLE,
                        'confidence': 0.8,
                        'lifespan': 10,  # Default temporary lifespan
                        'age': 0
                    }
                elif cell_type == CellType.SEMI_PERMANENT_OBSTACLE:
                    self.obstacles[(x, y)] = {
                        'type': CellType.SEMI_PERMANENT_OBSTACLE,
                        'confidence': 0.8,
                        'lifespan': 30,  # Default semi-permanent lifespan
                        'age': 0
                    }
    
    def add_obstacle(self, x: int, y: int, obstacle_type: CellType = CellType.PERMANENT_OBSTACLE, 
                    confidence: float = 0.8, lifespan: int = -1) -> bool:
        """
        Add a new obstacle to the grid and tracking system
        
        Args:
            x, y: Coordinates
            obstacle_type: Type of obstacle (from CellType enum)
            confidence: Initial confidence level (0.0-1.0)
            lifespan: Number of cycles the obstacle will exist (-1=permanent)
            
        Returns:
            bool: True if obstacle was added successfully
        """
        if not self.grid.in_bounds(x, y):
            print(f"Cannot add obstacle at ({x}, {y}): position out of bounds")
            return False
            
        cell_type = self.grid.get_cell(x, y)
        valid_types = [CellType.EMPTY, CellType.PERMANENT_OBSTACLE, 
                      CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]
                      
        if cell_type not in valid_types:
            print(f"Cannot add obstacle at ({x}, {y}): position occupied by non-obstacle")
            return False
        
        # If there's already an obstacle of a different type, clear it first
        if cell_type in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
            if cell_type != obstacle_type:
                self.remove_obstacle(x, y)
        
        # Update grid with the new obstacle type
        result = self.grid.set_cell(x, y, obstacle_type)
        if not result:
            print(f"Failed to set grid cell at ({x}, {y}) to obstacle type {obstacle_type}")
            return False
        
        # Store obstacle metadata
        self.obstacles[(x, y)] = {
            'type': obstacle_type,
            'confidence': confidence,
            'lifespan': lifespan,
            'age': 0
        }
        
        # Remove from recently removed set if it was there
        if (x, y) in self.recently_removed:
            self.recently_removed.remove((x, y))
        
        print(f"Added {self._get_obstacle_name(obstacle_type)} obstacle at ({x}, {y})" + 
              (f" with lifespan {lifespan}" if lifespan > 0 else ""))
        return True
    
    def _get_obstacle_name(self, obstacle_type: CellType) -> str:
        """Get a human-readable name for an obstacle type"""
        return {
            CellType.PERMANENT_OBSTACLE: "permanent",
            CellType.TEMPORARY_OBSTACLE: "temporary",
            CellType.SEMI_PERMANENT_OBSTACLE: "semi-permanent"
        }.get(obstacle_type, "unknown")
    
    def add_temporary_obstacle(self, x: int, y: int, lifespan: int = 10) -> bool:
        """Add a temporary obstacle with specified lifespan"""
        return self.add_obstacle(x, y, obstacle_type=CellType.TEMPORARY_OBSTACLE, 
                               confidence=0.9, lifespan=lifespan)
    
    def add_semi_permanent_obstacle(self, x: int, y: int, lifespan: int = 30) -> bool:
        """Add a semi-permanent obstacle with specified lifespan"""
        return self.add_obstacle(x, y, obstacle_type=CellType.SEMI_PERMANENT_OBSTACLE, 
                               confidence=0.7, lifespan=lifespan)
    
    def remove_obstacle(self, x: int, y: int) -> bool:
        """Remove an obstacle from the grid and tracking system"""
        if not self.grid.in_bounds(x, y):
            return False
            
        cell_type = self.grid.get_cell(x, y)
        obstacle_types = [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, 
                         CellType.SEMI_PERMANENT_OBSTACLE]
                         
        if cell_type not in obstacle_types:
            return False
        
        # Clear the cell in the grid
        if not self.grid.clear_cell(x, y):
            print(f"Warning: Failed to clear obstacle at ({x}, {y})")
            return False
        
        # Remove from tracking
        if (x, y) in self.obstacles:
            del self.obstacles[(x, y)]
            
            # Add to recently removed set to avoid re-reporting
            self.recently_removed.add((x, y))
            
            return True
        
        # Add to recently removed even if not found in tracking
        self.recently_removed.add((x, y))
        return True
    
    def register_robot_interaction(self, robot_id: int, x: int, y: int, success: bool) -> None:
        """
        Register a robot's interaction with an obstacle
        
        Args:
            robot_id: ID of the robot
            x, y: Coordinates of the obstacle
            success: Whether the robot successfully navigated past the obstacle
        """
        if robot_id not in self.robot_interactions:
            self.robot_interactions[robot_id] = {}
        
        if (x, y) not in self.robot_interactions[robot_id]:
            self.robot_interactions[robot_id][(x, y)] = {'attempts': 0, 'successes': 0, 'last_seen': 0}
        
        self.robot_interactions[robot_id][(x, y)]['attempts'] += 1
        if success:
            self.robot_interactions[robot_id][(x, y)]['successes'] += 1
        self.robot_interactions[robot_id][(x, y)]['last_seen'] = 0  # Reset age counter
        
        # Update obstacle classification based on interaction
        self._update_classification(x, y, success)
    
    def _update_classification(self, x: int, y: int, success: bool) -> None:
        """Update obstacle classification based on robot interaction"""
        if (x, y) not in self.obstacles:
            return
        
        obstacle = self.obstacles[(x, y)]
        cell_type = self.grid.get_cell(x, y)
        obstacle_types = [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, 
                         CellType.SEMI_PERMANENT_OBSTACLE]
        
        # If a robot successfully navigates where an obstacle was thought to be,
        # reduce confidence or consider reclassifying
        if success and cell_type in obstacle_types:
            obstacle['confidence'] -= 0.2
            
            # If confidence drops too low, consider reclassifying
            if obstacle['confidence'] < 0.3:
                if obstacle['type'] == CellType.PERMANENT_OBSTACLE:  # Permanent -> Semi-permanent
                    obstacle['type'] = CellType.SEMI_PERMANENT_OBSTACLE
                    obstacle['lifespan'] = 30
                    obstacle['confidence'] = 0.7
                    self.grid.set_cell(x, y, CellType.SEMI_PERMANENT_OBSTACLE)
                    print(f"Reclassified obstacle at ({x}, {y}) from permanent to semi-permanent")
                elif obstacle['type'] == CellType.SEMI_PERMANENT_OBSTACLE:  # Semi-permanent -> Temporary
                    obstacle['type'] = CellType.TEMPORARY_OBSTACLE
                    obstacle['lifespan'] = 10
                    obstacle['confidence'] = 0.8
                    self.grid.set_cell(x, y, CellType.TEMPORARY_OBSTACLE)
                    print(f"Reclassified obstacle at ({x}, {y}) from semi-permanent to temporary")
        
        # If a robot cannot navigate where we thought there was no obstacle,
        # add a new obstacle with appropriate classification
        elif not success and cell_type == CellType.EMPTY:
            self.add_obstacle(x, y, obstacle_type=CellType.TEMPORARY_OBSTACLE, 
                            confidence=0.6, lifespan=10)
            print(f"Detected new temporary obstacle at ({x}, {y}) from failed navigation")
    
    def update_cycle(self) -> int:
        """
        Update all obstacles for one simulation cycle
        - Age obstacles
        - Remove expired temporary obstacles
        - Update confidence levels
        
        Returns:
            int: Number of obstacles removed
        """
        obstacles_to_remove = []
        
        for pos, obstacle in list(self.obstacles.items()):
            x, y = pos
            
            # Skip permanent obstacles
            if obstacle['lifespan'] == -1:
                continue
            
            # Age the obstacle
            obstacle['age'] += 1
            
            # Check if the obstacle has expired
            if obstacle['age'] >= obstacle['lifespan']:
                obstacles_to_remove.append(pos)
            
            # Age robot interactions
            for robot_data in self.robot_interactions.values():
                if pos in robot_data:
                    robot_data[pos]['last_seen'] += 1
        
        # Remove expired obstacles
        removed_count = 0
        for pos in obstacles_to_remove:
            x, y = pos
            # Skip if this position was removed recently
            if pos in self.recently_removed:
                continue
                
            # Only report if obstacle is still on the grid
            cell_type = self.grid.get_cell(x, y)
            if cell_type in [CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                print(f"Removing expired obstacle at ({x}, {y})")
                
            if self.remove_obstacle(x, y):
                removed_count += 1
        
        # Clear the recently removed set periodically to avoid memory buildup
        if self.recently_removed and len(self.recently_removed) > 50:
            self.recently_removed.clear()
        
        return removed_count
    
    def is_obstacle_temporary(self, x: int, y: int) -> bool:
        """Check if an obstacle is temporary"""
        if not self.grid.in_bounds(x, y):
            return False
        return self.grid.get_cell(x, y) == CellType.TEMPORARY_OBSTACLE
    
    def is_obstacle_semi_permanent(self, x: int, y: int) -> bool:
        """Check if an obstacle is semi-permanent"""
        if not self.grid.in_bounds(x, y):
            return False
        return self.grid.get_cell(x, y) == CellType.SEMI_PERMANENT_OBSTACLE
    
    def is_obstacle_permanent(self, x: int, y: int) -> bool:
        """Check if an obstacle is permanent"""
        if not self.grid.in_bounds(x, y):
            return False
        return self.grid.get_cell(x, y) == CellType.PERMANENT_OBSTACLE
    
    def get_obstacle_remaining_lifespan(self, x: int, y: int) -> int:
        """Get the remaining lifespan of an obstacle, or -1 if permanent"""
        if not self.grid.in_bounds(x, y):
            return -1
            
        if (x, y) not in self.obstacles:
            return -1
            
        obstacle = self.obstacles[(x, y)]
        
        if obstacle['lifespan'] == -1:
            return -1
            
        return max(0, obstacle['lifespan'] - obstacle['age'])
    
    def get_obstacle_info(self, x: int, y: int) -> Optional[Dict]:
        """Get complete information about an obstacle"""
        if not self.grid.in_bounds(x, y):
            return None
            
        if (x, y) not in self.obstacles:
            return None
            
        return self.obstacles[(x, y)]
    
    def share_obstacle_knowledge(self, source_robot_id: int, target_robot_id: int) -> int:
        """
        Share obstacle knowledge between robots
        
        Args:
            source_robot_id: ID of the source robot
            target_robot_id: ID of the target robot
            
        Returns:
            int: Number of observations shared
        """
        if source_robot_id not in self.robot_interactions or target_robot_id not in self.robot_interactions:
            return 0
            
        shared_count = 0
        
        for pos, source_data in self.robot_interactions[source_robot_id].items():
            # Only share relatively recent observations
            if source_data['last_seen'] > 15:  # Skip old observations
                continue
                
            if pos not in self.robot_interactions[target_robot_id]:
                self.robot_interactions[target_robot_id][pos] = source_data.copy()
                shared_count += 1
            else:
                # Target robot already has some knowledge, update with source knowledge
                target_data = self.robot_interactions[target_robot_id][pos]
                
                # Only update if source has more recent information
                if source_data['last_seen'] < target_data['last_seen']:
                    self.robot_interactions[target_robot_id][pos] = source_data.copy()
                    shared_count += 1
        
        if shared_count > 0:
            print(f"Robot {source_robot_id} shared {shared_count} obstacle observations with Robot {target_robot_id}")
            
        return shared_count