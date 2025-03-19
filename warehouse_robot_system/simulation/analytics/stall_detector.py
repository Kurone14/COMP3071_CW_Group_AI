from typing import List, Dict, Tuple, Any, Optional
from core.models.grid import Grid


class StallDetector:
    """
    Detects and resolves simulation stalls by tracking progress and applying
    increasingly aggressive interventions when progress stalls.
    """
    
    def __init__(self, grid: Grid, path_finder):
        """
        Initialize the stall detector
        
        Args:
            grid: The environment grid
            path_finder: PathFinder instance for calculating paths
        """
        self.grid = grid
        self.path_finder = path_finder
        
        self.loop_count = 0
        self.last_progress_at = 0
        self.previous_picked_count = 0
        self.previous_delivered_count = 0
    
    def reset(self) -> None:
        """Reset all tracking counters"""
        self.loop_count = 0
        self.last_progress_at = 0
        self.previous_picked_count = 0
        self.previous_delivered_count = 0
        print("Stall detector reset")
    
    def check_progress(self, robots: List[Any], items: List[Any]) -> Tuple[int, List[Any]]:
        """
        Check if the simulation is making progress
        
        Args:
            robots: List of all robots
            items: List of all items
            
        Returns:
            Tuple of (stall_time, remaining_items)
        """
        self.loop_count += 1
        
        remaining_items = [item for item in items if not item.picked]
        
        current_picked_count = sum(1 for item in items if item.picked)
        
        if current_picked_count > self.previous_picked_count:
            self.last_progress_at = self.loop_count
            print(f"Progress made! Items picked: {current_picked_count}/{len(items)}")
        self.previous_picked_count = current_picked_count
        
        current_delivered_count = len(items) - (current_picked_count + len(remaining_items))
        
        if current_delivered_count > self.previous_delivered_count:
            self.last_progress_at = self.loop_count
            print(f"Progress made! Items delivered: {current_delivered_count}/{len(items)}")
        self.previous_delivered_count = current_delivered_count
        
        return self.loop_count - self.last_progress_at, remaining_items
    
    def level1_recovery(self, robots: List[Any], items: List[Any], stall_time: int) -> bool:
        """
        Level 1: Mild stall (15 cycles) - standard recovery
        Free stuck assigned items and reset robots with no path to target
        
        Args:
            robots: List of all robots
            items: List of all items
            stall_time: How long the simulation has been stalled
            
        Returns:
            bool: True if changes were made
        """
        if stall_time <= 15:
            return False
            
        print(f"WARNING: Simulation stalled for {stall_time} cycles")
        
        stuck_items = [item for item in items if not item.picked and item.assigned]
        if stuck_items:
            print(f"Freeing {len(stuck_items)} stuck assigned items")
            for item in stuck_items:
                item.assigned = False
        
        for robot in robots:
            if not robot.path and robot.target_items:
                print(f"Robot {robot.id} has target items but no path. Resetting.")
                for item in robot.target_items:
                    item.assigned = False
                robot.target_items = []
                
        return True
    
    def level2_recovery(self, robots: List[Any], items: List[Any], stall_time: int) -> bool:
        """
        Level 2: Medium stall (20 cycles) - stronger interventions
        Teleport stuck robots to drop point and assign unassigned items
        
        Args:
            robots: List of all robots
            items: List of all items
            stall_time: How long the simulation has been stalled
            
        Returns:
            bool: True if changes were made
        """
        if stall_time <= 20:
            return False
            
        print(f"MEDIUM STALL: Taking stronger measures after {stall_time} cycles")
        made_changes = False
        
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            # Choose robot with most items and no path
            target_robot = max(robots_with_items, 
                             key=lambda r: (not bool(r.path), len(r.carrying_items)))
            
            if not target_robot.path or len(target_robot.path) > 15:
                print(f"TELEPORT: Moving robot {target_robot.id} with {len(target_robot.carrying_items)} items to drop point")
                
                # Update grid and robot position
                self.grid.set_cell(target_robot.x, target_robot.y, 0)
                
                drop_x, drop_y = self.grid.drop_point
                target_robot.x, target_robot.y = drop_x, drop_y
                from core.models.grid import CellType
                self.grid.set_cell(drop_x, drop_y, CellType.ROBOT)
                target_robot.path = [] 
                
                self.last_progress_at = self.loop_count
                made_changes = True
        
        unassigned_items = [item for item in items if not item.picked and not item.assigned]
        if unassigned_items:
            print(f"AGGRESSIVE ITEM ASSIGNMENT: {len(unassigned_items)} items remain unassigned")
            
            # Find an idle robot
            target_robot = None
            for robot in robots:
                if not robot.path and not robot.carrying_items:
                    target_robot = robot
                    break
            
            # If no idle robot, find the one closest to finishing its path
            if not target_robot:
                robots_by_path = [(r, len(r.path)) for r in robots if not r.carrying_items]
                if robots_by_path:
                    robots_by_path.sort(key=lambda x: x[1])
                    target_robot = robots_by_path[0][0]
            
            if target_robot:
                # Find closest item
                for item in sorted(unassigned_items, 
                                 key=lambda x: abs(x.x - target_robot.x) + abs(x.y - target_robot.y)):
                    print(f"FORCING: Sending robot {target_robot.id} to item #{item.id}")
                    item.assigned = True
                    target_robot.target_items = [item]
                    target_robot.path = self.path_finder.find_path(
                        (target_robot.y, target_robot.x), 
                        (item.y, item.x), 
                        robots,
                        target_robot.id
                    )
                    
                    # If can't find path, teleport robot closer to item
                    if not target_robot.path:
                        print(f"TELEPORT: Moving robot {target_robot.id} to item #{item.id}")
                        self.grid.set_cell(target_robot.x, target_robot.y, 0)
                        
                        # Find empty cell near item
                        teleport_x, teleport_y = item.x, item.y
                        directions = [(0,0), (0,1), (1,0), (0,-1), (-1,0)]
                        
                        for dx, dy in directions:
                            test_x, test_y = item.x + dx, item.y + dy
                            if self.grid.in_bounds(test_x, test_y) and self.grid.is_cell_empty(test_x, test_y):
                                teleport_x, teleport_y = test_x, test_y
                                break
                        
                        target_robot.x, target_robot.y = teleport_x, teleport_y
                        from core.models.grid import CellType
                        self.grid.set_cell(teleport_x, teleport_y, CellType.ROBOT)
                        
                        target_robot.path = self.path_finder.find_path(
                            (target_robot.y, target_robot.x), 
                            (item.y, item.x), 
                            robots,
                            target_robot.id
                        )
                    
                    self.last_progress_at = self.loop_count
                    made_changes = True
                    break
                    
        return made_changes
    
    def level3_recovery(self, robots: List[Any], items: List[Any], stall_time: int, 
                      remaining_items: List[Any]) -> bool:
        """
        Level 3: Severe stall (35 cycles) - extreme measures
        Teleport all robots with items to drop point, teleport robots to unreachable items
        
        Args:
            robots: List of all robots
            items: List of all items
            stall_time: How long the simulation has been stalled
            remaining_items: List of remaining unpicked items
            
        Returns:
            bool: True if changes were made
        """
        if stall_time <= 35:
            return False
            
        print(f"CRITICAL: Severe stall for {stall_time} cycles - taking extreme measures")
        made_changes = False
        
        # Teleport all robots with items to drop point
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            print(f"EMERGENCY: Teleporting ALL {len(robots_with_items)} robots with items to drop point")
            
            # Find positions around drop point
            drop_area = []
            drop_x, drop_y = self.grid.drop_point
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue  # Skip the drop point itself
                    test_x, test_y = drop_x + dx, drop_y + dy
                    if self.grid.in_bounds(test_x, test_y):
                        drop_area.append((test_x, test_y))
            
            if not drop_area:
                drop_area = [self.grid.drop_point]
            
            for i, robot in enumerate(robots_with_items):
                self.grid.set_cell(robot.x, robot.y, 0)
                
                if i < len(drop_area):
                    robot.x, robot.y = drop_area[i]
                else:
                    robot.x, robot.y = self.grid.drop_point
                
                from core.models.grid import CellType
                self.grid.set_cell(robot.x, robot.y, CellType.ROBOT)
                robot.path = []
            
            self.last_progress_at = self.loop_count
            made_changes = True
        
        # Teleport a robot to unreachable items
        if remaining_items:
            print(f"CRITICAL: {len(remaining_items)} items still unreachable after {stall_time} cycles")
            
            # Find an available robot
            available_robot = None
            for robot in robots:
                if not robot.carrying_items:
                    available_robot = robot
                    break
            
            if available_robot and remaining_items:
                item = remaining_items[0]
                print(f"EMERGENCY: Teleporting robot {available_robot.id} to unreachable item #{item.id}")
                
                self.grid.set_cell(available_robot.x, available_robot.y, 0)
                
                available_robot.x, available_robot.y = item.x, item.y
                from core.models.grid import CellType
                self.grid.set_cell(item.x, item.y, CellType.ROBOT)
                
                available_robot.target_items = [item]
                item.assigned = True
                
                self.last_progress_at = self.loop_count
                made_changes = True
                
        return made_changes
    
    def level4_recovery(self, robots: List[Any], items: List[Any], stall_time: int, 
                      remaining_items: List[Any]) -> bool:
        """
        Level 4: Force simulation completion (50 cycles)
        Instantly complete all remaining items
        
        Args:
            robots: List of all robots
            items: List of all items
            stall_time: How long the simulation has been stalled
            remaining_items: List of remaining unpicked items
            
        Returns:
            bool: True if simulation was force-completed
        """
        if stall_time <= 50:
            return False
            
        print(f"GIVING UP: Force completing simulation after {stall_time} cycles of stall")
        
        if remaining_items:
            print(f"Completing by teleporting all {len(remaining_items)} remaining items to drop point")
            for item in remaining_items:
                item.picked = True
        
        for robot in robots:
            if robot.carrying_items:
                print(f"Force delivering items carried by robot {robot.id}")
                robot.carrying_items = []
                robot.current_weight = 0
                robot.path = []
                
        return True
        
    def check_timeout(self) -> bool:
        """
        Check if the simulation has been running too long
        
        Returns:
            bool: True if simulation has timed out
        """
        return self.loop_count > 200  # Timeout after 200 cycles