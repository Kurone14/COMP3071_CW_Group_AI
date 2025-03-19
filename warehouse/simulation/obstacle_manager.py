class ObstacleManager:
    """
    Manages obstacles in the warehouse environment, including classification,
    tracking, and lifecycle management of different obstacle types.
    
    Obstacle Types:
    - 0: Empty space
    - 1: Permanent obstacle (walls, fixed structures)
    - 2: Item
    - 3: Robot
    - 4: Drop point
    - 5: Temporary obstacle (short duration, will disappear)
    - 6: Semi-permanent obstacle (longer duration)
    """
    
    def __init__(self, grid, width, height):
        """Initialize the obstacle manager with the grid reference"""
        self.grid = grid
        self.width = width
        self.height = height
        
        # Store obstacle metadata including type, confidence, and lifespan
        # Key: (x, y) coordinates, Value: {'type': int, 'confidence': float, 'lifespan': int, 'age': int}
        self.obstacles = {}
        
        # Track obstacle interactions for each robot
        # Key: robot_id, Value: {(x, y): {'attempts': int, 'last_seen': timestamp}}
        self.robot_interactions = {}
        
        # Initialize obstacle classification from the grid
        self._initialize_from_grid()
    
    def _initialize_from_grid(self):
        """Initialize obstacle tracking from the current grid state"""
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:  # Existing obstacles are initially classified as permanent
                    self.obstacles[(x, y)] = {
                        'type': 1,  # Permanent
                        'confidence': 0.8,  # Initial confidence level
                        'lifespan': -1,  # -1 means unlimited/permanent
                        'age': 0
                    }
    
    def update_grid(self, grid):
        """Update the grid reference and reinitialize"""
        self.grid = grid
        self._initialize_from_grid()
    
    def add_obstacle(self, x, y, obstacle_type=1, confidence=0.8, lifespan=-1):
        """
        Add a new obstacle to the grid and tracking system
        
        Args:
            x, y: Coordinates
            obstacle_type: 1=Permanent, 5=Temporary, 6=Semi-permanent
            confidence: Initial confidence level (0.0-1.0)
            lifespan: Number of cycles the obstacle will exist (-1=permanent)
        """
        if not (0 <= x < self.width and 0 <= y < self.height):
            print(f"Cannot add obstacle at ({x}, {y}): position out of bounds")
            return False
            
        if self.grid[y][x] not in [0, 1, 5, 6]:  # Don't overwrite items, robots, etc.
            print(f"Cannot add obstacle at ({x}, {y}): position occupied by non-obstacle")
            return False
        
        # Update grid with the new obstacle type
        self.grid[y][x] = obstacle_type
        
        # Store obstacle metadata
        self.obstacles[(x, y)] = {
            'type': obstacle_type,
            'confidence': confidence,
            'lifespan': lifespan,
            'age': 0
        }
        
        print(f"Added {self._get_obstacle_name(obstacle_type)} obstacle at ({x}, {y})" + 
              (f" with lifespan {lifespan}" if lifespan > 0 else ""))
        return True
    
    def _get_obstacle_name(self, obstacle_type):
        """Get a human-readable name for an obstacle type"""
        return {
            1: "permanent",
            5: "temporary",
            6: "semi-permanent"
        }.get(obstacle_type, "unknown")
    
    def add_temporary_obstacle(self, x, y, lifespan=10):
        """Add a temporary obstacle with specified lifespan"""
        return self.add_obstacle(x, y, obstacle_type=5, confidence=0.9, lifespan=lifespan)
    
    def add_semi_permanent_obstacle(self, x, y, lifespan=30):
        """Add a semi-permanent obstacle with specified lifespan"""
        return self.add_obstacle(x, y, obstacle_type=6, confidence=0.7, lifespan=lifespan)
    
    def remove_obstacle(self, x, y):
        """Remove an obstacle from the grid and tracking system"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
            
        if self.grid[y][x] not in [1, 5, 6]:
            return False
        
        self.grid[y][x] = 0  # Set to empty space
        
        if (x, y) in self.obstacles:
            del self.obstacles[(x, y)]
        
        return True
    
    def register_robot_interaction(self, robot_id, x, y, success):
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
    
    def _update_classification(self, x, y, success):
        """Update obstacle classification based on robot interaction"""
        if (x, y) not in self.obstacles:
            return
        
        obstacle = self.obstacles[(x, y)]
        
        # If a robot successfully navigates where an obstacle was thought to be,
        # reduce confidence or consider reclassifying
        if success and self.grid[y][x] in [1, 5, 6]:
            obstacle['confidence'] -= 0.2
            
            # If confidence drops too low, consider reclassifying
            if obstacle['confidence'] < 0.3:
                if obstacle['type'] == 1:  # Permanent -> Semi-permanent
                    obstacle['type'] = 6
                    obstacle['lifespan'] = 30
                    obstacle['confidence'] = 0.7
                    self.grid[y][x] = 6
                    print(f"Reclassified obstacle at ({x}, {y}) from permanent to semi-permanent")
                elif obstacle['type'] == 6:  # Semi-permanent -> Temporary
                    obstacle['type'] = 5
                    obstacle['lifespan'] = 10
                    obstacle['confidence'] = 0.8
                    self.grid[y][x] = 5
                    print(f"Reclassified obstacle at ({x}, {y}) from semi-permanent to temporary")
        
        # If a robot cannot navigate where we thought there was no obstacle,
        # add a new obstacle with appropriate classification
        elif not success and self.grid[y][x] == 0:
            self.add_obstacle(x, y, obstacle_type=5, confidence=0.6, lifespan=10)
            print(f"Detected new temporary obstacle at ({x}, {y}) from failed navigation")
    
    def update_cycle(self):
        """
        Update all obstacles for one simulation cycle
        - Age obstacles
        - Remove expired temporary obstacles
        - Update confidence levels
        """
        obstacles_to_remove = []
        
        for pos, obstacle in self.obstacles.items():
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
        for pos in obstacles_to_remove:
            x, y = pos
            print(f"Removing expired obstacle at ({x}, {y})")
            self.remove_obstacle(x, y)
        
        return len(obstacles_to_remove)
    
    def is_obstacle_temporary(self, x, y):
        """Check if an obstacle is temporary (type 5)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.grid[y][x] == 5
    
    def is_obstacle_semi_permanent(self, x, y):
        """Check if an obstacle is semi-permanent (type 6)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.grid[y][x] == 6
    
    def is_obstacle_permanent(self, x, y):
        """Check if an obstacle is permanent (type 1)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        return self.grid[y][x] == 1
    
    def get_obstacle_remaining_lifespan(self, x, y):
        """Get the remaining lifespan of an obstacle, or -1 if permanent"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return -1
            
        if (x, y) not in self.obstacles:
            return -1
            
        obstacle = self.obstacles[(x, y)]
        
        if obstacle['lifespan'] == -1:
            return -1
            
        return max(0, obstacle['lifespan'] - obstacle['age'])
    
    def get_obstacle_info(self, x, y):
        """Get complete information about an obstacle"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return None
            
        if (x, y) not in self.obstacles:
            return None
            
        return self.obstacles[(x, y)]
    
    def share_obstacle_knowledge(self, source_robot_id, target_robot_id):
        """Share obstacle knowledge between robots"""
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