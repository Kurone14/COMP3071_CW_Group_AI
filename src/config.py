# Configuration settings for the warehouse robot simulation

# Display settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
CAPTION = "Warehouse Robot Simulation"

# Robot settings
MAX_ROBOTS = 10
ROBOT_SIZE = 10
ROBOT_MAX_SPEED = 80  # Decreased for better control
ROBOT_SENSOR_RANGE = 150  # Increased range
ROBOT_COLORS = {
    "idle": (255, 0, 0),         # Red
    "moving": (255, 165, 0),     # Orange
    "pickup": (0, 255, 0),       # Green
    "dropoff": (0, 0, 255),      # Blue
    "carrying": (128, 0, 128)    # Purple when carrying items
}

# Environment settings
GRID_SIZE = 20
OBSTACLE_COLORS = {
    "permanent": (0, 0, 0),     # Black
    "temporary": (100, 100, 100) # Gray
}
PICKUP_COLOR = (0, 255, 0)      # Green
DROPOFF_COLOR = (0, 0, 255)     # Blue
SHELF_COLOR = (255, 255, 0)     # Yellow

# Learning agent settings
LEARNING_RATE = 0.1
DISCOUNT_FACTOR = 0.9
EXPLORATION_RATE = 1.0
EXPLORATION_DECAY = 0.995
MIN_EXPLORATION_RATE = 0.01

# Task settings
TASK_ASSIGNMENT_INTERVAL = 30  # Assign tasks more frequently
LAYOUT_CHANGE_INTERVAL = 500   # Change layout every 500 steps
MIN_STEPS_BETWEEN_LAYOUT_CHANGES = 1000

# Physics settings
GRAVITY = (0, 0)
FRICTION = 0.7
DAMPENING = 0.9  # Higher dampening for better control

# Stuck detection settings
STUCK_CHECK_INTERVAL = 120  # Check for stuck robots every 120 frames
STUCK_THRESHOLD = 20  # Distance below which a robot is considered stuck
STUCK_TIME_THRESHOLD = 3.0  # Time in seconds after which to attempt unstuck actions
REPLAN_TIME_THRESHOLD = 2.0  # Minimum time between replanning attempts

# Boundary settings
BOUNDARY_MARGIN = 30  # Margin for boundary enforcement
BOUNDARY_FORCE_MULTIPLIER = 3.0  # Force multiplier for boundary correction

# Paths
MODEL_DIR = "models"
REPORT_FILE = "performance_report.png"