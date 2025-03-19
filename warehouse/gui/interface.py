import tkinter as tk
from tkinter import simpledialog, messagebox, ttk

class WarehouseGUI:
    def __init__(self, width, height, master=None):
        self.root = tk.Tk() if master is None else master
        self.root.title("Autonomous Robot Warehouse Simulation")
        
        self.main_container = tk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.left_panel = tk.Frame(self.main_container)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.canvas_frame = tk.Frame(self.left_panel)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, width=width*30, height=height*30, bg="white")
        self.canvas.pack()
        
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
        
        self.add_robot_button = tk.Button(self.entity_controls, text="Add Robot", state=tk.DISABLED)
        self.add_robot_button.pack(side=tk.LEFT, padx=5)
        
        self.add_item_button = tk.Button(self.entity_controls, text="Add Item", state=tk.DISABLED)
        self.add_item_button.pack(side=tk.LEFT, padx=5)
        
        self.right_panel = tk.Frame(self.main_container, width=350)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.right_panel.pack_propagate(False)
        
        self.status_frame = tk.Frame(self.right_panel)
        self.status_frame.pack(fill=tk.BOTH, expand=True)
        
        self.status_label = tk.Label(self.status_frame, text="Warehouse Status", font=("Arial", 14, "bold"))
        self.status_label.pack(pady=(0, 10))
        
        self.items_left_var = tk.StringVar(value="Items left: 0")
        self.items_left_label = tk.Label(self.status_frame, textvariable=self.items_left_var, font=("Arial", 12))
        self.items_left_label.pack(pady=5)
        
        self.notebook = ttk.Notebook(self.status_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.robot_tab = tk.Frame(self.notebook)
        self.notebook.add(self.robot_tab, text="Robots")
        
        self.robot_display_frame = tk.Frame(self.robot_tab)
        self.robot_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.robot_canvas = tk.Canvas(self.robot_display_frame)
        self.robot_scrollbar = tk.Scrollbar(self.robot_display_frame, orient="vertical", command=self.robot_canvas.yview)
        self.robot_scrollable_frame = tk.Frame(self.robot_canvas)
        
        self.robot_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.robot_canvas.configure(scrollregion=self.robot_canvas.bbox("all"))
        )
        
        self.robot_canvas.create_window((0, 0), window=self.robot_scrollable_frame, anchor="nw")
        self.robot_canvas.configure(yscrollcommand=self.robot_scrollbar.set)
        
        self.robot_canvas.pack(side="left", fill="both", expand=True)
        self.robot_scrollbar.pack(side="right", fill="y")
        
        self.robot_actions_frame = tk.Frame(self.robot_tab)
        self.robot_actions_frame.pack(fill=tk.X, pady=5)
        
        self.edit_robot_button = tk.Button(self.robot_actions_frame, text="Edit Robot", state=tk.DISABLED)
        self.edit_robot_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_robot_button = tk.Button(self.robot_actions_frame, text="Delete Robot", state=tk.DISABLED)
        self.delete_robot_button.pack(side=tk.LEFT, padx=5)
        
        self.item_tab = tk.Frame(self.notebook)
        self.notebook.add(self.item_tab, text="Items")
        
        self.item_display_frame = tk.Frame(self.item_tab)
        self.item_display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.item_canvas = tk.Canvas(self.item_display_frame)
        self.item_scrollbar = tk.Scrollbar(self.item_display_frame, orient="vertical", command=self.item_canvas.yview)
        self.item_scrollable_frame = tk.Frame(self.item_canvas)
        
        self.item_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.item_canvas.configure(scrollregion=self.item_canvas.bbox("all"))
        )
        
        self.item_canvas.create_window((0, 0), window=self.item_scrollable_frame, anchor="nw")
        self.item_canvas.configure(yscrollcommand=self.item_scrollbar.set)
        
        self.item_canvas.pack(side="left", fill="both", expand=True)
        self.item_scrollbar.pack(side="right", fill="y")
        
        self.item_actions_frame = tk.Frame(self.item_tab)
        self.item_actions_frame.pack(fill=tk.X, pady=5)
        
        self.edit_item_button = tk.Button(self.item_actions_frame, text="Edit Item", state=tk.DISABLED)
        self.edit_item_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_item_button = tk.Button(self.item_actions_frame, text="Delete Item", state=tk.DISABLED)
        self.delete_item_button.pack(side=tk.LEFT, padx=5)
        
        self.cell_size = 30
        self.width = width
        self.height = height
        
        self.canvas.bind("<Button-1>", self.canvas_click)
        self.add_entity_mode = None  
        
        self.selected_robot_id = None
        self.selected_item_id = None
        
        self.robot_frames = {}
        self.item_frames = {}
    
    def canvas_click(self, event):
        """Handle clicks on the canvas for adding entities"""
        if self.add_entity_mode:
            x = event.x // self.cell_size
            y = event.y // self.cell_size
            
            if self.add_entity_mode == "robot" and self.add_robot_callback:
                self.add_robot_callback(x, y)
                self.exit_add_mode()
            elif self.add_entity_mode == "item" and self.add_item_callback:
                weight = simpledialog.askinteger("Item Weight", "Enter item weight (kg):", 
                                                minvalue=1, maxvalue=10)
                if weight:
                    self.add_item_callback(x, y, weight)
                    self.exit_add_mode()
    
    def enter_add_robot_mode(self):
        """Enter mode for adding a robot"""
        self.add_entity_mode = "robot"
        self.add_robot_button.config(relief=tk.SUNKEN)
        self.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Robot", "Click on the grid to place a new robot")
    
    def enter_add_item_mode(self):
        """Enter mode for adding an item"""
        self.add_entity_mode = "item"
        self.add_item_button.config(relief=tk.SUNKEN)
        self.canvas.config(cursor="hand2")
        messagebox.showinfo("Add Item", "Click on the grid to place a new item")
    
    def exit_add_mode(self):
        """Exit add entity mode"""
        self.add_entity_mode = None
        self.add_robot_button.config(relief=tk.RAISED)
        self.add_item_button.config(relief=tk.RAISED)
        self.canvas.config(cursor="")
    
    def setup_robot_status_displays(self, robots):
        """Create status displays for robots"""
        for widget in self.robot_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.robot_frames = {}
        self.selected_robot_id = None
        
        self.edit_robot_button.config(state=tk.DISABLED)
        self.delete_robot_button.config(state=tk.DISABLED)
        
        for robot in robots:
            frame = tk.Frame(self.robot_scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            frame.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            title = tk.Label(frame, text=f"Robot {robot.id} (Cap: {robot.capacity}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            status_var = tk.StringVar(value="Status: Idle")
            status = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status.pack(anchor=tk.W)
            status.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            items_var = tk.StringVar(value="Items: None")
            items = tk.Label(frame, textvariable=items_var, font=("Arial", 9))
            items.pack(anchor=tk.W)
            items.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            steps_var = tk.StringVar(value="Steps: 0")
            steps = tk.Label(frame, textvariable=steps_var, font=("Arial", 9))
            steps.pack(anchor=tk.W)
            steps.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            loc_var = tk.StringVar(value=f"Location: ({robot.x}, {robot.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, r_id=robot.id: self.select_robot(r_id))
            
            self.robot_frames[robot.id] = {
                'frame': frame,
                'status': status_var,
                'items': items_var,
                'steps': steps_var,
                'location': loc_var
            }
    
    def select_robot(self, robot_id):
        """Handle selection of a robot"""
        if self.selected_robot_id in self.robot_frames:
            self.robot_frames[self.selected_robot_id]['frame'].config(bg=self.root.cget('bg'))
        
        self.selected_robot_id = robot_id
        self.robot_frames[robot_id]['frame'].config(bg='light blue')
        
        self.edit_robot_button.config(state=tk.NORMAL)
        self.delete_robot_button.config(state=tk.NORMAL)
    
    def select_item(self, item_id):
        """Handle selection of an item"""
        if self.selected_item_id in self.item_frames:
            self.item_frames[self.selected_item_id]['frame'].config(bg=self.root.cget('bg'))
        
        self.selected_item_id = item_id
        self.item_frames[item_id]['frame'].config(bg='light blue')
        
        self.edit_item_button.config(state=tk.NORMAL)
        self.delete_item_button.config(state=tk.NORMAL)
    
    def update_items_list(self, items):
        """Update the item list in the Items tab"""
        for widget in self.item_scrollable_frame.winfo_children():
            widget.destroy()
        
        self.item_frames = {}
        self.selected_item_id = None
        
        self.edit_item_button.config(state=tk.DISABLED)
        self.delete_item_button.config(state=tk.DISABLED)
        
        for item in items:
            frame = tk.Frame(self.item_scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            frame.bind("<Button-1>", lambda e, i_id=item.id: self.select_item(i_id))
            
            status = "Picked" if item.picked else "Waiting"
            if item.assigned and not item.picked:
                status = "Assigned"
            
            title = tk.Label(frame, text=f"Item {item.id} (Weight: {item.weight}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, i_id=item.id: self.select_item(i_id))
            
            loc_var = tk.StringVar(value=f"Location: ({item.x}, {item.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, i_id=item.id: self.select_item(i_id))
            
            status_var = tk.StringVar(value=f"Status: {status}")
            status_label = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status_label.pack(anchor=tk.W)
            status_label.bind("<Button-1>", lambda e, i_id=item.id: self.select_item(i_id))
            
            self.item_frames[item.id] = {
                'frame': frame,
                'location': loc_var,
                'status': status_var
            }
            
            if item.picked:
                frame.configure(bg='#D5F5E3')  
            elif item.assigned:
                frame.configure(bg='#FCF3CF')  
    
    def update_status(self, robots, items):
        """Update the status displays"""
        try:
            for robot in robots:
                if robot.id in self.robot_frames:
                    status_text = "Idle"
                    if robot.path:
                        if robot.carrying_items:
                            status_text = "To Drop Point"
                        else:
                            status_text = "To Item"
                    
                    self.robot_frames[robot.id]['status'].set(f"Status: {status_text}")
                    
                    if robot.carrying_items:
                        items_text = ", ".join([f"#{item.id}({item.weight}kg)" for item in robot.carrying_items])
                        self.robot_frames[robot.id]['items'].set(f"Items: {items_text}")
                    else:
                        self.robot_frames[robot.id]['items'].set("Items: None")
                    
                    self.robot_frames[robot.id]['steps'].set(f"Steps: {robot.steps}")
                    self.robot_frames[robot.id]['location'].set(f"Location: ({robot.x}, {robot.y})")
            
            for item in items:
                if item.id in self.item_frames:
                    status = "Picked" if item.picked else "Waiting"
                    if item.assigned and not item.picked:
                        status = "Assigned"
                    
                    self.item_frames[item.id]['status'].set(f"Status: {status}")
                    self.item_frames[item.id]['location'].set(f"Location: ({item.x}, {item.y})")
                    
                    if item.picked:
                        self.item_frames[item.id]['frame'].configure(bg='#D5F5E3') 
                    elif item.assigned:
                        self.item_frames[item.id]['frame'].configure(bg='#FCF3CF')  
                    else:
                        if self.selected_item_id != item.id:
                            self.item_frames[item.id]['frame'].configure(bg=self.root.cget('bg'))
            
            items_left = sum(1 for item in items if not item.picked)
            self.items_left_var.set(f"Items left: {items_left}")
            
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def draw_environment(self, grid, width, height, drop_point, robots, items):
        """Draw the simulation environment on the canvas"""
        self.canvas.delete("all")
        cell_size = self.cell_size
        
        for x in range(0, width+1):
            self.canvas.create_line(x*cell_size, 0, x*cell_size, height*cell_size, fill="#DDDDDD")
        for y in range(0, height+1):
            self.canvas.create_line(0, y*cell_size, width*cell_size, y*cell_size, fill="#DDDDDD")
        
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 1:  
                    self.canvas.create_rectangle(x*cell_size, y*cell_size, 
                                               (x+1)*cell_size, (y+1)*cell_size, 
                                               fill="gray", outline="black")
        
        if drop_point:
            x, y = drop_point
            self.canvas.create_rectangle(x*cell_size, y*cell_size, 
                                       (x+1)*cell_size, (y+1)*cell_size, 
                                       fill="green", outline="black")
            self.canvas.create_text(x*cell_size + cell_size//2, y*cell_size + cell_size//2, 
                                  text="DROP", fill="white", font=("Arial", 8, "bold"))
        
        for item in items:
            if not item.picked:
                extra_highlight = 0
                fill_color = "blue"
                
                if self.selected_item_id == item.id:
                    extra_highlight = -2
                    fill_color = "dark blue"
                
                self.canvas.create_rectangle(
                    item.x*cell_size + 5 + extra_highlight, 
                    item.y*cell_size + 5 + extra_highlight, 
                    (item.x+1)*cell_size - 5 - extra_highlight, 
                    (item.y+1)*cell_size - 5 - extra_highlight, 
                    fill=fill_color, outline="black"
                )
                self.canvas.create_text(
                    item.x*cell_size + cell_size//2, 
                    item.y*cell_size + cell_size//2, 
                    text=f"{item.weight}kg", 
                    fill="white", 
                    font=("Arial", 8, "bold")
                )
        
        for robot in robots:
            extra_highlight = 0
            fill_color = "red"
            
            if self.selected_robot_id == robot.id:
                extra_highlight = -2
                fill_color = "dark red"
            
            self.canvas.create_oval(
                robot.x*cell_size + 2 + extra_highlight, 
                robot.y*cell_size + 2 + extra_highlight, 
                (robot.x+1)*cell_size - 2 - extra_highlight, 
                (robot.y+1)*cell_size - 2 - extra_highlight, 
                fill=fill_color, outline="black"
            )
            self.canvas.create_text(
                robot.x*cell_size + cell_size//2, 
                robot.y*cell_size + cell_size//2, 
                text=f"R{robot.id}", 
                fill="white", 
                font=("Arial", 8, "bold")
            )
    
    def set_button_commands(self, start_cmd, pause_cmd, reset_cmd, add_robot_cmd, add_item_cmd, 
                           edit_robot_cmd, delete_robot_cmd, edit_item_cmd, delete_item_cmd):
        """Set the commands for all buttons"""
        self.start_button.config(command=start_cmd)
        self.pause_button.config(command=pause_cmd)
        self.reset_button.config(command=reset_cmd)
        
        self.add_robot_button.config(command=self.enter_add_robot_mode)
        self.add_item_button.config(command=self.enter_add_item_mode)
        
        self.edit_robot_button.config(command=lambda: edit_robot_cmd(self.selected_robot_id))
        self.delete_robot_button.config(command=lambda: delete_robot_cmd(self.selected_robot_id))
        self.edit_item_button.config(command=lambda: edit_item_cmd(self.selected_item_id))
        self.delete_item_button.config(command=lambda: delete_item_cmd(self.selected_item_id))
        
        self.add_robot_callback = add_robot_cmd
        self.add_item_callback = add_item_cmd
    
    def show_edit_robot_dialog(self, robot):
        """Display dialog for editing a robot"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Robot {robot.id}")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Edit Robot {robot.id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        pos_frame = tk.Frame(dialog)
        pos_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(pos_frame, text="Position (x, y):").pack(side=tk.LEFT, padx=10)
        
        x_var = tk.StringVar(value=str(robot.x))
        y_var = tk.StringVar(value=str(robot.y))
        
        x_entry = tk.Entry(pos_frame, textvariable=x_var, width=4)
        x_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Label(pos_frame, text=",").pack(side=tk.LEFT)
        
        y_entry = tk.Entry(pos_frame, textvariable=y_var, width=4)
        y_entry.pack(side=tk.LEFT, padx=2)
        
        cap_frame = tk.Frame(dialog)
        cap_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cap_frame, text="Capacity (kg):").pack(side=tk.LEFT, padx=10)
        
        cap_var = tk.StringVar(value=str(robot.capacity))
        cap_entry = tk.Entry(cap_frame, textvariable=cap_var, width=6)
        cap_entry.pack(side=tk.LEFT, padx=2)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        result = {"cancelled": True}
        
        def on_save():
            try:
                x = int(x_var.get())
                y = int(y_var.get())
                capacity = int(cap_var.get())
                
                if capacity <= 0:
                    messagebox.showerror("Invalid input", "Capacity must be greater than 0")
                    return
                
                result["x"] = x
                result["y"] = y
                result["capacity"] = capacity
                result["cancelled"] = False
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid input", "Please enter valid numbers for all fields")
        
        def on_cancel():
            dialog.destroy()
        
        save_btn = tk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        self.root.wait_window(dialog)
        
        return result
    
    def show_edit_item_dialog(self, item):
        """Display dialog for editing an item"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Edit Item {item.id}")
        dialog.geometry("300x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text=f"Edit Item {item.id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        pos_frame = tk.Frame(dialog)
        pos_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(pos_frame, text="Position (x, y):").pack(side=tk.LEFT, padx=10)
        
        x_var = tk.StringVar(value=str(item.x))
        y_var = tk.StringVar(value=str(item.y))
        
        x_entry = tk.Entry(pos_frame, textvariable=x_var, width=4)
        x_entry.pack(side=tk.LEFT, padx=2)
        
        tk.Label(pos_frame, text=",").pack(side=tk.LEFT)
        
        y_entry = tk.Entry(pos_frame, textvariable=y_var, width=4)
        y_entry.pack(side=tk.LEFT, padx=2)
        
        weight_frame = tk.Frame(dialog)
        weight_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(weight_frame, text="Weight (kg):").pack(side=tk.LEFT, padx=10)
        
        weight_var = tk.StringVar(value=str(item.weight))
        weight_entry = tk.Entry(weight_frame, textvariable=weight_var, width=6)
        weight_entry.pack(side=tk.LEFT, padx=2)
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        
        result = {"cancelled": True}
        
        def on_save():
            try:
                x = int(x_var.get())
                y = int(y_var.get())
                weight = int(weight_var.get())
                
                if weight <= 0:
                    messagebox.showerror("Invalid input", "Weight must be greater than 0")
                    return
                
                result["x"] = x
                result["y"] = y
                result["weight"] = weight
                result["cancelled"] = False
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid input", "Please enter valid numbers for all fields")
        
        def on_cancel():
            dialog.destroy()
        
        save_btn = tk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        self.root.wait_window(dialog)
        
        return result
    
    def enable_entity_controls(self, enable=True):
        """Enable or disable entity control buttons"""
        state = tk.NORMAL if enable else tk.DISABLED
        self.add_robot_button.config(state=state)
        self.add_item_button.config(state=state)
    
    def run(self):
        """Run the Tkinter main loop"""
        self.root.mainloop()