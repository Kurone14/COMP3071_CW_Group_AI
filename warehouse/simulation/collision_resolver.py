class CollisionResolver:
    
    def resolve_collisions(self, robots, next_positions, robot_stuck_time):
        collisions = {}  
        
        for robot_id, pos in next_positions.items():
            collisions[robot_id] = []
            for other_id, other_pos in next_positions.items():
                if robot_id != other_id and pos == other_pos:
                    collisions[robot_id].append(other_id)
        
        robots_to_skip = set()
        
        for robot_id, conflicting_ids in collisions.items():
            if conflicting_ids and robot_id not in robots_to_skip:
                robot = next(r for r in robots if r.id == robot_id)
                
                for conflicting_id in conflicting_ids:
                    conflicting_robot = next(r for r in robots if r.id == conflicting_id)
                    
                    self._apply_priorities(
                        robot, conflicting_robot, 
                        robot_id, conflicting_id, 
                        robot_stuck_time, robots_to_skip
                    )
        
        return robots_to_skip
    
    def _apply_priorities(self, robot1, robot2, robot1_id, robot2_id, robot_stuck_time, robots_to_skip):
        robot1_carrying = bool(robot1.carrying_items)
        robot2_carrying = bool(robot2.carrying_items)
        
        robot1_time_stuck = robot_stuck_time.get(robot1_id, 0)
        robot2_time_stuck = robot_stuck_time.get(robot2_id, 0)
        
        if robot1_carrying and not robot2_carrying:
            robots_to_skip.add(robot2_id)
            return
        elif robot2_carrying and not robot1_carrying:
            robots_to_skip.add(robot1_id)
            return
        
        if abs(robot1_time_stuck - robot2_time_stuck) > 5:
            if robot1_time_stuck > robot2_time_stuck:
                robots_to_skip.add(robot2_id)
            else:
                robots_to_skip.add(robot1_id)
            return
        
        if len(robot1.path) > len(robot2.path):
            robots_to_skip.add(robot2_id)
        else:
            robots_to_skip.add(robot1_id)