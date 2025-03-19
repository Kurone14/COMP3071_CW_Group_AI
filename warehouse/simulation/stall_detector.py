class StallDetector:
    """Detects and resolves stalled simulation states"""
    def __init__(self, grid, width, height, drop_point, path_finder):
        self.grid = grid
        self.width = width
        self.height = height
        self.drop_point = drop_point
        self.path_finder = path_finder
        
        self.loop_count = 0
        self.last_progress_at = 0
        self.previous_picked_count = 0
        self.previous_delivered_count = 0
    
    def reset(self):
        """Reset all tracking counters"""
        self.loop_count = 0
        self.last_progress_at = 0
        self.previous_picked_count = 0
        self.previous_delivered_count = 0
        print("Stall detector reset")
    
    def update_grid(self, grid):
        """Update the grid reference"""
        self.grid = grid
    
    def check_progress(self, robots, items):
        """Check if the simulation is making progress"""
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
    
    def level1_recovery(self, robots, items, stall_time):
        """
        Level 1: Mild stall (at 15 cycles) - standard recovery
        Free stuck assigned items and reset robots with no path to target
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
    
    def level2_recovery(self, robots, items, stall_time):
        """
        Level 2: Medium stall (at 20 cycles) - stronger interventions
        Teleport stuck robots to drop point and assign unassigned items
        """
        if stall_time <= 20:
            return False
            
        print(f"MEDIUM STALL: Taking stronger measures after {stall_time} cycles")
        made_changes = False
        
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            target_robot = max(robots_with_items, 
                              key=lambda r: (not bool(r.path), len(r.carrying_items)))
            
            if not target_robot.path or len(target_robot.path) > 15:
                print(f"TELEPORT: Moving robot {target_robot.id} with {len(target_robot.carrying_items)} items to drop point")
                self.grid[target_robot.y][target_robot.x] = 0
                
                target_robot.x, target_robot.y = self.drop_point
                self.grid[target_robot.y][target_robot.x] = 3
                target_robot.path = [] 
                
                self.last_progress_at = self.loop_count
                made_changes = True
        
        unassigned_items = [item for item in items if not item.picked and not item.assigned]
        if unassigned_items:
            print(f"AGGRESSIVE ITEM ASSIGNMENT: {len(unassigned_items)} items remain unassigned")
            
            target_robot = None
            for robot in robots:
                if not robot.path and not robot.carrying_items:
                    target_robot = robot
                    break
            
            if not target_robot:
                robots_by_path = [(r, len(r.path)) for r in robots if not r.carrying_items]
                if robots_by_path:
                    robots_by_path.sort(key=lambda x: x[1])
                    target_robot = robots_by_path[0][0]
            
            if target_robot:
                for item in sorted(unassigned_items, 
                                   key=lambda x: abs(x.x - target_robot.x) + abs(x.y - target_robot.y)):
                    print(f"FORCING: Sending robot {target_robot.id} to item #{item.id}")
                    item.assigned = True
                    target_robot.target_items = [item]
                    target_robot.path = self.path_finder.a_star_pathfinding(
                        (target_robot.y, target_robot.x), 
                        (item.y, item.x), 
                        robots,
                        target_robot.id
                    )
                    
                    if not target_robot.path:
                        print(f"TELEPORT: Moving robot {target_robot.id} to item #{item.id}")
                        self.grid[target_robot.y][target_robot.x] = 0
                        
                        teleport_x, teleport_y = item.x, item.y
                        directions = [(0,0), (0,1), (1,0), (0,-1), (-1,0)]
                        
                        for dx, dy in directions:
                            test_x, test_y = item.x + dx, item.y + dy
                            if 0 <= test_x < self.width and 0 <= test_y < self.height and self.grid[test_y][test_x] == 0:
                                teleport_x, teleport_y = test_x, test_y
                                break
                        
                        target_robot.x, target_robot.y = teleport_x, teleport_y
                        self.grid[target_robot.y][target_robot.x] = 3
                        
                        target_robot.path = self.path_finder.a_star_pathfinding(
                            (target_robot.y, target_robot.x), 
                            (item.y, item.x), 
                            robots,
                            target_robot.id
                        )
                    
                    self.last_progress_at = self.loop_count
                    made_changes = True
                    break
                    
        return made_changes
    
    def level3_recovery(self, robots, items, stall_time, remaining_items):
        """
        Level 3: Severe stall (at 35 cycles) - extreme measures
        Teleport all robots with items to drop point, teleport robots to unreachable items
        """
        if stall_time <= 35:
            return False
            
        print(f"CRITICAL: Severe stall for {stall_time} cycles - taking extreme measures")
        made_changes = False
        
        robots_with_items = [r for r in robots if r.carrying_items]
        if robots_with_items:
            print(f"EMERGENCY: Teleporting ALL {len(robots_with_items)} robots with items to drop point")
            
            drop_area = []
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    if dx == 0 and dy == 0:
                        continue 
                    drop_x, drop_y = self.drop_point[0] + dx, self.drop_point[1] + dy
                    if 0 <= drop_x < self.width and 0 <= drop_y < self.height:
                        drop_area.append((drop_x, drop_y))
            
            if not drop_area:
                drop_area = [self.drop_point]
            
            for i, robot in enumerate(robots_with_items):
                self.grid[robot.y][robot.x] = 0
                
                if i < len(drop_area):
                    robot.x, robot.y = drop_area[i]
                else:
                    robot.x, robot.y = self.drop_point
                
                self.grid[robot.y][robot.x] = 3
                robot.path = []
            
            self.last_progress_at = self.loop_count
            made_changes = True
        
        if remaining_items:
            print(f"CRITICAL: {len(remaining_items)} items still unreachable after {stall_time} cycles")
            
            available_robot = None
            for robot in robots:
                if not robot.carrying_items:
                    available_robot = robot
                    break
            
            if available_robot and remaining_items:
                item = remaining_items[0]
                print(f"EMERGENCY: Teleporting robot {available_robot.id} to unreachable item #{item.id}")
                
                self.grid[available_robot.y][available_robot.x] = 0
                
                available_robot.x, available_robot.y = item.x, item.y
                self.grid[available_robot.y][available_robot.x] = 3
                
                available_robot.target_items = [item]
                item.assigned = True
                
                self.last_progress_at = self.loop_count
                made_changes = True
                
        return made_changes
    
    def level4_recovery(self, robots, items, stall_time, remaining_items):
        """
        Level 4: Force simulation completion (at 50 cycles)
        Instantly complete all remaining items
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
        
    def check_timeout(self):
        """Check if the simulation has been running too long"""
        return self.loop_count > 200  