"""
Helper Functions Module
Various utility functions for the warehouse robot simulation
"""
import math
import numpy as np
import os

def create_directory_if_not_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    if hasattr(point1, 'x') and hasattr(point1, 'y'):
        # pymunk.Vec2d object
        x1, y1 = point1.x, point1.y
    else:
        # tuple/list
        x1, y1 = point1
        
    if hasattr(point2, 'x') and hasattr(point2, 'y'):
        # pymunk.Vec2d object
        x2, y2 = point2.x, point2.y
    else:
        # tuple/list
        x2, y2 = point2
    
    return math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def normalize_vector(vector):
    """Normalize a 2D vector to unit length"""
    length = math.sqrt(vector[0]**2 + vector[1]**2)
    if length > 0:
        return (vector[0] / length, vector[1] / length)
    return (0, 0)

def point_in_rect(point, rect_pos, rect_size):
    """Check if a point is inside a rectangle"""
    x, y = point
    rx, ry = rect_pos
    rw, rh = rect_size
    
    return (x >= rx and x <= rx + rw and
            y >= ry and y <= ry + rh)

def get_angle_between_vectors(v1, v2):
    """Get the angle between two vectors in radians"""
    dot = v1[0] * v2[0] + v1[1] * v2[1]
    len1 = math.sqrt(v1[0]**2 + v1[1]**2)
    len2 = math.sqrt(v2[0]**2 + v2[1]**2)
    
    # Avoid division by zero
    if len1 * len2 == 0:
        return 0
        
    # Use dot product formula: cos(θ) = (v1·v2) / (|v1|·|v2|)
    cos_angle = max(-1.0, min(1.0, dot / (len1 * len2)))
    angle = math.acos(cos_angle)
    
    # Determine sign of angle
    cross = v1[0] * v2[1] - v1[1] * v2[0]
    if cross < 0:
        angle = -angle
        
    return angle

def smooth_path(path, smoothing_factor=0.5):
    """Smooth a path to make it more natural"""
    if len(path) <= 2:
        return path
        
    smoothed_path = [path[0]]
    
    for i in range(1, len(path) - 1):
        # Get current and adjacent points
        prev = path[i-1]
        current = path[i]
        next_point = path[i+1]
        
        # Calculate smoothed point
        smoothed_x = current[0] * (1 - smoothing_factor) + (prev[0] + next_point[0]) * 0.5 * smoothing_factor
        smoothed_y = current[1] * (1 - smoothing_factor) + (prev[1] + next_point[1]) * 0.5 * smoothing_factor
        
        smoothed_path.append((smoothed_x, smoothed_y))
        
    smoothed_path.append(path[-1])
    
    return smoothed_path

def is_path_clear(start, end, obstacles, grid_size):
    """Check if a straight line path between start and end points is clear of obstacles"""
    # Create a line of points between start and end
    distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
    steps = int(distance / (grid_size * 0.5))  # Check at half grid size intervals
    steps = max(2, steps)  # At least 2 steps (start and end)
    
    for i in range(steps + 1):
        t = i / steps
        x = start[0] + t * (end[0] - start[0])
        y = start[1] + t * (end[1] - start[1])
        
        # Check if point is in any obstacle
        for obs in obstacles:
            ox, oy = obs['position']
            ow, oh = obs['size']
            
            if (x > ox and x < ox + ow and 
                y > oy and y < oy + oh):
                return False
                
    return True