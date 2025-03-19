from models.robot import Robot
from models.item import Item
import random

class EntityManager:
    def __init__(self, grid, width, height, drop_point):
        self.grid = grid
        self.width = width
        self.height = height
        self.drop_point = drop_point
        self.robots = []
        self.items = []
        
        self.next_robot_id = 0
        self.next_item_id = 0
    
    def is_position_valid(self, x, y):
        """Check if a position is valid for placing an entity"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        if self.grid[y][x] != 0:
            return False
        return True
    
    def add_robot(self, x, y, capacity=None):
        """Add a new robot at the specified position"""
        if not self.is_position_valid(x, y):
            print(f"Cannot place robot at ({x}, {y}): position not valid or not empty")
            return False
            
        if capacity is None:
            capacity = random.randint(10, 15)
            
        robot = Robot(self.next_robot_id, x, y, capacity)
        self.robots.append(robot)
        self.grid[y][x] = 3 
        
        self.next_robot_id += 1
        
        print(f"Added robot {robot.id} at ({x}, {y}) with capacity {capacity}kg")
        return True
    
    def edit_robot(self, robot_id, new_x, new_y, new_capacity):
        """Edit an existing robot"""
        robot = None
        for r in self.robots:
            if r.id == robot_id:
                robot = r
                break
        
        if not robot:
            print(f"Robot {robot_id} not found")
            return False
        
        if robot.carrying_items or robot.path:
            print(f"Cannot edit robot {robot_id} while it is active")
            return False
        
        if (new_x, new_y) != (robot.x, robot.y):
            if not self.is_position_valid(new_x, new_y):
                print(f"Cannot move robot to ({new_x}, {new_y}): position not valid or not empty")
                return False
            
            self.grid[robot.y][robot.x] = 0
            
            robot.x = new_x
            robot.y = new_y
            
            self.grid[robot.y][robot.x] = 3
        
        if new_capacity != robot.capacity:
            robot.capacity = new_capacity
        
        print(f"Updated robot {robot_id} to position ({new_x}, {new_y}) with capacity {new_capacity}kg")
        return True
    
    def delete_robot(self, robot_id):
        """Delete an existing robot"""
        robot = None
        for i, r in enumerate(self.robots):
            if r.id == robot_id:
                robot = r
                robot_index = i
                break
        
        if not robot:
            print(f"Robot {robot_id} not found")
            return False
        
        if robot.carrying_items:
            print(f"Cannot delete robot {robot_id} while it is carrying items")
            return False
        
        self.grid[robot.y][robot.x] = 0
        
        self.robots.pop(robot_index)
        
        print(f"Deleted robot {robot_id}")
        return True
    
    def add_item(self, x, y, weight=None):
        """Add a new item at the specified position"""
        if not self.is_position_valid(x, y):
            print(f"Cannot place item at ({x}, {y}): position not valid or not empty")
            return False
            
        if weight is None:
            weight = random.randint(1, 8)
            
        item = Item(self.next_item_id, x, y, weight)
        self.items.append(item)
        self.grid[y][x] = 2  
        
        self.next_item_id += 1
        
        print(f"Added item {item.id} at ({x}, {y}) with weight {weight}kg")
        return True
    
    def edit_item(self, item_id, new_x, new_y, new_weight):
        """Edit an existing item"""
        item = None
        for i in self.items:
            if i.id == item_id:
                item = i
                break
        
        if not item:
            print(f"Item {item_id} not found")
            return False
        
        if item.picked or item.assigned:
            print(f"Cannot edit item {item_id} while it is picked or assigned")
            return False
        
        if (new_x, new_y) != (item.x, item.y):
            if not self.is_position_valid(new_x, new_y):
                print(f"Cannot move item to ({new_x}, {new_y}): position not valid or not empty")
                return False
            
            self.grid[item.y][item.x] = 0
            
            item.x = new_x
            item.y = new_y
            
            self.grid[item.y][item.x] = 2
        
        if new_weight != item.weight:
            item.weight = new_weight
        
        print(f"Updated item {item_id} to position ({new_x}, {new_y}) with weight {new_weight}kg")
        return True
    
    def delete_item(self, item_id):
        """Delete an existing item"""
        item = None
        for i, it in enumerate(self.items):
            if it.id == item_id:
                item = it
                item_index = i
                break
        
        if not item:
            print(f"Item {item_id} not found")
            return False
        
        if item.picked or item.assigned:
            print(f"Cannot delete item {item_id} while it is picked or assigned")
            return False
        
        self.grid[item.y][item.x] = 0
        
        self.items.pop(item_index)
        
        print(f"Deleted item {item_id}")
        return True
    
    def update_grid(self, grid):
        """Update the grid reference"""
        self.grid = grid