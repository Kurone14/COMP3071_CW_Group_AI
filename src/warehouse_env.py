import pygame
import numpy as np
import random
import math

class WarehouseEnvironment:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.obstacles = []
        self.robots = []
        self.layout_version = 0
        self.shelves = []
        self.pickup_points = []
        self.dropoff_points = []
        
        # Create initial pickup and dropoff points with better placement
        self.create_logistics_points()
        
    def create_logistics_points(self):
        # Create pickup points (green) in a logical layout
        self.pickup_points = [
            {'position': (50, 500), 'size': (30, 30), 'id': 0},
            {'position': (150, 500), 'size': (30, 30), 'id': 1},
            {'position': (250, 500), 'size': (30, 30), 'id': 2},
        ]
        
        # Create dropoff points (blue) in a logical layout
        self.dropoff_points = [
            {'position': (700, 100), 'size': (30, 30), 'id': 0},
            {'position': (700, 200), 'size': (30, 30), 'id': 1},
            {'position': (700, 300), 'size': (30, 30), 'id': 2},
        ]
        
        # Create shelves (yellow) - organized in rows
        self.shelves = [
            {'position': (250, 150), 'size': (40, 100), 'id': 0},
            {'position': (350, 150), 'size': (40, 100), 'id': 1},
            {'position': (450, 150), 'size': (40, 100), 'id': 2},
            {'position': (250, 300), 'size': (40, 100), 'id': 3},
            {'position': (350, 300), 'size': (40, 100), 'id': 4},
            {'position': (450, 300), 'size': (40, 100), 'id': 5},
        ]
    
    def add_obstacle(self, position, size, is_temporary=False):
        # Add obstacles to the environment with validation
        x, y = position
        w, h = size
        
        # Ensure obstacle is within bounds
        if x < 0 or y < 0 or x + w > self.width or y + h > self.height:
            print(f"Warning: Obstacle at {position} is outside environment bounds, adjusting...")
            x = max(0, min(self.width - w, x))
            y = max(0, min(self.height - h, y))
        
        obstacle = {
            'position': (x, y),
            'size': size,
            'temporary': is_temporary,
            'id': len(self.obstacles)
        }
        self.obstacles.append(obstacle)
        
    def change_layout(self):
        # Improved layout changes that maintain warehouse organization
        self.layout_version += 1
        
        # Remove temporary obstacles
        self.obstacles = [obs for obs in self.obstacles if not obs['temporary']]
        
        # Add new temporary obstacles in sensible locations
        for _ in range(3):
            # Choose more strategic positions, avoiding critical paths
            avoid_areas = []
            
            # Areas to avoid: pickup/dropoff zones and immediate surroundings
            for point in self.pickup_points + self.dropoff_points:
                px, py = point['position']
                pw, ph = point['size']
                avoid_areas.append((px - 50, py - 50, pw + 100, ph + 100))
            
            # Find valid position for new obstacle
            valid_position = False
            attempts = 0
            x, y, width, height = 0, 0, 0, 0
            
            while not valid_position and attempts < 20:
                attempts += 1
                x = random.randint(50, self.width - 100)
                y = random.randint(50, self.height - 100)
                width = random.randint(30, 60)
                height = random.randint(30, 60)
                
                # Check if position overlaps with avoid areas
                valid_position = True
                for ax, ay, aw, ah in avoid_areas:
                    if (x < ax + aw and x + width > ax and
                        y < ay + ah and y + height > ay):
                        valid_position = False
                        break
            
            if valid_position:
                self.add_obstacle((x, y), (width, height), is_temporary=True)
            
        # Move some existing obstacles to create strategic challenges
        for obstacle in self.obstacles[:2]:  # Move first two obstacles
            x, y = obstacle['position']
            
            # Move in a more controlled way
            # Try to keep obstacles in logical positions
            new_x = max(20, min(self.width - obstacle['size'][0] - 20, 
                              x + random.randint(-80, 80)))
            new_y = max(20, min(self.height - obstacle['size'][1] - 20, 
                              y + random.randint(-80, 80)))
            
            obstacle['position'] = (new_x, new_y)
            
        # Rearrange shelves to simulate warehouse reorganization
        # Move each shelf to a new position in the same general area
        for shelf in self.shelves:
            x, y = shelf['position']
            
            # Keep shelves in a grid-like arrangement
            grid_x = 150 + (random.randint(0, 4) * 100)
            grid_y = 100 + (random.randint(0, 3) * 120)
            
            shelf['position'] = (grid_x, grid_y)
        
        print(f"Layout changed to version {self.layout_version}")
        
    def add_robot(self, robot):
        self.robots.append(robot)
        robot.environment = self
        
    def reset(self):
        # Reset environment state for new training episode
        for i, robot in enumerate(self.robots):
            # Reset robot positions with better spacing
            pos_x = 50 + (i * min(100, (self.width - 100) / max(1, len(self.robots) - 1)))
            pos_y = 50
            
            robot.body.position = (pos_x, pos_y)
            robot.body.velocity = (0, 0)
            
            # Reset robot states
            robot.path = []
            robot.detected_obstacles = []
            robot.carrying_item = False
            robot.state = "idle"
            robot.target = None
            
        # Reset layout to original
        self.obstacles = [obs for obs in self.obstacles if not obs['temporary']]
        
        # Reset logistics points
        self.create_logistics_points()
        
    def step(self, learning_agents=None, evaluator=None):
        # Update environment state
        for i, robot in enumerate(self.robots):
            # Update robot's perception
            robot.update_perception(self)
            
            # If we have learning agents, use them to control robots
            if learning_agents and i < len(learning_agents):
                action = learning_agents[i].get_action(robot, self)
                robot.apply_action(action)
            else:
                # Default behavior if no learning agents
                robot.execute_movement()
            
        # Check for collisions and resolve them
        self.check_collisions(evaluator)
        
    def check_collisions(self, evaluator=None):
        # Improved collision detection and handling
        for i, robot1 in enumerate(self.robots):
            # Check for robot-robot collisions
            for j, robot2 in enumerate(self.robots[i+1:], i+1):
                dist = math.sqrt(
                    (robot1.body.position.x - robot2.body.position.x)**2 + 
                    (robot1.body.position.y - robot2.body.position.y)**2
                )
                
                if dist < 20:  # Collision threshold for two robots
                    # Record collision in evaluator
                    if evaluator:
                        evaluator.record_collision_event(robot1.id)
                    
                    # Apply separation forces
                    force_magnitude = 50  # Separation force
                    dx = robot1.body.position.x - robot2.body.position.x
                    dy = robot1.body.position.y - robot2.body.position.y
                    
                    if dx != 0 or dy != 0:
                        # Normalize
                        length = math.sqrt(dx*dx + dy*dy)
                        dx /= length
                        dy /= length
                        
                        # Apply opposite forces to separate robots
                        robot1.body.apply_force_at_local_point(
                            (dx * force_magnitude, dy * force_magnitude), 
                            (0, 0)
                        )
                        robot2.body.apply_force_at_local_point(
                            (-dx * force_magnitude, -dy * force_magnitude), 
                            (0, 0)
                        )
        
    def render(self, screen):
        # Draw pickup points (green)
        for point in self.pickup_points:
            pygame.draw.rect(screen, (0, 255, 0), 
                            (point['position'][0], point['position'][1], 
                             point['size'][0], point['size'][1]))
            # Add label
            font = pygame.font.SysFont(None, 20)
            label = font.render(f"P{point['id']}", True, (0, 0, 0))
            screen.blit(label, (point['position'][0] + 10, point['position'][1] + 10))
        
        # Draw dropoff points (blue)
        for point in self.dropoff_points:
            pygame.draw.rect(screen, (0, 0, 255), 
                            (point['position'][0], point['position'][1], 
                             point['size'][0], point['size'][1]))
            # Add label
            font = pygame.font.SysFont(None, 20)
            label = font.render(f"D{point['id']}", True, (255, 255, 255))
            screen.blit(label, (point['position'][0] + 10, point['position'][1] + 10))
        
        # Draw shelves (yellow)
        for shelf in self.shelves:
            pygame.draw.rect(screen, (255, 255, 0), 
                            (shelf['position'][0], shelf['position'][1], 
                             shelf['size'][0], shelf['size'][1]))
            # Add label
            font = pygame.font.SysFont(None, 20)
            label = font.render(f"S{shelf['id']}", True, (0, 0, 0))
            screen.blit(label, (shelf['position'][0] + 15, shelf['position'][1] + 50))
        
        # Draw obstacles
        for obstacle in self.obstacles:
            color = (100, 100, 100) if obstacle['temporary'] else (0, 0, 0)
            pygame.draw.rect(screen, color, 
                            (obstacle['position'][0], obstacle['position'][1], 
                             obstacle['size'][0], obstacle['size'][1]))
            # Add label for permanent obstacles
            if not obstacle['temporary']:
                font = pygame.font.SysFont(None, 18)
                label = font.render(f"O{obstacle['id']}", True, (255, 255, 255))
                screen.blit(label, (obstacle['position'][0] + 5, obstacle['position'][1] + 5))