import tkinter as tk
from tkinter import messagebox
from simulation.entity_manager import EntityManager
from simulation.movement_controller import MovementController
from simulation.stall_detector import StallDetector
from simulation.performance_tracker import PerformanceTracker
from gui.entity_dialogs import RobotEditDialog, ItemEditDialog

class WarehouseSimulation:
    """Main simulation class that handles the warehouse environment"""
    def __init__(self, width=20, height=20, robot_count=3, item_count=10, obstacle_density=0.1, 
                 gui=None, path_finder=None, item_assigner=None):
        self.width = width
        self.height = height
        self.grid = [[0 for _ in range(width)] for _ in range(height)]
        
        self.drop_point = None
        self.obstacle_density = obstacle_density
        
        self.running = False
        self.paused = False
        
        self.gui = gui
        self.path_finder = path_finder
        self.item_assigner = item_assigner
        
        self.entity_manager = None
        self.movement_controller = None
        self.stall_detector = None

        self.robot_start_positions = {} 

        
        self.performance_tracker = PerformanceTracker()
        
        if all([gui, path_finder, item_assigner]):
            self._initialize_components()
            self.initialize_environment(robot_count, item_count)
            
            gui.set_button_commands(
                self.start_simulation,
                self.toggle_pause,
                self.reset_simulation,
                self.add_robot,
                self.add_item,
                self.edit_robot,
                self.delete_robot,
                self.edit_item,
                self.delete_item,
                self.set_drop_point,
                self.toggle_obstacle,
                self.resize_grid,
                self.add_roadblock
            )
            
            gui.enable_entity_controls(True)
    
    def _initialize_components(self):
        """Initialize simulation components"""
        self.entity_manager = EntityManager(self.grid, self.width, self.height, self.drop_point)
        self.movement_controller = MovementController(
            self.grid, self.width, self.height, self.drop_point, self.path_finder
        )
        self.stall_detector = StallDetector(
            self.grid, self.width, self.height, self.drop_point, self.path_finder
        )
    
    def initialize_environment(self, robot_count, item_count):
        """Initialize the warehouse environment"""
        self._generate_grid()
        
        self._setup_drop_point()
        
        if self.entity_manager:
            self.entity_manager.grid = self.grid
            self.entity_manager.drop_point = self.drop_point
        
        if self.movement_controller:
            self.movement_controller.grid = self.grid
            self.movement_controller.drop_point = self.drop_point
            
        if self.stall_detector:
            self.stall_detector.grid = self.grid
            self.stall_detector.drop_point = self.drop_point
            
        if self.path_finder:
            self.path_finder.grid = self.grid
            self.path_finder.drop_point = self.drop_point
            
        if self.item_assigner:
            self.item_assigner.grid = self.grid
        
        self.entity_manager.robots = []
        self.entity_manager.items = []
        self.entity_manager.next_robot_id = 0
        self.entity_manager.next_item_id = 0
        
        self.performance_tracker.reset()
        
        self._place_initial_robots(robot_count)
        
        if item_count > 0:
            self._place_initial_items(item_count)
        
        if self.gui:
            self.gui.setup_robot_status_displays(self.entity_manager.robots)
            self.gui.items_left_var.set(f"Items left: {len(self.entity_manager.items)}")
            self.gui.draw_environment(
                self.grid, self.width, self.height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
            self.gui.update_items_list(self.entity_manager.items)
            
            if hasattr(self.gui, 'update_performance_stats'):
                self.gui.update_performance_stats(self.performance_tracker.format_statistics())
    
    def _generate_grid(self):
        """Generate grid with obstacles"""
        import random
        
        self.grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        random.seed(42)
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < self.obstacle_density:
                    self.grid[y][x] = 1  
                    
        random.seed()
    
    def _setup_drop_point(self):
        """Set up the drop point in the environment"""
        drop_x = self.width - 3
        drop_y = self.height - 3
        
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                if 0 <= drop_y + dy < self.height and 0 <= drop_x + dx < self.width:
                    self.grid[drop_y + dy][drop_x + dx] = 0 
        
        self.drop_point = (drop_x, drop_y)
        self.grid[drop_y][drop_x] = 4  
    
    def _place_initial_robots(self, robot_count):
        """Place initial robots in the environment"""
        for i in range(robot_count):
            robot_x = 2 + i * 2  
            robot_y = self.height - 2
            
            if robot_x >= self.width:
                robot_x = robot_x % (self.width - 4) + 2
                robot_y -= 1
            
            while self.grid[robot_y][robot_x] != 0:
                robot_x = (robot_x + 1) % (self.width - 2) + 1
            
            capacity = 10 + (i * 2) % 6  
            self.entity_manager.add_robot(robot_x, robot_y, capacity)

            newest_robot = self.entity_manager.robots[-1]
            self.robot_start_positions[newest_robot.id] = (robot_x, robot_y)
    
    def _place_initial_items(self, item_count):
        """Place initial items in the environment"""
        import random
        
        for i in range(item_count):
            item_x = random.randint(1, self.width - 2)
            item_y = random.randint(1, self.height // 2)
            
            while self.grid[item_y][item_x] != 0:
                item_x = random.randint(1, self.width - 2)
                item_y = random.randint(1, self.height - 2)
            
            weight = random.randint(1, 8)
            self.entity_manager.add_item(item_x, item_y, weight)
    
    def add_robot(self, x, y, capacity=None):
        """Add a new robot at the specified position"""
        if self.entity_manager.add_robot(x, y, capacity):
            newest_robot = self.entity_manager.robots[-1]
            self.robot_start_positions[newest_robot.id] = (x, y)
            
            if self.gui:
                self.gui.setup_robot_status_displays(self.entity_manager.robots)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
            return True
        return False
    
    def edit_robot(self, robot_id):
        """Edit an existing robot"""
        robot = None
        for r in self.entity_manager.robots:
            if r.id == robot_id:
                robot = r
                break
                
        if not robot:
            return False
            
        if robot.carrying_items or robot.path:
            print(f"Cannot edit robot {robot_id} while it is active")
            return False
            
        if self.gui:
            result = RobotEditDialog.show_dialog(self.gui.root, robot)
            
            if result["cancelled"]:
                return False
                
            if self.entity_manager.edit_robot(
                robot_id, result["x"], result["y"], result["capacity"]
            ):
                self.gui.setup_robot_status_displays(self.entity_manager.robots)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
                return True
        return False
    
    def delete_robot(self, robot_id):
        """Delete an existing robot"""
        if self.entity_manager.delete_robot(robot_id):
            if robot_id in self.robot_start_positions:
                del self.robot_start_positions[robot_id]
                
            if self.gui:
                self.gui.setup_robot_status_displays(self.entity_manager.robots)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
            return True
        return False
    
    def add_item(self, x, y, weight=None):
        """Add a new item at the specified position"""
        if self.entity_manager.add_item(x, y, weight):
            if self.gui:
                self.gui.update_items_list(self.entity_manager.items)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
                self.gui.items_left_var.set(f"Items left: {len(self.entity_manager.items)}")
            return True
        return False
    
    def edit_item(self, item_id):
        """Edit an existing item"""
        item = None
        for i in self.entity_manager.items:
            if i.id == item_id:
                item = i
                break
                
        if not item:
            return False
            
        if item.picked or item.assigned:
            print(f"Cannot edit item {item_id} while it is picked or assigned")
            return False
            
        if self.gui:
            result = ItemEditDialog.show_dialog(self.gui.root, item)
            
            if result["cancelled"]:
                return False
                
            if self.entity_manager.edit_item(
                item_id, result["x"], result["y"], result["weight"]
            ):
                self.gui.update_items_list(self.entity_manager.items)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
                return True
        return False
    
    def delete_item(self, item_id):
        """Delete an existing item"""
        if self.entity_manager.delete_item(item_id):
            if self.gui:
                self.gui.update_items_list(self.entity_manager.items)
                self.gui.draw_environment(
                    self.grid, self.width, self.height, 
                    self.drop_point, self.entity_manager.robots, self.entity_manager.items
                )
                self.gui.items_left_var.set(f"Items left: {len(self.entity_manager.items)}")
            return True
        return False
    
    def set_drop_point(self, x, y):
        """Set drop point to a new position"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            print(f"Invalid drop point coordinates: ({x}, {y})")
            return False
        
        if self.drop_point:
            old_x, old_y = self.drop_point
            self.grid[old_y][old_x] = 0
        
        self.drop_point = (x, y)
        self.grid[y][x] = 4  
        
        if self.entity_manager:
            self.entity_manager.drop_point = self.drop_point
        if self.movement_controller:
            self.movement_controller.drop_point = self.drop_point
        if self.stall_detector:
            self.stall_detector.drop_point = self.drop_point
        if self.path_finder:
            self.path_finder.drop_point = self.drop_point
        
        if self.gui:
            self.gui.draw_environment(
                self.grid, self.width, self.height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
        
        print(f"Drop point set to ({x}, {y})")
        return True
    
    def toggle_obstacle(self, x, y):
        """Toggle obstacle at position (x,y)"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            print(f"Invalid coordinates: ({x}, {y})")
            return False
        
        if self.grid[y][x] not in [0, 1]:  
            print(f"Cannot toggle obstacle at ({x}, {y}): position is occupied")
            return False
        
        if self.grid[y][x] == 0:
            self.grid[y][x] = 1  
            print(f"Added obstacle at ({x}, {y})")
        else:
            self.grid[y][x] = 0  
            print(f"Removed obstacle at ({x}, {y})")
        
        if self.gui:
            self.gui.draw_environment(
                self.grid, self.width, self.height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
        
        return True
    
    def add_roadblock(self, x, y):
        """Add a roadblock during simulation"""
        if not (0 <= x < self.width and 0 <= y < self.height):
            print(f"Invalid roadblock coordinates: ({x}, {y})")
            return False
        
        if self.grid[y][x] != 0: 
            print(f"Cannot add roadblock at ({x}, {y}): position is occupied")
            return False
        
        self.grid[y][x] = 1 
        print(f"Added roadblock at ({x}, {y})")
        
        if self.gui:
            self.gui.draw_environment(
                self.grid, self.width, self.height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
        
        self._recalculate_affected_robot_paths(x, y)
        
        return True
    
    def _recalculate_affected_robot_paths(self, block_x, block_y):
        """Recalculate paths for robots that are affected by a new roadblock"""
        for robot in self.entity_manager.robots:
            if not robot.path:
                continue
            
            path_coords = [(py, px) for py, px in robot.path]
            block_pos = (block_y, block_x)
            
            if block_pos in path_coords:
                print(f"Robot {robot.id}'s path is blocked by new roadblock. Recalculating path.")
                
                if robot.carrying_items:
                    new_path = self.path_finder.a_star_pathfinding(
                        (robot.y, robot.x), 
                        (self.drop_point[1], self.drop_point[0]), 
                        self.entity_manager.robots,
                        robot.id,
                        robot.current_weight
                    )
                elif robot.target_items:
                    first_item = robot.target_items[0]
                    new_path = self.path_finder.a_star_pathfinding(
                        (robot.y, robot.x), 
                        (first_item.y, first_item.x), 
                        self.entity_manager.robots,
                        robot.id
                    )
                else:
                    new_path = []
                
                if new_path:
                    robot.path = new_path
                    print(f"New path found for robot {robot.id}.")
                else:
                    print(f"WARNING: Robot {robot.id} can't find new path. Will retry next cycle.")
                    robot.path = []  
    
    def resize_grid(self, new_width, new_height):
        """Resize the grid, preserving entities when possible"""
        if new_width < self.width or new_height < self.height:
            messagebox.showwarning("Resize Grid", "Grid can only be expanded, not reduced in size.")
            return False
        
        old_grid = self.grid
        old_width, old_height = self.width, self.height
        
        new_grid = [[0 for _ in range(new_width)] for _ in range(new_height)]
        
        for y in range(old_height):
            for x in range(old_width):
                new_grid[y][x] = old_grid[y][x]
        
        self.width, self.height = new_width, new_height
        self.grid = new_grid
        
        if self.entity_manager:
            self.entity_manager.grid = new_grid
            self.entity_manager.width = new_width
            self.entity_manager.height = new_height
        if self.movement_controller:
            self.movement_controller.grid = new_grid
            self.movement_controller.width = new_width
            self.movement_controller.height = new_height
        if self.stall_detector:
            self.stall_detector.grid = new_grid
            self.stall_detector.width = new_width
            self.stall_detector.height = new_height
        if self.path_finder:
            self.path_finder.grid = new_grid
            self.path_finder.width = new_width
            self.path_finder.height = new_height
        
        if self.gui and hasattr(self.gui, 'canvas_view'):
            canvas = self.gui.canvas_view.canvas
            canvas.config(width=new_width*self.gui.canvas_view.cell_size, 
                        height=new_height*self.gui.canvas_view.cell_size)
            self.gui.canvas_view.width = new_width
            self.gui.canvas_view.height = new_height
        
        if self.gui:
            self.gui.draw_environment(
                self.grid, new_width, new_height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
        
        print(f"Grid resized from {old_width}x{old_height} to {new_width}x{new_height}")
        return True
    
    def start_simulation(self):
        """Start the simulation"""
        if not self.running:
            self.running = True
            self.paused = False
            
            self.performance_tracker.start()
            
            if self.gui:
                self.gui.start_button.config(state=tk.DISABLED)
                self.gui.pause_button.config(state=tk.NORMAL, text="Pause")
                
                self.gui.enable_entity_controls(False)
                
                self.gui.root.after(300, self.simulation_loop)
    
    def toggle_pause(self):
        """Pause or resume the simulation"""
        self.paused = not self.paused
        
        if self.paused:
            self.performance_tracker.stop()
        else:
            self.performance_tracker.start()
            
        if self.gui:
            if self.paused:
                self.gui.pause_button.config(text="Resume")
            else:
                self.gui.pause_button.config(text="Pause")
                self.gui.root.after(300, self.simulation_loop)
        
    def reset_simulation(self):
        """Reset the simulation while preserving environment"""
        self.running = False
        self.paused = False
        
        self.performance_tracker.stop()
        
        if self.stall_detector:
            self.stall_detector.reset()
        
        current_drop_point = self.drop_point
        
        preserved_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == 1:
                    preserved_grid[y][x] = 1
                elif self.grid[y][x] == 4:
                    preserved_grid[y][x] = 4
        
        self.grid = preserved_grid
        
        if self.entity_manager:
            self.entity_manager.grid = preserved_grid
        if self.movement_controller:
            self.movement_controller.grid = preserved_grid
        if self.stall_detector:
            self.stall_detector.grid = preserved_grid
        if self.path_finder:
            self.path_finder.grid = preserved_grid
        if self.item_assigner:
            self.item_assigner.grid = preserved_grid
        
        for robot in self.entity_manager.robots:
            if 0 <= robot.y < self.height and 0 <= robot.x < self.width:
                self.grid[robot.y][robot.x] = 0
            
            if robot.id in self.robot_start_positions:
                start_x, start_y = self.robot_start_positions[robot.id]
                robot.x, robot.y = start_x, start_y
            
            robot.carrying_items = []
            robot.target_items = []
            robot.current_weight = 0
            robot.path = []
            robot.steps = 0
            
            if 0 <= robot.y < self.height and 0 <= robot.x < self.width:
                self.grid[robot.y][robot.x] = 3 
        
        for item in self.entity_manager.items:
            item.picked = False
            item.assigned = False
            
            if 0 <= item.y < self.height and 0 <= item.x < self.width:
                self.grid[item.y][item.x] = 2  
        
        self.performance_tracker.reset()
        
        if self.gui:
            self.gui.setup_robot_status_displays(self.entity_manager.robots)
            self.gui.items_left_var.set(f"Items left: {len(self.entity_manager.items)}")
            self.gui.draw_environment(
                self.grid, self.width, self.height, 
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
            self.gui.update_items_list(self.entity_manager.items)
            
            if hasattr(self.gui, 'update_performance_stats'):
                self.gui.update_performance_stats(self.performance_tracker.format_statistics())
            
            self.gui.start_button.config(state=tk.NORMAL)
            self.gui.pause_button.config(state=tk.DISABLED)
            
            self.gui.enable_entity_controls(True)
        
        print("Simulation reset - all entities preserved and robots returned to starting positions")
        return True

    def simulation_loop(self):
        """Main simulation loop with progress tracking and stall recovery"""
        if not self.running or self.paused:
            return
            
        remaining_items = [item for item in self.entity_manager.items if not item.picked]
        carrying_items = sum(len(robot.carrying_items) for robot in self.entity_manager.robots)
        print(f"Remaining items: {len(remaining_items)}, Being carried: {carrying_items}")
        
        stall_time, remaining_items = self.stall_detector.check_progress(
            self.entity_manager.robots, 
            self.entity_manager.items
        )
        
        if stall_time > 15:
            self.stall_detector.level1_recovery(
                self.entity_manager.robots, 
                self.entity_manager.items, 
                stall_time
            )
            
        if stall_time > 20:
            self.stall_detector.level2_recovery(
                self.entity_manager.robots, 
                self.entity_manager.items, 
                stall_time
            )
            
        if stall_time > 35:
            self.stall_detector.level3_recovery(
                self.entity_manager.robots,
                self.entity_manager.items,
                stall_time,
                remaining_items
            )
            
        if stall_time > 50:
            force_complete = self.stall_detector.level4_recovery(
                self.entity_manager.robots,
                self.entity_manager.items,
                stall_time,
                remaining_items
            )
            
            if force_complete:
                self.running = False
                self.performance_tracker.stop()
                if self.gui:
                    self.gui.pause_button.config(state=tk.DISABLED)
                    self.gui.start_button.config(state=tk.NORMAL, text="Start")
                    
                    if hasattr(self.gui, 'update_performance_stats'):
                        self.gui.update_performance_stats(self.performance_tracker.format_statistics())
                        
                print("Simulation completed: All items collected and delivered!")
                return
        
        if self.stall_detector.check_timeout():
            print("TIMEOUT: Maximum simulation time reached")
            self.running = False
            self.performance_tracker.stop()
            if self.gui:
                self.gui.pause_button.config(state=tk.DISABLED)
                self.gui.start_button.config(state=tk.NORMAL, text="Start")
                
                if hasattr(self.gui, 'update_performance_stats'):
                    self.gui.update_performance_stats(self.performance_tracker.format_statistics())
            return
        
        self.item_assigner.assign_items_to_robots(
            self.entity_manager.robots,
            self.entity_manager.items,
            self.drop_point
        )
        
        steps_taken = self.movement_controller.move_robots(
            self.entity_manager.robots,
            lambda: self._on_progress_made()
        )
        
        self.performance_tracker.add_steps(steps_taken)
        
        if self.gui:
            self.gui.draw_environment(
                self.grid, self.width, self.height,
                self.drop_point, self.entity_manager.robots, self.entity_manager.items
            )
            self.gui.update_status(
                self.entity_manager.robots,
                self.entity_manager.items
            )
            
            if hasattr(self.gui, 'update_performance_stats'):
                self.gui.update_performance_stats(self.performance_tracker.format_statistics())
        
        all_delivered = self._check_completion(remaining_items)
        if all_delivered:
            self.running = False
            self.performance_tracker.stop()
            if self.gui:
                self.gui.pause_button.config(state=tk.DISABLED)
                self.gui.start_button.config(state=tk.NORMAL, text="Start")
                
                if hasattr(self.gui, 'update_performance_stats'):
                    self.gui.update_performance_stats(self.performance_tracker.format_statistics())
                    
            print("Simulation completed: All items collected and delivered!")
            return

        if self.gui:
            self.gui.root.after(300, self.simulation_loop)
    
    def _on_progress_made(self):
        """Called when progress is made (item delivered)"""
        self.stall_detector.last_progress_at = self.stall_detector.loop_count
        
        self.performance_tracker.add_delivered_items()
    
    def _check_completion(self, remaining_items):
        """Check if all items have been collected and delivered"""
        if remaining_items:
            return False
            
        for robot in self.entity_manager.robots:
            if robot.carrying_items:
                return False
                
        return True