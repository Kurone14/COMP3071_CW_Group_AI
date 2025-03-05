"""
Physics Engine Module
Handles all physics-related setup and calculations
"""
import pymunk
import config

def setup_physics():
    """Initialize the physics space and set up global physics parameters"""
    space = pymunk.Space()
    space.gravity = config.GRAVITY
    return space

def add_collision_handlers(space):
    """Set up collision handlers for different object types"""
    # Robot-obstacle collision handler
    robot_obstacle_handler = space.add_collision_handler(1, 2)
    robot_obstacle_handler.begin = on_robot_obstacle_collision
    
    # Robot-robot collision handler
    robot_robot_handler = space.add_collision_handler(1, 1)
    robot_robot_handler.begin = on_robot_robot_collision
    
    return space

def on_robot_obstacle_collision(arbiter, space, data):
    """Handle collisions between robots and obstacles"""
    # Get the robot from collision shapes
    robot_shape = arbiter.shapes[0]
    obstacle_shape = arbiter.shapes[1]
    
    # We can access the robot through the shape's body's data attribute
    # if we set it up during initialization
    
    # For now, just return True to allow the physics engine to handle the collision
    return True

def on_robot_robot_collision(arbiter, space, data):
    """Handle collisions between two robots"""
    # Get the robots from collision shapes
    robot_shape1 = arbiter.shapes[0]
    robot_shape2 = arbiter.shapes[1]
    
    # We can implement collision resolution logic here
    # For example, adjust robot velocities or trigger collision avoidance behaviors
    
    # For now, just return True to allow the physics engine to handle the collision
    return True

def apply_damping(body, damping_factor=None):
    """Apply damping to a physics body to simulate friction"""
    if damping_factor is None:
        damping_factor = config.DAMPENING
    
    body.velocity = body.velocity * damping_factor