import tkinter as tk
from tkinter import ttk
from gui.canvas_view import CanvasView
from gui.entity_display import RobotDisplay, ItemDisplay
from tkinter import simpledialog, messagebox

class WarehouseGUI:
    def __init__(self, width, height, master=None):
        self.root = tk.Tk() if master is None else master
        self.root.title("Autonomous Robot Warehouse Simulation")
        
        self.root.menu = tk.Menu(self.root)
        self.root.config(menu=self.root.menu)
        
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.left_panel = tk.Frame(self.main_container)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_view = CanvasView(self.left_panel, width, height)
        
        self.create_control_buttons()
        
        self.right_panel = tk.Frame(self.main_container, width=350)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.right_panel.pack_propagate(False)
        
        self.create_status_panel()
        
        self.width = width
        self.height = height
        
        self.selected_robot_id = None
        self.selected_item_id = None
        
        self.add_entity_mode = None 
        
        self.add_robot_callback = None
        self.add_item_callback = None
        self.set_drop_point_callback = None
        self.toggle_obstacle_callback = None
        self.resize_grid_callback = None
        self.add_roadblock_callback = None
        
        self.create_environment_menu()
    
    def create_environment_menu(self):
        """Create environment control menu"""
        env_menu = tk.Menu(self.root.menu, tearoff=0)
        self.root.menu.add_cascade(label="Environment", menu=env_menu)
        
        env_menu.add_command(label="Set Grid Size", command=self.show_grid_size_dialog)
        env_menu.add_command(label="Set Drop Point", command=self.enter_set_drop_point_mode)
        env_menu.add_command(label="Toggle Obstacle Mode", command=self.enter_obstacle_mode)
    
    def create_control_buttons(self):
        """Create control buttons for the simulation"""
        self.control_frame = tk.Frame(self.left_panel)
        self.control_frame.pack(pady=10, fill=tk.X)
        
        self.simulation_controls = tk.Frame(self.control_frame)
        self.simulation_controls.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.start_button = tk.Button(self.simulation_controls, text="Start")
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = tk.Button(self.simulation_controls, text="Pause", state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.reset_button = tk.Button(self.simulation_controls, text="Reset")
        self.reset_button.pack(side=tk.LEFT, padx=5)
        
        self.entity_controls = tk.Frame(self.control_frame)
        self.entity_controls.pack(side=tk.RIGHT)
        
        self.add_robot_button = tk.Button(self.entity_controls, text="Add Robot")
        self.add_robot_button.pack(side=tk.LEFT, padx=5)
        
        self.add_item_button = tk.Button(self.entity_controls, text="Add Item")
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        
        self.roadblock_button = tk.Button(self.entity_controls, text="Add Roadblocks")
        self.roadblock_button.pack(side=tk.LEFT, padx=5)
    
    def create_status_panel(self):
        """Create the status panel with tabs for robots and items"""
        self.status_frame = tk.Frame(self.right_panel)
        self.status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = tk.Label(self.status_frame, text="Warehouse Status", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=(0, 10))
        
        self.performance_frame = tk.LabelFrame(self.status_frame, text="Performance")
        self.performance_frame.pack(fill=tk.X, pady=5)
        
        self.performance_labels = []
        for i in range(5):  
            label = tk.Label(self.performance_frame, text="-", anchor="w")
            label.pack(fill=tk.X, padx=5, pady=2)
            self.performance_labels.append(label)
        
        self.items_left_var = tk.StringVar(value="Items left: 0")
        self.items_left_label = tk.Label(self.status_frame, textvariable=self.items_left_var, font=("Arial", 12))
        self.items_left_label.pack(pady=5)
        
        self.notebook = ttk.Notebook(self.status_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.robot_display = RobotDisplay(self.notebook)
        self.item_display = ItemDisplay(self.notebook)
        
        self.notebook.add(self.robot_display.get_frame(), text="Robots")
        self.notebook.add(self.item_display.get_frame(), text="Items")
    
    def update_performance_stats(self, stats_list):
        """Update the performance statistics display"""
        for i, stat in enumerate(stats_list):
            if i < len(self.performance_labels):
                self.performance_labels[i].config(text=stat)
    
    def setup_robot_status_displays(self, robots):
        """Delegate to robot display component"""
        self.robot_display.setup_robot_frames(robots, self.select_robot)
    
    def update_items_list(self, items):
        """Delegate to item display component"""
        self.item_display.update_items_list(items, self.select_item)
    
    def select_robot(self, robot_id):
        """Handle selection of a robot"""
        if self.selected_robot_id:
            self.robot_display.deselect_robot(self.selected_robot_id)
        
        self.selected_robot_id = robot_id
        self.robot_display.select_robot(robot_id)
        
        self.canvas_view.set_selected_robot(robot_id)
    
    def select_item(self, item_id):
        """Handle selection of an item"""
        if self.selected_item_id:
            self.item_display.deselect_item(self.selected_item_id)
        
        self.selected_item_id = item_id
        self.item_display.select_item(item_id)
        
        self.canvas_view.set_selected_item(item_id)
    
    def update_status(self, robots, items):
        """Update the status displays for robots and items"""
        try:
            self.robot_display.update_status(robots)
            
            self.item_display.update_status(items)
            
            items_left = sum(1 for item in items if not item.picked)
            self.items_left_var.set(f"Items left: {items_left}")
            
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def draw_environment(self, grid, width, height, drop_point, robots, items, obstacle_manager=None):
        """Delegate to canvas view component"""
        self.canvas_view.draw_environment(
            grid, width, height, drop_point, robots, items,
            self.selected_robot_id, self.selected_item_id, obstacle_manager
        )
    
    def set_button_commands(self, start_cmd, pause_cmd, reset_cmd, add_robot_cmd, add_item_cmd, 
                           edit_robot_cmd, delete_robot_cmd, edit_item_cmd, delete_item_cmd,
                           set_drop_point_cmd=None, toggle_obstacle_cmd=None, resize_grid_cmd=None,
                           add_roadblock_cmd=None):
        """Set the commands for all buttons"""
        self.start_button.config(command=start_cmd)
        self.pause_button.config(command=pause_cmd)
        self.reset_button.config(command=reset_cmd)
        
        self.add_robot_button.config(command=self.enter_add_robot_mode)
        self.add_item_button.config(command=self.enter_add_item_mode)
        self.roadblock_button.config(command=self.enter_roadblock_mode)
        
        self.add_robot_callback = add_robot_cmd
        self.add_item_callback = add_item_cmd
        self.set_drop_point_callback = set_drop_point_cmd
        self.toggle_obstacle_callback = toggle_obstacle_cmd
        self.resize_grid_callback = resize_grid_cmd
        self.add_roadblock_callback = add_roadblock_cmd
        
        self.robot_display.set_action_buttons(
            lambda: edit_robot_cmd(self.selected_robot_id),
            lambda: delete_robot_cmd(self.selected_robot_id)
        )
        
        self.item_display.set_action_buttons(
            lambda: edit_item_cmd(self.selected_item_id),
            lambda: delete_item_cmd(self.selected_item_id)
        )
        
        self.canvas_view.set_click_handler(self.canvas_click)
    
    def canvas_click(self, event):
        """Handle clicks on the canvas for adding entities"""
        if self.add_entity_mode:
            x = event.x // self.canvas_view.cell_size
            y = event.y // self.canvas_view.cell_size
            
            if self.add_entity_mode == "robot" and self.add_robot_callback:
                self.add_robot_callback(x, y)
                self.exit_add_mode()
            elif self.add_entity_mode == "item" and self.add_item_callback:
                weight = simpledialog.askinteger("Item Weight", "Enter item weight (kg):", 
                                                minvalue=1, maxvalue=10)
                if weight:
                    self.add_item_callback(x, y, weight)
                    self.exit_add_mode()
            elif self.add_entity_mode == "drop_point" and self.set_drop_point_callback:
                self.set_drop_point_callback(x, y)
                self.exit_add_mode()
            elif self.add_entity_mode == "obstacle" and self.toggle_obstacle_callback:
                self.toggle_obstacle_callback(x, y)
            elif self.add_entity_mode == "roadblock" and self.add_roadblock_callback:
                self.add_roadblock_callback(x, y)
    
    def enter_add_robot_mode(self):
        """Enter mode for adding a robot"""
        self.add_entity_mode = "robot"
        self.add_robot_button.config(relief=tk.SUNKEN)
        self.canvas_view.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Robot", "Click on the grid to place a new robot")
    
    def enter_add_item_mode(self):
        """Enter mode for adding an item"""
        self.add_entity_mode = "item"
        self.add_item_button.config(relief=tk.SUNKEN)
        self.canvas_view.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Item", "Click on the grid to place a new item")
    
    def enter_set_drop_point_mode(self):
        """Enter mode for setting drop point"""
        self.add_entity_mode = "drop_point"
        self.canvas_view.canvas.config(cursor="crosshair")
        messagebox.showinfo("Set Drop Point", "Click on the grid to place the drop point")
    
    def enter_obstacle_mode(self):
        """Enter mode for toggling obstacles"""
        self.add_entity_mode = "obstacle"
        self.canvas_view.canvas.config(cursor="plus")
        messagebox.showinfo("Toggle Obstacles", "Click on the grid to add or remove obstacles. Press ESC when done.")
        self.root.bind("<Escape>", lambda e: self.exit_add_mode())
    
    def enter_roadblock_mode(self):
        """Enter mode for adding roadblocks during simulation"""
        self.add_entity_mode = "roadblock"
        self.roadblock_button.config(relief=tk.SUNKEN)
        self.canvas_view.canvas.config(cursor="crosshair")
        messagebox.showinfo("Add Roadblocks", "Click on the grid to place roadblocks. Press ESC when done.")
        self.root.bind("<Escape>", lambda e: self.exit_add_mode())
    
    def show_grid_size_dialog(self):
        """Show dialog for setting grid size"""
        from gui.entity_dialogs import GridSizeDialog
        result = GridSizeDialog.show_dialog(self.root, self.width, self.height)
        if not result["cancelled"] and self.resize_grid_callback:
            self.resize_grid_callback(result["width"], result["height"])
    
    def exit_add_mode(self):
        """Exit add entity mode"""
        self.add_entity_mode = None
        self.add_robot_button.config(relief=tk.RAISED)
        self.add_item_button.config(relief=tk.RAISED)
        self.roadblock_button.config(relief=tk.RAISED)
        self.canvas_view.canvas.config(cursor="")
        self.root.unbind("<Escape>")
    
    def enable_entity_controls(self, enable=True):
        """Enable or disable entity control buttons"""
        state = tk.NORMAL if enable else tk.DISABLED
        self.add_robot_button.config(state=state)
        self.add_item_button.config(state=state)
        if enable:
            self.roadblock_button.config(state=tk.DISABLED)
        else:
            self.roadblock_button.config(state=tk.NORMAL)
    
    def run(self):
        """Run the Tkinter main loop"""
        self.root.mainloop()