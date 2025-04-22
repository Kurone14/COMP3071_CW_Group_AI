from typing import List, Dict, Tuple, Set, Optional, Any
import random
from core.models.grid import Grid


class ItemAssigner:
    """
    Responsible for assigning items to robots in an optimal way,
    considering capacity, distance, and clustering of items.
    """
    
    def __init__(self, grid: Grid, path_finder):
        """
        Initialize the item assigner
        
        Args:
            grid: The environment grid
            path_finder: PathFinder instance for calculating paths
        """
        self.grid = grid
        self.path_finder = path_finder
        self.failed_attempts: Dict[Tuple[int, Any], int] = {}  # Track failed assignments
        self.max_attempts = 3  # Maximum number of attempts before giving up
        
        # Add clustering toggle flag (enabled by default)
        self.clustering_enabled = True
    
    def assign_items_to_robots(self, robots: List[Any], items: List[Any], drop_point: Tuple[int, int]) -> bool:
        """
        Advanced item assignment with capacity optimization and clustering
        
        Args:
            robots: List of robots
            items: List of items
            drop_point: Dropoff point coordinates (x, y)
            
        Returns:
            bool: True if there are fewer unassigned items than total items
        """
        unassigned_items = [item for item in items if not item.picked and not item.assigned]
        print("\n--- Item Assignment Cycle ---")
        print(f"Unassigned items: {len(unassigned_items)}")
        
        # Handle robots at drop point
        self._handle_drop_point_deliveries(robots, drop_point)
        
        # Handle robots carrying items without paths
        self._handle_stuck_carrying_robots(robots, drop_point, unassigned_items)
        
        # Categorize robots by their status
        idle_robots = [robot for robot in robots if not robot.path and not robot.carrying_items]
        carrying_robots = [robot for robot in robots if robot.carrying_items]
        moving_robots = [robot for robot in robots if robot.path and not robot.carrying_items]
        
        print(f"Robot status: {len(idle_robots)} idle, {len(carrying_robots)} carrying, {len(moving_robots)} moving to items")
        
        # Ensure carrying robots have paths to drop point
        self._ensure_carrying_robots_have_paths(carrying_robots, drop_point)
        
        # Handle moving robots without paths
        self._handle_stuck_moving_robots(moving_robots, robots, unassigned_items)
        
        # Assign items to idle robots
        self._assign_items_to_idle_robots(idle_robots, unassigned_items, robots, drop_point)
        
        # Periodically reset failed attempts history to prevent deadlocks
        if random.random() < 0.1:  
            self.failed_attempts = {}
            print("Reset failed attempts history")
        
        # Check for any remaining unassigned items with idle robots
        self._check_remaining_unassigned(items, robots)
        
        return len(unassigned_items) < len(items)
    
    def _handle_drop_point_deliveries(self, robots: List[Any], drop_point: Tuple[int, int]) -> None:
        """Handle robots that are at the drop point with items"""
        for robot in robots:
            if robot.carrying_items and (robot.x, robot.y) == drop_point:
                print(f"Robot {robot.id} dropping items at drop point")
                for item in robot.carrying_items:
                    print(f"  - Item #{item.id} successfully delivered")
                robot.carrying_items = []
                robot.current_weight = 0
                robot.path = []
                robot.target_items = []
    
    def _handle_stuck_carrying_robots(self, robots: List[Any], drop_point: Tuple[int, int], 
                                     unassigned_items: List[Any]) -> None:
        """Handle robots carrying items but without paths"""
        for robot in robots:
            if robot.carrying_items and not robot.path:
                print(f"Robot {robot.id} got stuck with items - attempting to find new path to drop point")
                robot.path = self.path_finder.find_path(
                    (robot.y, robot.x), 
                    (drop_point[1], drop_point[0]), 
                    robots,
                    robot.id,
                    robot.current_weight
                )
                
                if not robot.path:
                    attempt_key = (robot.id, 'drop_point')
                    self.failed_attempts[attempt_key] = self.failed_attempts.get(attempt_key, 0) + 1
                    
                    if self.failed_attempts[attempt_key] >= self.max_attempts:
                        print(f"CRITICAL: Robot {robot.id} permanently failed to find path to drop point. Freeing items.")
                        for item in robot.carrying_items:
                            item.picked = False
                            item.assigned = False
                            unassigned_items.append(item)
                        robot.carrying_items = []
                        robot.current_weight = 0
    
    def _ensure_carrying_robots_have_paths(self, carrying_robots: List[Any], drop_point: Tuple[int, int]) -> None:
        """Ensure robots carrying items have paths to the drop point"""
        for robot in carrying_robots:
            if not robot.path:
                print(f"Robot {robot.id} creating path to drop point")
                robot.path = self.path_finder.find_path(
                    (robot.y, robot.x), 
                    (drop_point[1], drop_point[0]), 
                    None,  # Not passing robots here to avoid deadlocks
                    robot.id,
                    robot.current_weight
                )
                
                if not robot.path:
                    print(f"WARNING: Robot {robot.id} failed to find path to drop point. Attempting again next cycle.")
    
    def _handle_stuck_moving_robots(self, moving_robots: List[Any], all_robots: List[Any], 
                                  unassigned_items: List[Any]) -> None:
        """Handle robots that are moving to items but have no path"""
        for robot in moving_robots:
            if robot.target_items and len(robot.path) == 0:
                print(f"Robot {robot.id} is stuck trying to get to item #{robot.target_items[0].id}")
                first_item = robot.target_items[0]
                robot.path = self.path_finder.find_path(
                    (robot.y, robot.x), 
                    (first_item.y, first_item.x), 
                    all_robots,
                    robot.id
                )
                
                if not robot.path:
                    attempt_key = (robot.id, first_item.id)
                    self.failed_attempts[attempt_key] = self.failed_attempts.get(attempt_key, 0) + 1
                    
                    if self.failed_attempts[attempt_key] >= self.max_attempts:
                        print(f"Robot {robot.id} permanently failed to reach item #{first_item.id}. Unassigning.")
                        for item in robot.target_items:
                            item.assigned = False
                            unassigned_items.append(item)
                        robot.target_items = []
    
    def _assign_items_to_idle_robots(self, idle_robots: List[Any], unassigned_items: List[Any], 
                                    all_robots: List[Any], drop_point: Tuple[int, int]) -> None:
        """Assign unassigned items to idle robots"""
        for robot in idle_robots:
            if not unassigned_items:
                break
                
            valid_items = []
            for item in unassigned_items[:]:
                if item.weight <= robot.capacity:
                    if (robot.id, item.id) in self.failed_attempts and self.failed_attempts[(robot.id, item.id)] >= self.max_attempts:
                        continue
                    valid_items.append(item)
            
            if valid_items:
                valid_items.sort(key=lambda x: abs(x.x - robot.x) + abs(x.y - robot.y))
                
                # Use clustering if enabled, otherwise just assign the closest item
                if self.clustering_enabled:
                    item_clusters = self._cluster_nearby_items(valid_items, robot)
                    best_cluster = self._select_best_cluster(item_clusters, robot)
                    
                    if best_cluster:
                        selected_items = []
                        current_weight = 0
                        
                        for item in best_cluster:
                            if current_weight + item.weight <= robot.capacity:
                                if not selected_items:
                                    test_path = self.path_finder.find_path(
                                        (robot.y, robot.x), 
                                        (item.y, item.x), 
                                        all_robots,
                                        robot.id
                                    )
                                    if not test_path:
                                        attempt_key = (robot.id, item.id)
                                        self.failed_attempts[attempt_key] = self.failed_attempts.get(attempt_key, 0) + 1
                                        print(f"Robot {robot.id} can't find path to item #{item.id} - attempt {self.failed_attempts[attempt_key]}")
                                        break
                                
                                selected_items.append(item)
                                current_weight += item.weight
                                unassigned_items.remove(item)
                                item.assigned = True
                        
                        if selected_items:
                            robot.target_items = selected_items
                            first_item = selected_items[0]
                            
                            robot.path = self.path_finder.find_path(
                                (robot.y, robot.x), 
                                (first_item.y, first_item.x), 
                                all_robots,
                                robot.id
                            )
                            
                            if robot.path:
                                print(f"Robot {robot.id} assigned to pick up {len(selected_items)} items with total weight {current_weight}kg, starting with item #{first_item.id}")
                            else:
                                print(f"Robot {robot.id} failed to find path to items during final assignment")
                                for item in selected_items:
                                    item.assigned = False
                                    unassigned_items.append(item)
                                robot.target_items = []
                else:
                    # Simpler assignment logic when clustering is disabled - just take the closest item
                    closest_item = valid_items[0]
                    test_path = self.path_finder.find_path(
                        (robot.y, robot.x), 
                        (closest_item.y, closest_item.x), 
                        all_robots,
                        robot.id
                    )
                    
                    if test_path:
                        unassigned_items.remove(closest_item)
                        closest_item.assigned = True
                        robot.target_items = [closest_item]
                        robot.path = test_path
                        print(f"Robot {robot.id} assigned to pick up single item #{closest_item.id} with weight {closest_item.weight}kg")
                    else:
                        attempt_key = (robot.id, closest_item.id)
                        self.failed_attempts[attempt_key] = self.failed_attempts.get(attempt_key, 0) + 1
                        print(f"Robot {robot.id} can't find path to item #{closest_item.id} - attempt {self.failed_attempts[attempt_key]}")

    
    def _cluster_nearby_items(self, items: List[Any], robot: Any) -> List[List[Any]]:
        """Group items that are close to each other for more efficient pickup"""
        clusters = []
        remaining_items = items.copy()
        
        while remaining_items:
            cluster_seed = remaining_items[0]  # Use first item as seed
            remaining_items.remove(cluster_seed)
            
            current_cluster = [cluster_seed]
            
            proximity_radius = 5  # Items within this Manhattan distance are considered nearby
            items_to_remove = []
            
            for item in remaining_items:
                if abs(item.x - cluster_seed.x) + abs(item.y - cluster_seed.y) <= proximity_radius:
                    current_cluster.append(item)
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                remaining_items.remove(item)
            
            clusters.append(current_cluster)
        
        return clusters
    
    def _select_best_cluster(self, clusters: List[List[Any]], robot: Any) -> List[Any]:
        """Select best cluster based on weight optimization and proximity"""
        if not clusters:
            return []
        
        best_score = -1
        best_cluster = []
        
        for cluster in clusters:
            total_weight = 0
            items_that_fit = []
            
            for item in cluster:
                if total_weight + item.weight <= robot.capacity:
                    total_weight += item.weight
                    items_that_fit.append(item)
            
            if not items_that_fit:
                continue
            
            first_item = cluster[0]
            distance_to_first = abs(first_item.x - robot.x) + abs(first_item.y - robot.y)
            
            capacity_utilization = total_weight / robot.capacity
            
            # Score combines capacity utilization (higher is better) and distance (lower is better)
            score = (capacity_utilization * 100) - (distance_to_first * 0.5)
            
            if score > best_score:
                best_score = score
                best_cluster = items_that_fit
        
        return best_cluster
    
    def _check_remaining_unassigned(self, items: List[Any], robots: List[Any]) -> None:
        """Check and report any remaining unassigned items and idle robots"""
        remaining_unassigned = [item for item in items if not item.picked and not item.assigned]
        remaining_idle = [robot for robot in robots if not robot.path and not robot.carrying_items]
        
        if remaining_unassigned and remaining_idle:
            print(f"WARNING: Still have {len(remaining_unassigned)} unassigned items and {len(remaining_idle)} idle robots!")
            for robot in remaining_idle:
                print(f"Idle robot {robot.id} with capacity {robot.capacity}kg")
            for item in remaining_unassigned[:3]:  # Only display first 3 for brevity
                print(f"Unassigned item #{item.id} at ({item.x},{item.y}) with weight {item.weight}kg")
                
                can_reach = False
                for robot in robots:
                    if item.weight <= robot.capacity:
                        test_path = self.path_finder.find_path(
                            (robot.y, robot.x), 
                            (item.y, item.x), 
                            robots,
                            robot.id
                        )
                        if test_path:
                            can_reach = True
                            print(f"  - Robot {robot.id} could reach this item. Why wasn't it assigned?")
                            break
                
                if not can_reach:
                    print(f"  - NO ROBOT CAN REACH THIS ITEM! It may be physically unreachable.")

    def assign_items_to_robots(self, robots: List[Any], items: List[Any], drop_point: Tuple[int, int]) -> bool:
        """
        Advanced item assignment with capacity optimization and clustering
        
        Args:
            robots: List of robots
            items: List of items
            drop_point: Dropoff point coordinates (x, y)
            
        Returns:
            bool: True if there are fewer unassigned items than total items
        """
        unassigned_items = [item for item in items if not item.picked and not item.assigned]
        print("\n--- Item Assignment Cycle ---")
        print(f"Unassigned items: {len(unassigned_items)}")
        
        # Handle robots at drop point
        self._handle_drop_point_deliveries(robots, drop_point)
        
        # Handle robots carrying items without paths
        self._handle_stuck_carrying_robots(robots, drop_point, unassigned_items)
        
        # Categorize robots by their status
        idle_robots = [robot for robot in robots if not robot.path and not robot.carrying_items]
        carrying_robots = [robot for robot in robots if robot.carrying_items]
        moving_robots = [robot for robot in robots if robot.path and not robot.carrying_items]
        
        print(f"Robot status: {len(idle_robots)} idle, {len(carrying_robots)} carrying, {len(moving_robots)} moving to items")
        
        # Ensure carrying robots have paths to drop point
        self._ensure_carrying_robots_have_paths(carrying_robots, drop_point)
        
        # Handle moving robots without paths
        self._handle_stuck_moving_robots(moving_robots, robots, unassigned_items)
        
        # Assign items to idle robots
        self._assign_items_to_idle_robots(idle_robots, unassigned_items, robots, drop_point)
        
        # Periodically reset failed attempts history to prevent deadlocks
        if random.random() < 0.1:  
            self.failed_attempts = {}
            print("Reset failed attempts history")
        
        # Check for unreachable items
        if unassigned_items and idle_robots and len(idle_robots) >= len(unassigned_items):
            self._handle_unreachable_items(unassigned_items, idle_robots, robots)
        
        # Check for any remaining unassigned items with idle robots
        self._check_remaining_unassigned(items, robots)
        
        return len(unassigned_items) < len(items)

    def _handle_unreachable_items(self, unassigned_items: List[Any], idle_robots: List[Any], all_robots: List[Any]) -> None:
        """
        Handle items that might be unreachable by any robot
        
        Args:
            unassigned_items: List of unassigned items
            idle_robots: List of idle robots
            all_robots: List of all robots
        """
        # Count failed assignments per item
        item_assignment_failures = {}
        
        for (robot_id, item_id), attempts in self.failed_attempts.items():
            if item_id not in item_assignment_failures:
                item_assignment_failures[item_id] = 0
            item_assignment_failures[item_id] += attempts
        
        # Find items with many failed assignment attempts
        potentially_unreachable = []
        for item in unassigned_items:
            if item.id in item_assignment_failures and item_assignment_failures[item.id] >= len(idle_robots) * 2:
                potentially_unreachable.append(item)
        
        if potentially_unreachable:
            print(f"WARNING: Detected {len(potentially_unreachable)} potentially unreachable items")
            
            for item in potentially_unreachable:
                print(f"Checking if item #{item.id} at ({item.x}, {item.y}) is truly unreachable...")
                
                is_reachable = False
                best_robot = None
                shortest_path_length = float('inf')
                
                # Try each robot to see if any can reach it
                for robot in idle_robots:
                    path = self.path_finder.find_path(
                        (robot.y, robot.x),
                        (item.y, item.x),
                        None,  # Don't avoid other robots for this check
                        robot.id
                    )
                    
                    if path:
                        is_reachable = True
                        if len(path) < shortest_path_length:
                            shortest_path_length = len(path)
                            best_robot = robot
                
                if not is_reachable:
                    print(f"CONFIRMED: Item #{item.id} is unreachable. Finding closest available robot...")
                    
                    # Find the closest robot to teleport
                    closest_robot = None
                    closest_distance = float('inf')
                    
                    for robot in idle_robots:
                        distance = abs(robot.x - item.x) + abs(robot.y - item.y)
                        if distance < closest_distance:
                            closest_distance = distance
                            closest_robot = robot
                    
                    if closest_robot:
                        print(f"TELEPORTING: Robot {closest_robot.id} to unreachable item #{item.id}")
                        
                        # Find positions near the item
                        positions_to_try = []
                        
                        # Try positions in increasing distance
                        for distance in range(1, 5):
                            for dx in range(-distance, distance + 1):
                                for dy in range(-distance, distance + 1):
                                    if abs(dx) + abs(dy) == distance:  # Manhattan distance
                                        positions_to_try.append((item.x + dx, item.y + dy))
                        
                        # Try each position until we find an empty one
                        teleport_x, teleport_y = item.x, item.y  # Default
                        for x, y in positions_to_try:
                            if self.grid.in_bounds(x, y) and self.grid.is_cell_empty(x, y):
                                teleport_x, teleport_y = x, y
                                break
                        
                        # Clear previous position and move robot
                        from core.models.grid import CellType
                        self.grid.set_cell(closest_robot.x, closest_robot.y, CellType.EMPTY)
                        closest_robot.x, closest_robot.y = teleport_x, teleport_y
                        self.grid.set_cell(teleport_x, teleport_y, CellType.ROBOT)
                        
                        # Assign item to robot
                        closest_robot.target_items = [item]
                        item.assigned = True
                        
                        # Reset path
                        closest_robot.path = self.path_finder.find_path(
                            (closest_robot.y, closest_robot.x),
                            (item.y, item.x),
                            all_robots,
                            closest_robot.id
                        )
                        
                        print(f"Robot {closest_robot.id} teleported to ({teleport_x}, {teleport_y}) and assigned to item #{item.id}")
                        
                        # Remove from idle robots
                        idle_robots.remove(closest_robot)
                elif best_robot:
                    print(f"Item #{item.id} is reachable! Assigning to robot {best_robot.id}")
                    
                    # Assign item to best robot
                    best_robot.target_items = [item]
                    item.assigned = True
                    
                    # Set path
                    best_robot.path = self.path_finder.find_path(
                        (best_robot.y, best_robot.x),
                        (item.y, item.x),
                        all_robots,
                        best_robot.id
                    )
                    
                    # Remove from idle robots and unassigned items
                    idle_robots.remove(best_robot)
                    unassigned_items.remove(item)
        
        # For any remaining items after attempting to handle unreachable ones,
        # forcibly complete them if they've been unreachable for too long
        if self._should_force_complete_items(unassigned_items):
            print("CRITICAL: Some items remain unreachable for too long")
            print("Force completing remaining items to avoid deadlock")
            
            for item in unassigned_items:
                print(f"Force completing item #{item.id}")
                item.picked = True
                item.assigned = False

    def _should_force_complete_items(self, unassigned_items: List[Any]) -> bool:
        """
        Determine if we should force-complete remaining unreachable items
        
        Args:
            unassigned_items: List of unassigned items
            
        Returns:
            bool: True if items should be force-completed
        """
        # Track how many cycles an item remains unassigned
        if not hasattr(self, 'item_unassigned_cycles'):
            self.item_unassigned_cycles = {}
        
        # Update cycle count for each unassigned item
        for item in unassigned_items:
            if item.id not in self.item_unassigned_cycles:
                self.item_unassigned_cycles[item.id] = 0
            self.item_unassigned_cycles[item.id] += 1
        
        # Clean up tracked items that are no longer unassigned
        for item_id in list(self.item_unassigned_cycles.keys()):
            if item_id not in [item.id for item in unassigned_items]:
                del self.item_unassigned_cycles[item_id]
        
        # Check if any item has been unassigned for too long
        for item in unassigned_items:
            if self.item_unassigned_cycles.get(item.id, 0) > 30:
                return True
        
        return False