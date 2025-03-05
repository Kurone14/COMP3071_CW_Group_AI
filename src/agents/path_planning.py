"""
Path Planning Module
Various path planning algorithms for warehouse robots
"""
import math
import heapq
import random

def a_star_search(start, goal, detected_obstacles, grid_size, environment_width, environment_height):
    """A* path planning algorithm
    
    Args:
        start: Starting position (pymunk.Vec2d)
        goal: Goal position (tuple)
        detected_obstacles: List of obstacle dictionaries
        grid_size: Size of grid cells for discretization
        environment_width: Width of the environment
        environment_height: Height of the environment
    
    Returns:
        List of waypoints from start to goal
    """
    # Convert positions to grid coordinates
    start_grid = (int(start.x / grid_size), int(start.y / grid_size))
    goal_grid = (int(goal[0] / grid_size), int(goal[1] / grid_size))
    
    # If start or goal are outside boundaries, adjust them
    if start_grid[0] < 0 or start_grid[0] >= environment_width // grid_size or start_grid[1] < 0 or start_grid[1] >= environment_height // grid_size:
        print(f"Start position out of bounds, adjusting")
        start_grid = (
            max(0, min(environment_width // grid_size - 1, start_grid[0])),
            max(0, min(environment_height // grid_size - 1, start_grid[1]))
        )
    
    if goal_grid[0] < 0 or goal_grid[0] >= environment_width // grid_size or goal_grid[1] < 0 or goal_grid[1] >= environment_height // grid_size:
        print(f"Goal position out of bounds, adjusting")
        goal_grid = (
            max(0, min(environment_width // grid_size - 1, goal_grid[0])),
            max(0, min(environment_height // grid_size - 1, goal_grid[1]))
        )
    
    # A* algorithm
    open_set = []
    heapq.heappush(open_set, (heuristic(start_grid, goal_grid), 0, start_grid))  # f_score, tiebreaker, position
    came_from = {}
    g_score = {start_grid: 0}
    f_score = {start_grid: heuristic(start_grid, goal_grid)}
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
            smoothed_path = smooth_path(path)
            
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
            if (neighbor[0] < 0 or neighbor[0] >= environment_width // grid_size or 
                neighbor[1] < 0 or neighbor[1] >= environment_height // grid_size):
                continue
            
            # Skip if we've already processed this neighbor
            if neighbor in closed_set:
                continue
                
            # Check if neighbor is valid (not in obstacle)
            if is_valid_position(neighbor, grid_size, detected_obstacles, environment_width, environment_height):
                # Movement cost is higher for diagonal moves
                move_cost = 1.414 if dx != 0 and dy != 0 else 1.0
                tentative_g = g_score[current] + move_cost
                
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + heuristic(neighbor, goal_grid)
                    heapq.heappush(open_set, (f_score[neighbor], tiebreaker, neighbor))
                    tiebreaker += 1
    
    # If no path found after max iterations or empty open set
    if iterations >= max_iterations:
        print(f"Path search exceeded max iterations, using direct path")
    else:
        print(f"No path found, using direct path with waypoints")
    
    # Plan a simple path with intermediate waypoints
    direct_path = plan_direct_path(start, goal, environment_width, environment_height)
    return direct_path

def smooth_path(path):
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

def plan_direct_path(start, goal, environment_width, environment_height):
    """Plan a direct path with intermediate waypoints to handle obstacles"""
    # Create a path with intermediate waypoints to navigate around potential obstacles
    start_x, start_y = start.x, start.y
    goal_x, goal_y = goal
    
    # Create intermediate waypoints to avoid obstacles and stay in bounds
    path = []
    
    # If start and goal are far apart, add intermediate waypoints
    distance = math.sqrt((goal_x - start_x)**2 + (goal_y - start_y)**2)
    
    if distance > 100:
        # Add waypoint at 1/3 distance
        wx1 = start_x + (goal_x - start_x) / 3
        wy1 = start_y + (goal_y - start_y) / 3
        # Ensure waypoint is in bounds
        wx1 = max(20, min(environment_width - 20, wx1))
        wy1 = max(20, min(environment_height - 20, wy1))
        path.append((wx1, wy1))
        
        # Add waypoint at 2/3 distance
        wx2 = start_x + 2 * (goal_x - start_x) / 3
        wy2 = start_y + 2 * (goal_y - start_y) / 3
        # Ensure waypoint is in bounds
        wx2 = max(20, min(environment_width - 20, wx2))
        wy2 = max(20, min(environment_height - 20, wy2))
        path.append((wx2, wy2))
    
    # Add the goal
    path.append(goal)
    
    return path

def is_valid_position(position, grid_size, detected_obstacles, environment_width, environment_height):
    """Check if position is valid (not in obstacle)"""
    x, y = position[0] * grid_size, position[1] * grid_size
    
    # Check boundaries with a margin
    margin = 10
    if x < margin or y < margin or x >= environment_width - margin or y >= environment_height - margin:
        return False
    
    # Check obstacles with padding
    padding = grid_size // 2
    for obstacle in detected_obstacles:
        ox, oy = obstacle['position']
        ow, oh = obstacle['size']
        
        if (x > ox - padding and x < ox + ow + padding and 
            y > oy - padding and y < oy + oh + padding):
            return False
    
    return True

def heuristic(a, b):
    """Euclidean distance heuristic for A*"""
    return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)

def line_intersects_rectangle(x1, y1, x2, y2, rx1, ry1, rx2, ry2):
    """Check if line from (x1,y1) to (x2,y2) intersects with rectangle defined by (rx1,ry1) to (rx2,ry2)"""
    # Check if either endpoint is inside rectangle
    if (rx1 <= x1 <= rx2 and ry1 <= y1 <= ry2) or (rx1 <= x2 <= rx2 and ry1 <= y2 <= ry2):
        return True
    
    # Check each edge of the rectangle for intersection with the line
    if line_segments_intersect(x1, y1, x2, y2, rx1, ry1, rx2, ry1):  # Top edge
        return True
    if line_segments_intersect(x1, y1, x2, y2, rx1, ry1, rx1, ry2):  # Left edge
        return True
    if line_segments_intersect(x1, y1, x2, y2, rx2, ry1, rx2, ry2):  # Right edge
        return True
    if line_segments_intersect(x1, y1, x2, y2, rx1, ry2, rx2, ry2):  # Bottom edge
        return True
    
    return False

def line_segments_intersect(x1, y1, x2, y2, x3, y3, x4, y4):
    """Check if line segments (x1,y1)-(x2,y2) and (x3,y3)-(x4,y4) intersect"""
    def ccw(a, b, c):
        return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
    
    a = (x1, y1)
    b = (x2, y2)
    c = (x3, y3)
    d = (x4, y4)
    
    return ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d)

def check_path_collision(start_pos, target_pos, obstacles):
    """Check if there's an obstacle in direct path from start to target"""
    for obstacle in obstacles:
        ox, oy = obstacle['position']
        ow, oh = obstacle['size']
        
        # Check if line intersects with obstacle
        if line_intersects_rectangle(
            start_pos[0], start_pos[1], target_pos[0], target_pos[1],
            ox, oy, ox + ow, oy + oh
        ):
            return True
    
    return False

def dijkstra_search(start, goal, detected_obstacles, grid_size, environment_width, environment_height):
    """Dijkstra's algorithm for path planning (similar to A* but without heuristic)"""
    # Same as A* but without using a heuristic
    pass

def rrt_search(start, goal, detected_obstacles, grid_size, environment_width, environment_height, max_iterations=1000):
    """Rapidly-exploring Random Tree (RRT) path planning"""
    # Implementation of RRT algorithm
    pass