import random

class ItemAssigner:
    def __init__(self, grid, path_finder):
        self.grid = grid
        self.path_finder = path_finder
        self.failed_attempts = {}  
        self.max_attempts = 3
    
    def assign_items_to_robots(self, robots, items, drop_point):
        """Advanced item assignment with better capacity optimization"""
        unassigned_items = [item for item in items if not item.picked and not item.assigned]
        print("\n--- Item Assignment Cycle ---")
        print(f"Unassigned items: {len(unassigned_items)}")
        
        for robot in robots:
            if robot.carrying_items and (robot.x, robot.y) == drop_point:
                print(f"Robot {robot.id} dropping items at drop point")
                for item in robot.carrying_items:
                    print(f"  - Item #{item.id} successfully delivered")
                robot.carrying_items = []
                robot.current_weight = 0
                robot.path = []
                robot.target_items = []
        
        for robot in robots:
            if robot.carrying_items and not robot.path:
                print(f"Robot {robot.id} got stuck with items - attempting to find new path to drop point")
                robot.path = self.path_finder.a_star_pathfinding(
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
        
        idle_robots = [robot for robot in robots if not robot.path and not robot.carrying_items]
        carrying_robots = [robot for robot in robots if robot.carrying_items]
        moving_robots = [robot for robot in robots if robot.path and not robot.carrying_items]
        
        print(f"Robot status: {len(idle_robots)} idle, {len(carrying_robots)} carrying, {len(moving_robots)} moving to items")
        
        for robot in carrying_robots:
            if not robot.path:
                print(f"Robot {robot.id} creating path to drop point")
                robot.path = self.path_finder.a_star_pathfinding(
                    (robot.y, robot.x), 
                    (drop_point[1], drop_point[0]), 
                    robots,
                    robot.id,
                    robot.current_weight
                )
                
                if not robot.path:
                    print(f"WARNING: Robot {robot.id} failed to find path to drop point. Attempting again next cycle.")
        
        for robot in moving_robots:
            if robot.target_items and len(robot.path) == 0:
                print(f"Robot {robot.id} is stuck trying to get to item #{robot.target_items[0].id}")
                first_item = robot.target_items[0]
                robot.path = self.path_finder.a_star_pathfinding(
                    (robot.y, robot.x), 
                    (first_item.y, first_item.x), 
                    robots,
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
                
                item_clusters = self._cluster_nearby_items(valid_items, robot)
                
                best_cluster = self._select_best_cluster(item_clusters, robot)
                
                if best_cluster:
                    selected_items = []
                    current_weight = 0
                    
                    for item in best_cluster:
                        if current_weight + item.weight <= robot.capacity:
                            if not selected_items:
                                test_path = self.path_finder.a_star_pathfinding(
                                    (robot.y, robot.x), 
                                    (item.y, item.x), 
                                    robots,
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
                        
                        robot.path = self.path_finder.a_star_pathfinding(
                            (robot.y, robot.x), 
                            (first_item.y, first_item.x), 
                            robots,
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
        
        if random.random() < 0.1:  
            self.failed_attempts = {}
            print("Reset failed attempts history")
        
        remaining_unassigned = [item for item in items if not item.picked and not item.assigned]
        remaining_idle = [robot for robot in robots if not robot.path and not robot.carrying_items]
        
        if remaining_unassigned and remaining_idle:
            print(f"WARNING: Still have {len(remaining_unassigned)} unassigned items and {len(remaining_idle)} idle robots!")
            for robot in remaining_idle:
                print(f"Idle robot {robot.id} with capacity {robot.capacity}kg")
            for item in remaining_unassigned[:3]: 
                print(f"Unassigned item #{item.id} at ({item.x},{item.y}) with weight {item.weight}kg")
                
                can_reach = False
                for robot in robots:
                    if item.weight <= robot.capacity:
                        test_path = self.path_finder.a_star_pathfinding(
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
        
        return len(unassigned_items) < len(items)
    
    def _cluster_nearby_items(self, items, robot):
        """Group items that are close to each other for more efficient pickup"""
        clusters = []
        remaining_items = items.copy()
        
        while remaining_items:
            cluster_seed = remaining_items[0]  
            remaining_items.remove(cluster_seed)
            
            current_cluster = [cluster_seed]
            
            proximity_radius = 5
            items_to_remove = []
            
            for item in remaining_items:
                if abs(item.x - cluster_seed.x) + abs(item.y - cluster_seed.y) <= proximity_radius:
                    current_cluster.append(item)
                    items_to_remove.append(item)
            
            for item in items_to_remove:
                remaining_items.remove(item)
            
            clusters.append(current_cluster)
        
        return clusters
    
    def _select_best_cluster(self, clusters, robot):
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
            
            score = (capacity_utilization * 100) - (distance_to_first * 0.5)
            
            if score > best_score:
                best_score = score
                best_cluster = items_that_fit
        
        return best_cluster