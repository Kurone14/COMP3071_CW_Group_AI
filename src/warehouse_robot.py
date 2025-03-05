import pymunk
import pygame
import numpy as np
import math
import time
import random
from collections import deque

class WarehouseRobot:
    def __init__(self, space, position, id):
        self.id = id
        
        # Create the robot body
        self.body = pymunk.Body(1, 100)
        self.body.position = position
        
        # Create the robot shape
        self.shape = pymunk.Circle(self.body, 10)
        self.shape.collision_type = 1
        self.shape.friction = 0.7
        
        # Add to space
        space.add(self.body, self.shape)
        
        # Perception capabilities
        self.sensor_range = 150  # Increased range
        self.sensors = []
        self.detected_obstacles = []
        self.known_layout = {}
        
        # Planning capabilities
        self.path = []
        self.target = None
        self.target_id = None  # To track which pickup/dropoff point is targeted
        self.max_speed = 80  # Decreased for better control
        self.state = "idle"  # idle, moving, pickup, dropoff
        
        # Task-related attributes
        self.carrying_item = False
        self.current_task = None
        self.task_start_time = None  # To track task duration
        
        # Status tracking
        self.last_replan_time = time.time()
        self.position_history = []
        self.last_progress_time = time.time()
        
        # Colors based on state
        self.colors = {
            "idle": (255, 0, 0),         # Red
            "moving": (255, 165, 0),     # Orange
            "pickup": (0, 255, 0),       # Green
            "dropoff": (0, 0, 255),      # Blue
            "carrying": (128, 0, 128)    # Purple when carrying items
        }

        self.environment = None
    
    def update_perception(self, environment):
        # Simulate sensor readings
        self.detected_obstacles = []
        
        # Check for obstacles within sensor range
        for obstacle in environment.obstacles:
            dist = self.distance_to_obstacle(obstacle)
            if dist < self.sensor_range:
                self.detected_obstacles.append(obstacle)
                
                # Update known layout
                self.known_layout[obstacle['id']] = {
                    'position': obstacle['position'],
                    'size': obstacle['size'],
                    'last_seen': 0  # time counter
                }
        
        # Check for other robots
        for robot in environment.robots:
            if robot.id != self.id:
                dist = self.distance_to_point(robot.body.position)
                if dist < self.sensor_range:
                    # Add other robots as dynamic obstacles
                    self.detected_obstacles.append({
                        'position': (robot.body.position.x - 10, robot.body.position.y - 10),
                        'size': (20, 20),
                        'id': f'robot_{robot.id}',
                        'temporary': True
                    })
                    
        # Check for shelves
        for shelf in environment.shelves:
            dist = self.distance_to_obstacle(shelf)
            if dist < self.sensor_range:
                self.detected_obstacles.append(shelf)
    
    def distance_to_obstacle(self, obstacle):
        # Calculate distance to the closest point of the obstacle
        x, y = self.body.position
        ox, oy = obstacle['position']
        ow, oh = obstacle['size']
        
        closest_x = max(ox, min(x, ox + ow))
        closest_y = max(oy, min(y, oy + oh))
        
        return math.sqrt((x - closest_x)**2 + (y - closest_y)**2)

    def distance_to_point(self, point):
        # Calculate Euclidean distance to a point
        return math.sqrt((self.body.position.x - point.x)**2 + (self.body.position.y - point.y)**2)

    def plan_path(self, target):
        # Simple A* path planning implementation
        self.target = target
        self.path = self.a_star_search(self.body.position, target)
        self.state = "moving"
        
    def a_star_search(self, start, goal):
        """Improved A* search that ensures robots can reach their targets"""
        # Convert positions to grid coordinates
        grid_size = 20
        start_grid = (int(start.x / grid_size), int(start.y / grid_size))
        goal_grid = (int(goal[0] / grid_size), int(goal[1] / grid_size))
        
        # If start or goal are outside boundaries, adjust them
        width, height = self.environment.width, self.environment.height
        if start_grid[0] < 0 or start_grid[0] >= width // grid_size or start_grid[1] < 0 or start_grid[1] >= height // grid_size:
            print(f"Robot {self.id}: Start position out of bounds, adjusting")
            start_grid = (
                max(0, min(width // grid_size - 1, start_grid[0])),
                max(0, min(height // grid_size - 1, start_grid[1]))
            )
        
        if goal_grid[0] < 0 or goal_grid[0] >= width // grid_size or goal_grid[1] < 0 or goal_grid[1] >= height // grid_size:
            print(f"Robot {self.id}: Goal position out of bounds, adjusting")
            goal_grid = (
                max(0, min(width // grid_size - 1, goal_grid[0])),
                max(0, min(height // grid_size - 1, goal_grid[1]))
            )
        
        # A* algorithm
        import heapq
        open_set = []
        heapq.heappush(open_set, (self.heuristic(start_grid, goal_grid), 0, start_grid))  # f_score, tiebreaker, position
        came_from = {}
        g_score = {start_grid: 0}
        f_score = {start_grid: self.heuristic(start_grid, goal_grid)}
        closed_set = set()  # To track visited nodes
        tiebreaker = 1  # To ensure heap uniqueness when f_scores are equal
        
        iterations = 0
        max_iterations = 1000  # Prevent infinite loops
        
        while open_set and iterations < max_iterations:
            iterations += 1
            _, _, current = heapq.heappop(open_set)
            
            if current in closed_set:
                continue
                
            closed_set.add(current)
            
            if current == goal_grid:
                # Reconstruct path
                path = []
                while current in came_from:
                    path.append((current[0] * grid_size + grid_size // 2, current[1] * grid_size + grid_size // 2))
                    current = came_from[current]
                path.reverse()
                
                # Add intermediate waypoints for smoother paths
                smoothed_path = self.smooth_path(path)
                
                # Add goal exactly as target position
                if smoothed_path:
                    smoothed_path.append(goal)
                else:
                    smoothed_path.append(goal)
                    
                return smoothed_path
            
            # Check neighbors - 8 directions
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]:
                neighbor = (current[0] + dx, current[1] + dy)
                
                # Skip if outside grid
                if (neighbor[0] < 0 or neighbor[0] >= width // grid_size or 
                    neighbor[1] < 0 or neighbor[1] >= height // grid_size):
                    continue
                
                # Skip if we've already processed this neighbor
                if neighbor in closed_set:
                    continue
                    
                # Check if neighbor is valid (not in obstacle)
                if self.is_valid_position(neighbor, grid_size):
                    # Movement cost is higher for diagonal moves
                    move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                    tentative_g = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal_grid)
                        heapq.heappush(open_set, (f_score[neighbor], tiebreaker, neighbor))
                        tiebreaker += 1
        
        # If no path found after max iterations or empty open set
        if iterations >= max_iterations:
            print(f"Robot {self.id}: Path search exceeded max iterations, using direct path")
        else:
            print(f"Robot {self.id}: No path found, using direct path with waypoints")
        
        # Plan a simple path with intermediate waypoints
        direct_path = self.plan_direct_path(start, goal)
        return direct_path

    def smooth_path(self, path):
        """Smooth path by adding intermediate waypoints and removing unnecessary ones"""
        if len(path) < 2:
            return path
            
        smoothed = [path[0]]
        
        for i in range(1, len(path)):
            # Add intermediate points for long segments
            prev = path[i-1]
            current = path[i]
            distance = math.sqrt((current[0] - prev[0])**2 + (current[1] - prev[1])**2)
            
            if distance > 100:  # If segment is too long
                # Add intermediate points
                steps = int(distance / 50)
                for step in range(1, steps):
                    t = step / steps
                    x = prev[0] + t * (current[0] - prev[0])
                    y = prev[1] + t * (current[1] - prev[1])
                    smoothed.append((x, y))
            
            smoothed.append(current)
        
        return smoothed

    def plan_direct_path(self, start, goal):
        """Plan a direct path with intermediate waypoints to handle obstacles"""
        # Create a path with intermediate waypoints to navigate around potential obstacles
        start_x, start_y = start.x, start.y
        goal_x, goal_y = goal
        
        # Get environment dimensions
        width, height = self.environment.width, self.environment.height
        
        # Create intermediate waypoints to avoid obstacles and stay in bounds
        path = []
        
        # If start and goal are far apart, add intermediate waypoints
        distance = math.sqrt((goal_x - start_x)**2 + (goal_y - start_y)**2)
        
        if distance > 100:
            # Add waypoint at 1/3 distance
            wx1 = start_x + (goal_x - start_x) / 3
            wy1 = start_y + (goal_y - start_y) / 3
            # Ensure waypoint is in bounds
            wx1 = max(20, min(width - 20, wx1))
            wy1 = max(20, min(height - 20, wy1))
            path.append((wx1, wy1))
            
            # Add waypoint at 2/3 distance
            wx2 = start_x + 2 * (goal_x - start_x) / 3
            wy2 = start_y + 2 * (goal_y - start_y) / 3
            # Ensure waypoint is in bounds
            wx2 = max(20, min(width - 20, wx2))
            wy2 = max(20, min(height - 20, wy2))
            path.append((wx2, wy2))
        
        # Add the goal
        path.append(goal)
        
        return path

    def is_valid_position(self, position, grid_size):
        # Check if position is valid (not in obstacle)
        x, y = position[0] * grid_size, position[1] * grid_size
        
        # Check boundaries with a margin
        margin = 10
        if x < margin or y < margin or x >= self.environment.width - margin or y >= self.environment.height - margin:
            return False
        
        # Check obstacles with padding
        padding = grid_size // 2
        for obstacle in self.detected_obstacles:
            ox, oy = obstacle['position']
            ow, oh = obstacle['size']
            
            if (x > ox - padding and x < ox + ow + padding and 
                y > oy - padding and y < oy + oh + padding):
                return False
        
        return True

    def heuristic(self, a, b):
        # Better heuristic - Euclidean distance
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

    def execute_movement(self):
        # Improved movement with better obstacle avoidance and path following
        if self.path and self.state == "moving":
            # Get next waypoint
            target = self.path[0]
            
            # Calculate direction vector
            dx = target[0] - self.body.position.x
            dy = target[1] - self.body.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Check for obstacles in the direct path
            collision_imminent = self.check_path_collision(target)
            
            if distance < 15:  # Waypoint reached
                self.path.pop(0)
                if not self.path:
                    # Path completed - check if we've reached the actual target
                    target_distance = math.sqrt(
                        (self.target[0] - self.body.position.x)**2 + 
                        (self.target[1] - self.body.position.y)**2
                    )
                    
                    if target_distance < 20:  # Close enough to target
                        self.check_task_completion()
                    else:
                        # We didn't reach the target, re-plan path
                        print(f"Robot {self.id}: Replanning path to target")
                        self.plan_path(self.target)
            else:
                # Apply appropriate force
                if collision_imminent:
                    # Obstacle avoidance - slow down and consider alternative paths
                    evasion_force = self.get_obstacle_avoidance_force()
                    force_x = dx / distance * self.max_speed * 0.5 + evasion_force[0]
                    force_y = dy / distance * self.max_speed * 0.5 + evasion_force[1]
                    self.body.apply_force_at_local_point((force_x, force_y), (0, 0))
                    
                    # If we're very close to an obstacle, consider replanning
                    if self.is_stuck_near_obstacle(5):
                        if time.time() - self.last_replan_time > 3.0:  # Don't replan too often
                            print(f"Robot {self.id}: Replanning due to obstacle")
                            self.plan_path(self.target)
                            self.last_replan_time = time.time()
                else:
                    # Normal movement - normalize direction vector
                    if distance > 0:
                        force_x = dx / distance * self.max_speed
                        force_y = dy / distance * self.max_speed
                        self.body.apply_force_at_local_point((force_x, force_y), (0, 0))
            
            # Check if we're stuck
            self.check_if_stuck()
        
        # Apply damping to simulate friction
        self.body.velocity = self.body.velocity * 0.9
        
        # Enforce speed limits
        current_speed = math.sqrt(self.body.velocity.x**2 + self.body.velocity.y**2)
        if current_speed > self.max_speed:
            scale_factor = self.max_speed / current_speed
            self.body.velocity = pymunk.Vec2d(
                self.body.velocity.x * scale_factor,
                self.body.velocity.y * scale_factor
            )
        
        # Enforce boundaries
        self.enforce_boundaries()

    def check_path_collision(self, target):
        # Check if there's an obstacle in direct path to target
        for obstacle in self.detected_obstacles:
            ox, oy = obstacle['position']
            ow, oh = obstacle['size']
            
            # Simple line-rectangle intersection check
            start_x, start_y = self.body.position.x, self.body.position.y
            end_x, end_y = target[0], target[1]
            
            # Check if line intersects with obstacle
            if self.line_intersects_rectangle(
                start_x, start_y, end_x, end_y,
                ox, oy, ox + ow, oy + oh
            ):
                return True
        
        return False

    def line_intersects_rectangle(self, x1, y1, x2, y2, rx1, ry1, rx2, ry2):
        # Check if line from (x1,y1) to (x2,y2) intersects with rectangle defined by (rx1,ry1) to (rx2,ry2)
        
        # Check if either endpoint is inside rectangle
        if (rx1 <= x1 <= rx2 and ry1 <= y1 <= ry2) or (rx1 <= x2 <= rx2 and ry1 <= y2 <= ry2):
            return True
        
        # Check each edge of the rectangle for intersection with the line
        if self.line_segments_intersect(x1, y1, x2, y2, rx1, ry1, rx2, ry1):  # Top edge
            return True
        if self.line_segments_intersect(x1, y1, x2, y2, rx1, ry1, rx1, ry2):  # Left edge
            return True
        if self.line_segments_intersect(x1, y1, x2, y2, rx2, ry1, rx2, ry2):  # Right edge
            return True
        if self.line_segments_intersect(x1, y1, x2, y2, rx1, ry2, rx2, ry2):  # Bottom edge
            return True
        
        return False

    def line_segments_intersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        # Check if line segments (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) intersect
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        
        a = (x1, y1)
        b = (x2, y2)
        c = (x3, y3)
        d = (x4, y4)
        
        return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)

    def get_obstacle_avoidance_force(self):
        # Calculate avoidance force based on nearby obstacles
        fx, fy = 0, 0
        robot_x, robot_y = self.body.position.x, self.body.position.y
        
        for obstacle in self.detected_obstacles:
            ox, oy = obstacle['position']
            ow, oh = obstacle['size']
            
            # Calculate center of obstacle
            center_x = ox + ow/2
            center_y = oy + oh/2
            
            # Vector from obstacle to robot
            vec_x = robot_x - center_x
            vec_y = robot_y - center_y
            
            # Distance squared (avoid sqrt for performance)
            dist_squared = vec_x*vec_x + vec_y*vec_y
            
            if dist_squared > 0:
                # Force is inversely proportional to distance squared
                # but has a maximum to prevent extreme forces
                force_magnitude = min(5000 / dist_squared, 300)
                
                # Normalize vector
                dist = math.sqrt(dist_squared)
                fx += (vec_x / dist) * force_magnitude
                fy += (vec_y / dist) * force_magnitude
        
        return (fx, fy)

    def is_stuck_near_obstacle(self, threshold=10):
        # Check if robot is very close to any obstacle
        robot_x, robot_y = self.body.position.x, self.body.position.y
        
        for obstacle in self.detected_obstacles:
            ox, oy = obstacle['position']
            ow, oh = obstacle['size']
            
            # Calculate distance to nearest point on obstacle
            closest_x = max(ox, min(robot_x, ox + ow))
            closest_y = max(oy, min(robot_y, oy + oh))
            
            dist = math.sqrt((robot_x - closest_x)**2 + (robot_y - closest_y)**2)
            
            if dist < threshold:
                return True
        
        return False

    def check_if_stuck(self, force_check=False):
        """Improved stuck detection with option to force check"""
        # Check if the robot hasn't moved significantly in a while
        current_time = time.time()
        current_pos = (self.body.position.x, self.body.position.y)
        
        # Initialize attributes if they don't exist yet
        if not hasattr(self, 'position_history'):
            self.position_history = []
        if not hasattr(self, 'last_progress_time'):
            self.last_progress_time = current_time
        if not hasattr(self, 'stuck_time'):
            self.stuck_time = None
        if not hasattr(self, 'last_replan_time'):
            self.last_replan_time = current_time
        
        # Add current position to history
        self.position_history.append((current_time, current_pos))
        
        # Remove old positions
        while self.position_history and current_time - self.position_history[0][0] > 5.0:
            self.position_history.pop(0)
        
        # If we have enough history or force check is enabled, check if we're stuck
        if len(self.position_history) >= 10 or force_check:
            # Calculate maximum distance moved
            max_dist = 0
            for _, pos in self.position_history:
                dist = math.sqrt(
                    (current_pos[0] - pos[0])**2 + 
                    (current_pos[1] - pos[1])**2
                )
                max_dist = max(max_dist, dist)
            
            # If we haven't moved much, we might be stuck
            if max_dist < 20:
                # If we weren't previously stuck, record when we got stuck
                if self.stuck_time is None:
                    self.stuck_time = current_time
                
                # Check if we've been stuck for too long (3 seconds)
                if force_check or current_time - self.stuck_time > 3.0:
                    if current_time - self.last_replan_time > 2.0:
                        print(f"Robot {self.id}: Stuck detected, replanning path")
                        
                        # Try to escape by temporarily moving away from target
                        escape_angle = random.uniform(0, 2 * math.pi)
                        escape_force = 300
                        fx = math.cos(escape_angle) * escape_force
                        fy = math.sin(escape_angle) * escape_force
                        self.body.apply_force_at_local_point((fx, fy), (0, 0))
                        
                        # Replan path or reset if we've been stuck for too long
                        if self.target and current_time - self.stuck_time < 10.0:
                            self.plan_path(self.target)
                        else:
                            # If stuck for too long, give up on current task
                            print(f"Robot {self.id}: Stuck for too long, giving up on task")
                            self.state = "idle"
                            self.target = None
                            self.stuck_time = None
                            return True
                            
                        self.last_replan_time = current_time
                    return True
            else:
                # Reset stuck time if we're moving
                self.stuck_time = None
        
        return False

    def enforce_boundaries(self):
        """Ensure robots stay within valid environment boundaries with strong correction"""
        # More aggressive boundary enforcement to prevent escaping
        margin = 30
        strong_force = self.max_speed * 3.0  # Stronger force for boundary correction
        
        x, y = self.body.position
        width, height = self.environment.width, self.environment.height
        
        # Reset position if outside boundaries by a significant amount
        if x < -margin or x > width + margin or y < -margin or y > height + margin:
            print(f"Robot {self.id} reset - out of bounds at ({x:.1f}, {y:.1f})")
            # Place robot back in bounds at a reasonable location
            new_x = max(margin * 2, min(width - margin * 2, x))
            new_y = max(margin * 2, min(height - margin * 2, y))
            self.body.position = (new_x, new_y)
            self.body.velocity = (0, 0)  # Stop movement
            
            # If the robot was trying to reach a target, replan path
            if self.target and self.state == "moving":
                self.plan_path(self.target)
            return
        
        # Apply strong corrective forces when near boundaries
        if x < margin:
            self.body.apply_force_at_local_point((strong_force, 0), (0, 0))
        elif x > width - margin:
            self.body.apply_force_at_local_point((-strong_force, 0), (0, 0))
        
        if y < margin:
            self.body.apply_force_at_local_point((0, strong_force), (0, 0))
        elif y > height - margin:
            self.body.apply_force_at_local_point((0, -strong_force), (0, 0))
        
        # Dampen velocity when near boundaries to prevent bouncing
        if x < margin * 2 or x > width - margin * 2 or y < margin * 2 or y > height - margin * 2:
            self.body.velocity = self.body.velocity * 0.8

    def check_task_completion(self):
        """Improved task completion detection with better position checking"""
        # Check if robot has reached pickup or dropoff point
        if self.target:
            # Calculate distance to target
            target_distance = math.sqrt(
                (self.target[0] - self.body.position.x)**2 + 
                (self.target[1] - self.body.position.y)**2
            )
            
            # If within completion threshold distance, check the specific point type
            if target_distance < 30:  # Increased threshold for more reliable detection
                # Check pickup points
                for point in self.environment.pickup_points:
                    point_distance = math.sqrt(
                        (point['position'][0] - self.body.position.x)**2 + 
                        (point['position'][1] - self.body.position.y)**2
                    )
                    
                    if point_distance < 30:
                        self.state = "pickup"
                        print(f"Robot {self.id} reached pickup point")
                        return
                
                # Check dropoff points
                for point in self.environment.dropoff_points:
                    point_distance = math.sqrt(
                        (point['position'][0] - self.body.position.x)**2 + 
                        (point['position'][1] - self.body.position.y)**2
                    )
                    
                    if point_distance < 30:
                        self.state = "dropoff"
                        print(f"Robot {self.id} reached dropoff point")
                        return
            
            # If close to target but not at a pickup/dropoff point, still mark task as done
            if target_distance < 40:
                print(f"Robot {self.id} reached target location but not at a specific point")
                self.state = "idle"
                self.target = None
                return
        
        # If execution reaches here, we haven't completed the task
        # Check if we're stuck (no path or no progress for a long time)
        if self.check_if_stuck(force_check=True):
            print(f"Robot {self.id} is stuck, resetting to idle")
            self.state = "idle"
            self.target = None

    def is_at_position(self, position, size):
        # Check if robot is at a specific position
        x, y = self.body.position
        px, py = position
        pw, ph = size
        
        return (x > px and x < px + pw and 
                y > py and y < py + ph)

    def apply_action(self, action):
        # Apply action from learning agent
        force = self.max_speed
        
        if action == 'up':
            self.body.apply_force_at_local_point((0, -force), (0, 0))
        elif action == 'down':
            self.body.apply_force_at_local_point((0, force), (0, 0))
        elif action == 'left':
            self.body.apply_force_at_local_point((-force, 0), (0, 0))
        elif action == 'right':
            self.body.apply_force_at_local_point((force, 0), (0, 0))
        elif action == 'up_left':
            self.body.apply_force_at_local_point((-force/1.414, -force/1.414), (0, 0))
        elif action == 'up_right':
            self.body.apply_force_at_local_point((force/1.414, -force/1.414), (0, 0))
        elif action == 'down_left':
            self.body.apply_force_at_local_point((-force/1.414, force/1.414), (0, 0))
        elif action == 'down_right':
            self.body.apply_force_at_local_point((force/1.414, force/1.414), (0, 0))
        elif action == 'stay':
            # Apply damping to stop movement
            self.body.velocity = self.body.velocity * 0.8

    def share_knowledge(self, other_robots):
        # Share discovered layout changes with other robots
        for robot in other_robots:
            if robot.id != self.id:
                # Share obstacle information
                for obs_id, obs_info in self.known_layout.items():
                    if obs_id not in robot.known_layout or robot.known_layout[obs_id]['last_seen'] < obs_info['last_seen']:
                        robot.known_layout[obs_id] = obs_info.copy()