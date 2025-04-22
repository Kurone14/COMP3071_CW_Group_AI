from typing import List, Dict, Tuple, Set, Any


class CollisionResolver:
    """
    Resolves potential collisions between robots trying to move to the same position.
    Uses a priority system to decide which robots should move and which should wait.
    """
    
    def resolve_collisions(self, robots: List[Any], 
                          next_positions: Dict[int, Tuple[int, int]], 
                          robot_stuck_time: Dict[int, int]) -> Set[int]:
        """
        Resolve collisions between robots
        
        Args:
            robots: List of all robots
            next_positions: Dictionary mapping robot_id to next position (x, y)
            robot_stuck_time: Dictionary tracking how long each robot has been stuck
            
        Returns:
            Set of robot IDs that should skip their turn due to collision
        """
        collisions: Dict[int, List[int]] = {}  # robot_id -> list of conflicting robot_ids
        
        # Identify all collisions
        for robot_id, pos in next_positions.items():
            collisions[robot_id] = []
            for other_id, other_pos in next_positions.items():
                if robot_id != other_id and pos == other_pos:
                    collisions[robot_id].append(other_id)
        
        robots_to_skip: Set[int] = set()
        
        # Resolve each collision based on priorities
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
    
    def _apply_priorities(self, 
                         robot1: Any, robot2: Any, 
                         robot1_id: int, robot2_id: int, 
                         robot_stuck_time: Dict[int, int], 
                         robots_to_skip: Set[int]) -> None:
        """
        Apply priorities to decide which robot should move
        
        Priority rules (in order):
        1. Robots carrying items have priority over empty robots
        2. Robots stuck for a long time have priority
        3. Robots with longer paths remaining (further from goal) have priority
        
        Args:
            robot1, robot2: The two robots in conflict
            robot1_id, robot2_id: IDs of the robots
            robot_stuck_time: Dictionary tracking how long each robot has been stuck
            robots_to_skip: Set to add robots that should skip their turn
        """
        robot1_carrying = bool(robot1.carrying_items)
        robot2_carrying = bool(robot2.carrying_items)
        
        robot1_time_stuck = robot_stuck_time.get(robot1_id, 0)
        robot2_time_stuck = robot_stuck_time.get(robot2_id, 0)
        
        # Rule 1: Robots carrying items have priority
        if robot1_carrying and not robot2_carrying:
            robots_to_skip.add(robot2_id)
            return
        elif robot2_carrying and not robot1_carrying:
            robots_to_skip.add(robot1_id)
            return
        
        # Rule 2: Robots stuck for a long time have priority
        if abs(robot1_time_stuck - robot2_time_stuck) > 5:
            if robot1_time_stuck > robot2_time_stuck:
                robots_to_skip.add(robot2_id)
            else:
                robots_to_skip.add(robot1_id)
            return
        
        # Rule 3: Robots with longer paths have priority (they're further from goal)
        if len(robot1.path) > len(robot2.path):
            robots_to_skip.add(robot2_id)
        else:
            robots_to_skip.add(robot1_id)