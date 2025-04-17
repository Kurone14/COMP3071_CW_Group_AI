from typing import List, Dict, Tuple, Any, Optional
from core.models.grid import Grid, CellType


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
        self.intervention_history = {}  # Track interventions applied to robots
    
    def reset(self) -> None:
        """Reset all tracking counters"""
        self.loop_count = 0
        self.last_progress_at = 0
        self.previous_picked_count = 0
        self.previous_delivered_count = 0
        self.intervention_history = {}
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
        
        # Check for robots stuck in "To Item" status first (every 5 cycles)
        if self.loop_count % 5 == 0:
            if self.check_stuck_to_item_robots(robots, items):
                # If interventions were made, reset the stall time
                self.last_progress_at = self.loop_count
        
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
        
        # Count robots that have moved
        moved_robots = sum(1 for robot in robots if robot.steps > 0)
        
        # Also track if we have idle robots but unassigned items
        idle_robots = [r for r in robots if not r.path and not r.carrying_items]
        unassigned_items = [i for i in items if not i.picked and not i.assigned]
        
        if idle_robots and unassigned_items:
            # This is a potential stall situation - robots are idle but items need picking
            print(f"WARNING: {len(idle_robots)} idle robots but {len(unassigned_items)} unassigned items")
            
            # If this persists for 10 cycles, try to help
            if self.loop_count - self.last_progress_at >= 10:
                print("INTERVENTION: Trying to assign items to idle robots")
                
                # For each idle robot, try to assign it to an unassigned item
                for robot in idle_robots:
                    if not unassigned_items:
                        break
                        
                    # Find closest unassigned item
                    closest_item = min(unassigned_items, 
                                    key=lambda i: abs(i.x - robot.x) + abs(i.y - robot.y))
                    
                    # Try to find a path
                    path = self.path_finder.find_path(
                        (robot.y, robot.x),
                        (closest_item.y, closest_item.x),
                        [],  # Don't consider other robots for this emergency path
                        robot.id
                    )
                    
                    if path:
                        print(f"Assigning robot {robot.id} to item #{closest_item.id}")
                        robot.target_items = [closest_item]
                        closest_item.assigned = True
                        robot.path = path
                        unassigned_items.remove(closest_item)
                        self.last_progress_at = self.loop_count  # Reset stall counter
                    else:
                        print(f"Robot {robot.id} can't reach item #{closest_item.id}")
        
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
        
        # NEW: Check for robots near drop point with no path
        self._check_robots_near_drop_point(robots)
                
        return True
    
    def _check_robots_near_drop_point(self, robots: List[Any]) -> bool:
        """
        Check for robots stuck near the drop point
        
        Args:
            robots: List of all robots
            
        Returns:
            bool: True if any robot was helped
        """
        made_changes = False
        drop_x, drop_y = self.grid.drop_point
        
        for robot in robots:
            if robot.carrying_items and not robot.path:
                # Calculate distance to drop point
                distance = abs(robot.x - drop_x) + abs(robot.y - drop_y)
                
                # If robot is close to drop point but can't reach it
                if distance <= 3:
                    print(f"Robot {robot.id} stuck near drop point (distance: {distance})")
                    
                    # Try to find a path around obstacles
                    robot.path = self.path_finder.find_path(
                        (robot.y, robot.x),
                        (drop_y, drop_x),
                        None,  # No robot avoidance for emergency path
                        robot.id,
                        robot.current_weight
                    )
                    
                    if robot.path:
                        print(f"Found new path for robot {robot.id} to drop point with {len(robot.path)} steps")
                        made_changes = True
                    else:
                        # Count this robot's interventions
                        self.intervention_history[robot.id] = self.intervention_history.get(robot.id, 0) + 1
                        
                        # If multiple interventions, more aggressive action
                        if self.intervention_history[robot.id] >= 2:
                            print(f"TELEPORT: Moving robot {robot.id} to drop point after repeated interventions")
                            
                            # Update grid and robot position
                            self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                            robot.x, robot.y = drop_x, drop_y
                            self.grid.set_cell(drop_x, drop_y, CellType.ROBOT)
                            made_changes = True
        
        return made_changes
    
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
        
        # Get drop point coordinates
        drop_x, drop_y = self.grid.drop_point
        
        # First, handle robots with items that are stuck
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            # Find robots that might be stuck near the drop point
            for robot in robots_with_items:
                # If no path or long path, and close to drop point
                if (not robot.path or len(robot.path) > 10) and \
                   abs(robot.x - drop_x) + abs(robot.y - drop_y) <= 5:
                    print(f"TELEPORT: Moving robot {robot.id} with {len(robot.carrying_items)} items to drop point")
                    
                    # Update grid and robot position
                    self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                    
                    robot.x, robot.y = drop_x, drop_y
                    self.grid.set_cell(drop_x, drop_y, CellType.ROBOT)
                    robot.path = []
                    
                    self.last_progress_at = self.loop_count
                    made_changes = True
                    break
        
        # If still no progress, assign unassigned items
        if not made_changes:
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
                            self.grid.set_cell(target_robot.x, target_robot.y, CellType.EMPTY)
                            
                            # Find empty cell near item
                            teleport_x, teleport_y = item.x, item.y
                            directions = [(0,0), (0,1), (1,0), (0,-1), (-1,0)]
                            
                            for dx, dy in directions:
                                test_x, test_y = item.x + dx, item.y + dy
                                if self.grid.in_bounds(test_x, test_y) and self.grid.is_cell_empty(test_x, test_y):
                                    teleport_x, teleport_y = test_x, test_y
                                    break
                            
                            target_robot.x, target_robot.y = teleport_x, teleport_y
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
        
        # Get drop point coordinates
        drop_x, drop_y = self.grid.drop_point
        
        # Teleport all robots with items to drop point
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            print(f"EMERGENCY: Teleporting ALL {len(robots_with_items)} robots with items to drop point")
            
            # Find positions around drop point
            drop_area = []
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue  # Skip the drop point itself
                    test_x, test_y = drop_x + dx, drop_y + dy
                    if self.grid.in_bounds(test_x, test_y):
                        drop_area.append((test_x, test_y))
            
            if not drop_area:
                drop_area = [(drop_x, drop_y)]  # Use drop point if no surrounding cells available
            
            for i, robot in enumerate(robots_with_items):
                self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                
                if i < len(drop_area):
                    robot.x, robot.y = drop_area[i]
                else:
                    robot.x, robot.y = drop_area[i % len(drop_area)]
                
                self.grid.set_cell(robot.x, robot.y, CellType.ROBOT)
                robot.path = []
                
                # Clear trajectory for this robot
                if hasattr(self.simulation, 'movement_controller') and \
                hasattr(self.simulation.movement_controller, 'trajectory_tracker') and \
                self.simulation.movement_controller.trajectory_tracker:
                    trajectory_tracker = self.simulation.movement_controller.trajectory_tracker
                    if robot.id in trajectory_tracker.trajectories:
                        trajectory_tracker.trajectories[robot.id].clear()
                        # Also clear target information
                        if robot.id in trajectory_tracker.target_types:
                            del trajectory_tracker.target_types[robot.id]
                        if robot.id in trajectory_tracker.target_positions:
                            del trajectory_tracker.target_positions[robot.id]
            
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
                
                self.grid.set_cell(available_robot.x, available_robot.y, CellType.EMPTY)
                
                # Find a position next to the item
                teleport_x, teleport_y = item.x, item.y
                directions = [(0,0), (0,1), (1,0), (0,-1), (-1,0)]
                
                for dx, dy in directions:
                    test_x, test_y = item.x + dx, item.y + dy
                    if self.grid.in_bounds(test_x, test_y) and self.grid.is_cell_empty(test_x, test_y):
                        teleport_x, teleport_y = test_x, test_y
                        break
                
                available_robot.x, available_robot.y = teleport_x, teleport_y
                self.grid.set_cell(teleport_x, teleport_y, CellType.ROBOT)
                
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
        
        # Mark all remaining items as picked
        if remaining_items:
            print(f"Completing by teleporting all {len(remaining_items)} remaining items to drop point")
            for item in remaining_items:
                item.picked = True
        
        # Clear all robots' carried items
        for robot in robots:
            if robot.carrying_items:
                print(f"Force delivering items carried by robot {robot.id}")
                robot.carrying_items = []
                robot.current_weight = 0
                robot.path = []
                
        # Reset stuck counters
        self.last_progress_at = self.loop_count
                
        return True
        
    def check_timeout(self) -> bool:
        """
        Check if the simulation has been running too long without progress
        
        Returns:
            bool: True if simulation has timed out
        """
        # Consider a timeout if:
        # 1. The simulation has been running for more than 200 cycles
        # 2. There has been no progress for more than 50 cycles
        
        cycles_without_progress = self.loop_count - self.last_progress_at
        
        # If no progress for a long time, that's a timeout regardless of total time
        if cycles_without_progress > 50:
            self.logger.warning(f"Simulation timed out: No progress for {cycles_without_progress} cycles")
            return True
            
        # If running for a very long time, that's also a timeout
        if self.loop_count > 200:
            # Only time out if there are still items to deliver
            remaining_items = False
            for robot in self.robots:
                if robot.carrying_items:
                    remaining_items = True
                    break
                    
            if remaining_items:
                self.logger.warning(f"Simulation timed out: Running for {self.loop_count} cycles with undelivered items")
                return True
                
        return False
    

    def check_stuck_to_item_robots(self, robots: List[Any], items: List[Any]) -> bool:
        """
        Check for robots that are stuck in 'To Item' status but not moving
        
        Args:
            robots: List of all robots
            items: List of all items
            
        Returns:
            bool: True if any interventions were made
        """
        made_changes = False
        
        # Find robots that are in "To Item" status but not moving
        for robot in robots:
            # Skip robots that aren't targeting items or are carrying items
            if not robot.target_items or robot.carrying_items:
                continue
                
            # Check if robot has been assigned to an item but has no path or isn't making progress
            if robot.target_items and not robot.path and not robot.steps:
                # Get target item
                target_item = robot.target_items[0]
                print(f"Robot {robot.id} is stuck in 'To Item' status trying to reach item #{target_item.id} but not moving")
                
                # Try to find a path without considering other robots
                new_path = self.path_finder.find_path(
                    (robot.y, robot.x),
                    (target_item.y, target_item.x),
                    [],  # No robot avoidance
                    robot.id
                )
                
                if new_path:
                    print(f"Found new path for robot {robot.id} to item #{target_item.id}")
                    robot.path = new_path
                    made_changes = True
                else:
                    # Calculate distance to item
                    distance = abs(robot.x - target_item.x) + abs(robot.y - target_item.y)
                    print(f"Robot {robot.id} is {distance} cells away from item #{target_item.id} but can't find path")
                    
                    # If robot is far from item, teleport it closer
                    if distance > 3:
                        print(f"TELEPORT: Moving robot {robot.id} closer to item #{target_item.id}")
                        
                        # Calculate positions around item in increasing distance
                        positions = []
                        for d in range(1, 4):  # Try up to 3 cells away
                            for dx in range(-d, d+1):
                                for dy in range(-d, d+1):
                                    if abs(dx) + abs(dy) == d:  # Manhattan distance exactly d
                                        test_x = target_item.x + dx
                                        test_y = target_item.y + dy
                                        if self.grid.in_bounds(test_x, test_y) and self.grid.is_cell_empty(test_x, test_y):
                                            positions.append((test_x, test_y))
                        
                        # If positions found, teleport to the first available one
                        if positions:
                            # Update grid and robot position
                            from core.models.grid import CellType
                            self.grid.set_cell(robot.x, robot.y, CellType.EMPTY)
                            
                            teleport_x, teleport_y = positions[0]
                            robot.x, robot.y = teleport_x, teleport_y
                            self.grid.set_cell(teleport_x, teleport_y, CellType.ROBOT)
                            
                            # Try to find a path from new position
                            robot.path = self.path_finder.find_path(
                                (robot.y, robot.x),
                                (target_item.y, target_item.x),
                                [],
                                robot.id
                            )
                            
                            print(f"Teleported robot {robot.id} to ({teleport_x}, {teleport_y})")
                            made_changes = True
                    else:
                        # Robot is close but still can't reach, examine surroundings for obstacles
                        # Check if there are obstacles between robot and item
                        obstacles_found = self._check_obstacles_between(robot, target_item)
                        
                        if obstacles_found:
                            # Choose one obstacle to remove
                            obstacle_x, obstacle_y = obstacles_found[0]
                            print(f"Removing obstacle at ({obstacle_x}, {obstacle_y}) blocking robot {robot.id}")
                            
                            # Remove obstacle
                            self.grid.set_cell(obstacle_x, obstacle_y, CellType.EMPTY)
                            
                            # Try to find a path again
                            robot.path = self.path_finder.find_path(
                                (robot.y, robot.x),
                                (target_item.y, target_item.x),
                                [],
                                robot.id
                            )
                            
                            made_changes = True
        
        return made_changes

    def _check_obstacles_between(self, robot: Any, item: Any) -> List[Tuple[int, int]]:
        """
        Check for obstacles between robot and item
        
        Args:
            robot: Robot trying to reach item
            item: Target item
            
        Returns:
            List of (x, y) coordinates of obstacles found
        """
        from core.models.grid import CellType
        obstacles = []
        
        # Define a bounding box between robot and item
        min_x = min(robot.x, item.x)
        max_x = max(robot.x, item.x)
        min_y = min(robot.y, item.y)
        max_y = max(robot.y, item.y)
        
        # Expand slightly to catch obstacles just outside direct path
        min_x = max(0, min_x - 1)
        max_x = min(self.grid.width - 1, max_x + 1)
        min_y = max(0, min_y - 1)
        max_y = min(self.grid.height - 1, max_y + 1)
        
        # Check all cells in the bounding box
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                cell = self.grid.get_cell(x, y)
                if cell in [CellType.PERMANENT_OBSTACLE, CellType.TEMPORARY_OBSTACLE, CellType.SEMI_PERMANENT_OBSTACLE]:
                    # Calculate if obstacle is roughly between robot and item
                    # using area triangulation
                    robot_to_obstacle = abs(robot.x - x) + abs(robot.y - y)
                    obstacle_to_item = abs(x - item.x) + abs(y - item.y)
                    robot_to_item = abs(robot.x - item.x) + abs(robot.y - item.y)
                    
                    # If obstacle is on or near the path
                    if robot_to_obstacle + obstacle_to_item <= robot_to_item + 2:
                        obstacles.append((x, y))
        
        # Sort by distance to robot (closest first)
        obstacles.sort(key=lambda obs: abs(obs[0] - robot.x) + abs(obs[1] - robot.y))
        
        return obstacles