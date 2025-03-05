"""
Warehouse Robot Module
Defines the warehouse robot behavior, perception, movement, and task handling
"""
import pymunk
import math
import time
import random
from collections import deque
import config
from agents.path_planning import a_star_search, check_path_collision, line_intersects_rectangle

class WarehouseRobot:
    def __init__(self, space, position, id):
        """Initialize robot with physics body and properties"""
        self.id = id
        
        # Create the robot body
        self.body = pymunk.Body(1, 100)
        self.body.position = position
        
        # Create the robot shape
        self.shape = pymunk.Circle(self.body, config.ROBOT_SIZE)
        self.shape.collision_type = 1
        self.shape.friction = config.FRICTION
        
        # Add to physics space
        space.add(self.body, self.shape)
        
        # Perception capabilities
        self.sensor_range = config.ROBOT_SENSOR_RANGE
        self.sensors = []
        self.detected_obstacles = []
        self.known_layout = {}
        
        # Planning capabilities
        self.path = []
        self.target = None
        self.target_id = None  # To track which pickup/dropoff point is targeted
        self.max_speed = config.ROBOT_MAX_SPEED
        self.state = "idle"  # idle, moving, pickup, dropoff
        
        # Task-related attributes
        self.carrying_item = False
        self.current_task = None
        self.task_start_time = None  # To track task duration
        
        # Status tracking
        self.last_replan_time = time.time()
        self.position_history = []
        self.last_progress_time = time.time()
        self.stuck_time = None
        
        # Reference to environment
        self.environment = None
    
    def update_perception(self, environment):
        """Update robot's perception of the environment"""
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
        """Calculate distance to the closest point of an obstacle"""
        x, y = self.body.position
        ox, oy = obstacle['position']
        ow, oh = obstacle['size']
        
        closest_x = max(ox, min(x, ox + ow))
        closest_y = max(oy, min(y, oy + oh))
        
        return math.sqrt((x - closest_x)**2 + (y - closest_y)**2)

    def distance_to_point(self, point):
        """Calculate Euclidean distance to a point"""
        return math.sqrt((self.body.position.x - point.x)**2 + (self.body.position.y - point.y)**2)

    def plan_path(self, target):
        """Plan a path to a target position"""
        self.target = target
        # Use the external path planning module
        self.path = a_star_search(
            self.body.position, 
            target, 
            self.detected_obstacles, 
            config.GRID_SIZE,
            self.environment.width,
            self.environment.height
        )
        self.state = "moving"
    
    def execute_movement(self):
        """Improved movement with better obstacle avoidance and path following"""
        if self.path and self.state == "moving":
            # Get next waypoint
            target = self.path[0]
            
            # Calculate direction vector
            dx = target[0] - self.body.position.x
            dy = target[1] - self.body.position.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Check for obstacles in the direct path
            collision_imminent = check_path_collision(
                (self.body.position.x, self.body.position.y), 
                target, 
                self.detected_obstacles
            )
            
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
                        if time.time() - self.last_replan_time > config.REPLAN_TIME_THRESHOLD:  # Don't replan too often
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
        self.body.velocity = self.body.velocity * config.DAMPENING
        
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

    def get_obstacle_avoidance_force(self):
        """Calculate avoidance force based on nearby obstacles"""
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
        """Check if robot is very close to any obstacle"""
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
            if max_dist < config.STUCK_THRESHOLD:
                # If we weren't previously stuck, record when we got stuck
                if self.stuck_time is None:
                    self.stuck_time = current_time
                
                # Check if we've been stuck for too long
                if force_check or current_time - self.stuck_time > config.STUCK_TIME_THRESHOLD:
                    if current_time - self.last_replan_time > config.REPLAN_TIME_THRESHOLD:
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
        margin = config.BOUNDARY_MARGIN
        strong_force = self.max_speed * config.BOUNDARY_FORCE_MULTIPLIER
        
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
        """Check if robot is at a specific position"""
        x, y = self.body.position
        px, py = position
        pw, ph = size
        
        return (x > px and x < px + pw and 
                y > py and y < py + ph)

    def apply_action(self, action):
        """Apply action from learning agent"""
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
        """Share discovered layout changes with other robots"""
        for robot in other_robots:
            if robot.id != self.id:
                # Share obstacle information
                for obs_id, obs_info in self.known_layout.items():
                    if obs_id not in robot.known_layout or robot.known_layout[obs_id]['last_seen'] < obs_info['last_seen']:
                        robot.known_layout[obs_id] = obs_info.copy()