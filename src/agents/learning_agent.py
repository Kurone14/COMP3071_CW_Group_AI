"""
Robot Learning Agent Module
Q-learning based agent for controlling warehouse robots
"""
import pickle
import numpy as np
import random
import os
import math
import config

class RobotLearningAgent:
    def __init__(self, robot_id):
        """Initialize the learning agent for a specific robot"""
        self.robot_id = robot_id
        self.learning_rate = config.LEARNING_RATE
        self.discount_factor = config.DISCOUNT_FACTOR
        self.exploration_rate = config.EXPLORATION_RATE
        self.exploration_decay = config.EXPLORATION_DECAY
        self.min_exploration_rate = config.MIN_EXPLORATION_RATE
        self.q_table = {}  # State-action value function
        self.state_history = []
        self.action_history = []
        self.reward_history = []
        
    def initialize_learning_model(self):
        """Initialize Q-learning model"""
        self.q_table = {}
        
    def get_state_representation(self, robot, environment):
        """Create a more informative discrete state representation"""
        # Simplify robot position to grid cells
        grid_size = 50
        x_pos = int(robot.body.position.x / grid_size)
        y_pos = int(robot.body.position.y / grid_size)
        
        # Add information about nearby obstacles (closest 3)
        obstacle_info = []
        if robot.detected_obstacles:
            # Sort obstacles by distance
            sorted_obstacles = sorted(
                robot.detected_obstacles, 
                key=lambda obs: (
                    (obs['position'][0] - robot.body.position.x)**2 + 
                    (obs['position'][1] - robot.body.position.y)**2
                )
            )
            
            # Take closest 3 obstacles
            for obs in sorted_obstacles[:3]:
                rel_x = int((obs['position'][0] - robot.body.position.x) / grid_size)
                rel_y = int((obs['position'][1] - robot.body.position.y) / grid_size)
                obstacle_info.append((rel_x, rel_y))
        
        # Sort obstacle info to ensure consistent state representation
        obstacle_info.sort()
        
        # Add target information if exists
        target_info = None
        if robot.target:
            target_rel_x = int((robot.target[0] - robot.body.position.x) / grid_size)
            target_rel_y = int((robot.target[1] - robot.body.position.y) / grid_size)
            target_info = (target_rel_x, target_rel_y)
        
        # Add carrying state
        carrying = 1 if robot.carrying_item else 0
        
        # Create state tuple
        state = (x_pos, y_pos, carrying, tuple(obstacle_info), target_info)
        return state
        
    def get_action(self, robot, environment):
        """Choose an action using epsilon-greedy policy"""
        # Get current state
        state = self.get_state_representation(robot, environment)
        
        # Epsilon-greedy action selection
        if random.random() < self.exploration_rate:
            # Explore: random action
            action = random.choice(self.get_possible_actions(robot))
        else:
            # Exploit: best known action
            action = self.get_best_action(state, robot)
        
        return action
    
    def get_possible_actions(self, robot):
        """Define possible actions for the robot"""
        # Define possible actions: move in 8 directions or stay
        return ['up', 'down', 'left', 'right', 'up_left', 'up_right', 'down_left', 'down_right', 'stay']
    
    def get_best_action(self, state, robot):
        """Get best action from Q-table for the current state"""
        if state not in self.q_table:
            # If state not in Q-table, initialize it
            self.q_table[state] = {action: 0 for action in self.get_possible_actions(robot)}
        
        # Find action with highest Q-value
        best_action = max(self.q_table[state], key=self.q_table[state].get)
        return best_action
    
    def calculate_reward(self, robot, environment, prev_state, action, new_state):
        """Calculate reward based on various factors"""
        reward = 0
        
        # Penalty for collisions
        if self.check_collision(robot, environment):
            reward -= 10
        
        # Reward for moving towards target if one exists
        if robot.target:
            prev_dist = self.distance_to_target(prev_state[:2], robot.target)
            new_dist = self.distance_to_target(new_state[:2], robot.target)
            
            if new_dist < prev_dist:
                # Reward is proportional to distance reduction
                reward += 1 * (prev_dist - new_dist) / prev_dist if prev_dist > 0 else 0
            else:
                # Smaller penalty for moving away from target
                reward -= 0.5 * (new_dist - prev_dist) / prev_dist if prev_dist > 0 else 0
        
        # Reward for completing tasks
        if robot.state == "pickup" and not robot.carrying_item:
            reward += 10  # Significant reward for pickup
            robot.carrying_item = True
        
        if robot.state == "dropoff" and robot.carrying_item:
            reward += 20  # Even bigger reward for dropoff (completes the cycle)
            robot.carrying_item = False
        
        # Small penalty for staying idle to encourage movement
        if action == 'stay' and robot.target:
            reward -= 0.2
        
        # Small penalty for energy usage (all movement actions)
        if action != 'stay':
            reward -= 0.1
        
        return reward
    
    def check_collision(self, robot, environment):
        """Check if robot is colliding with any obstacle or other robot"""
        # Check collision with obstacles
        for obstacle in environment.obstacles:
            x, y = robot.body.position
            ox, oy = obstacle['position']
            ow, oh = obstacle['size']
            
            if (x > ox and x < ox + ow and 
                y > oy and y < oy + oh):
                return True
        
        # Check for collisions with other robots
        for other_robot in environment.robots:
            if other_robot.id != robot.id:
                dist = math.sqrt(
                    (robot.body.position.x - other_robot.body.position.x)**2 + 
                    (robot.body.position.y - other_robot.body.position.y)**2
                )
                if dist < 20:  # Collision threshold
                    return True
        
        return False
    
    def distance_to_target(self, position, target):
        """Calculate Euclidean distance"""
        return math.sqrt((position[0] * 50 - target[0])**2 + (position[1] * 50 - target[1])**2)
    
    def train(self, environment, robot, episode_num):
        """Train the agent for one step"""
        # Get current state
        state = self.get_state_representation(robot, environment)
        
        # Choose action
        action = self.get_action(robot, environment)
        
        # Apply action
        robot.apply_action(action)
        
        # Get new state
        new_state = self.get_state_representation(robot, environment)
        
        # Calculate reward
        reward = self.calculate_reward(robot, environment, state, action, new_state)
        
        # Update Q-table
        self.update_q_table(state, action, reward, new_state)
        
        # Record history
        self.state_history.append(state)
        self.action_history.append(action)
        self.reward_history.append(reward)
        
        # Decay exploration rate
        self.exploration_rate = max(
            self.min_exploration_rate, 
            self.exploration_rate * self.exploration_decay
        )
        
        return reward
    
    def update_q_table(self, state, action, reward, new_state):
        """Update Q-table using Q-learning update rule"""
        # Initialize state in Q-table if not present
        if state not in self.q_table:
            self.q_table[state] = {a: 0 for a in self.get_possible_actions(None)}
        
        # Initialize new state in Q-table if not present
        if new_state not in self.q_table:
            self.q_table[new_state] = {a: 0 for a in self.get_possible_actions(None)}
        
        # Q-learning update rule
        best_next_action = max(self.q_table[new_state], key=self.q_table[new_state].get)
        self.q_table[state][action] = self.q_table[state][action] + self.learning_rate * (
            reward + 
            self.discount_factor * self.q_table[new_state][best_next_action] - 
            self.q_table[state][action]
        )
    
    def save_model(self, filename):
        """Save the Q-table to a file"""
        with open(filename, 'wb') as f:
            pickle.dump(self.q_table, f)
    
    def load_model(self, filename):
        """Load the Q-table from a file"""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.q_table = pickle.load(f)