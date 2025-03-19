import tkinter as tk

class EntityDisplay:
    """Base class for entity displays (robots and items)"""
    def __init__(self, parent):
        self.main_frame = tk.Frame(parent)
        
        self.display_frame = tk.Frame(self.main_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.display_frame, height=200)
        self.scrollbar = tk.Scrollbar(self.display_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.bind(
            "<Configure>",
            self._on_canvas_configure
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=self.canvas.winfo_width())
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        self.actions_frame = tk.Frame(self.main_frame)
        self.actions_frame.pack(fill=tk.X, pady=5)
        
        self.edit_button = tk.Button(self.actions_frame, text=f"Edit", state=tk.DISABLED)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = tk.Button(self.actions_frame, text=f"Delete", state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        self.entity_frames = {}
        self.selected_id = None
    
    def _on_canvas_configure(self, event):
        """Update canvas window width when canvas is resized"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
    
    def _on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        x, y = event.x_root, event.y_root
        canvas_x = self.canvas.winfo_rootx()
        canvas_y = self.canvas.winfo_rooty()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if (canvas_x <= x <= canvas_x + canvas_width and
            canvas_y <= y <= canvas_y + canvas_height):
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def get_frame(self):
        """Return the main frame for this display"""
        return self.main_frame
    
    def set_action_buttons(self, edit_callback, delete_callback):
        """Set the callbacks for action buttons"""
        self.edit_button.config(command=edit_callback)
        self.delete_button.config(command=delete_callback)


class RobotDisplay(EntityDisplay):
    """Display for robot entities"""
    def __init__(self, parent):
        super().__init__(parent)
        self.edit_button.config(text="Edit Robot")
        self.delete_button.config(text="Delete Robot")
    
    def setup_robot_frames(self, robots, select_callback):
        """Create frames for each robot"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.entity_frames = {}
        self.selected_id = None
        
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
        for robot in robots:
            frame = tk.Frame(self.scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            frame.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            title = tk.Label(frame, text=f"Robot {robot.id} (Cap: {robot.capacity}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            status_var = tk.StringVar(value="Status: Idle")
            status = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status.pack(anchor=tk.W)
            status.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            items_var = tk.StringVar(value="Items: None")
            items = tk.Label(frame, textvariable=items_var, font=("Arial", 9))
            items.pack(anchor=tk.W)
            items.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            steps_var = tk.StringVar(value="Steps: 0")
            steps = tk.Label(frame, textvariable=steps_var, font=("Arial", 9))
            steps.pack(anchor=tk.W)
            steps.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            loc_var = tk.StringVar(value=f"Location: ({robot.x}, {robot.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, r_id=robot.id: select_callback(r_id))
            
            self.entity_frames[robot.id] = {
                'frame': frame,
                'status': status_var,
                'items': items_var,
                'steps': steps_var,
                'location': loc_var
            }
        
        self.canvas.yview_moveto(0)
    
    def select_robot(self, robot_id):
        """Highlight the selected robot"""
        if robot_id in self.entity_frames:
            self.selected_id = robot_id
            self.entity_frames[robot_id]['frame'].config(bg='light blue')
            
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            
            self._ensure_visible(self.entity_frames[robot_id]['frame'])
    
    def deselect_robot(self, robot_id):
        """Remove highlighting from the robot"""
        if robot_id in self.entity_frames:
            self.entity_frames[robot_id]['frame'].config(bg=self.main_frame.cget('bg'))
    
    def update_status(self, robots):
        """Update the status display for all robots"""
        for robot in robots:
            if robot.id in self.entity_frames:
                status_text = "Idle"
                if robot.path:
                    if robot.carrying_items:
                        status_text = "To Drop Point"
                    else:
                        status_text = "To Item"
                
                self.entity_frames[robot.id]['status'].set(f"Status: {status_text}")
                
                if robot.carrying_items:
                    items_text = ", ".join([f"#{item.id}({item.weight}kg)" for item in robot.carrying_items])
                    self.entity_frames[robot.id]['items'].set(f"Items: {items_text}")
                else:
                    self.entity_frames[robot.id]['items'].set("Items: None")
                
                self.entity_frames[robot.id]['steps'].set(f"Steps: {robot.steps}")
                self.entity_frames[robot.id]['location'].set(f"Location: ({robot.x}, {robot.y})")
    
    def _ensure_visible(self, widget):
        """Ensure the widget is visible in the scrollable area"""
        bbox = self.canvas.bbox(self.canvas_window)
        if not bbox:
            return
            
        widget_y = widget.winfo_y()
        
        canvas_top = self.canvas.canvasy(0)
        canvas_height = self.canvas.winfo_height()
        canvas_bottom = canvas_top + canvas_height
        
        if widget_y < canvas_top:
            self.canvas.yview_moveto(float(widget_y) / bbox[3])
        elif widget_y + widget.winfo_height() > canvas_bottom:
            self.canvas.yview_moveto(float(widget_y + widget.winfo_height() - canvas_height) / bbox[3])


class ItemDisplay(EntityDisplay):
    """Display for item entities"""
    def __init__(self, parent):
        super().__init__(parent)
        self.edit_button.config(text="Edit Item")
        self.delete_button.config(text="Delete Item")
    
    def update_items_list(self, items, select_callback):
        """Update the item list display"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.entity_frames = {}
        self.selected_id = None
        
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
        for item in items:
            frame = tk.Frame(self.scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            frame.bind("<Button-1>", lambda e, i_id=item.id: select_callback(i_id))
            
            status = "Picked" if item.picked else "Waiting"
            if item.assigned and not item.picked:
                status = "Assigned"
            
            title = tk.Label(frame, text=f"Item {item.id} (Weight: {item.weight}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, i_id=item.id: select_callback(i_id))
            
            loc_var = tk.StringVar(value=f"Location: ({item.x}, {item.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, i_id=item.id: select_callback(i_id))
            
            status_var = tk.StringVar(value=f"Status: {status}")
            status_label = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status_label.pack(anchor=tk.W)
            status_label.bind("<Button-1>", lambda e, i_id=item.id: select_callback(i_id))
            
            self.entity_frames[item.id] = {
                'frame': frame,
                'location': loc_var,
                'status': status_var
            }
            
            if item.picked:
                frame.configure(bg='#D5F5E3')  
            elif item.assigned:
                frame.configure(bg='#FCF3CF')  
        
        self.canvas.yview_moveto(0)
    
    def select_item(self, item_id):
        """Highlight the selected item"""
        if item_id in self.entity_frames:
            self.selected_id = item_id
            self.entity_frames[item_id]['frame'].config(bg='light blue')
            
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            
            self._ensure_visible(self.entity_frames[item_id]['frame'])
    
    def deselect_item(self, item_id):
        """Remove highlighting from the item"""
        if item_id in self.entity_frames:
            self.entity_frames[item_id]['frame'].config(bg=self.main_frame.cget('bg'))
    
    def update_status(self, items):
        """Update the status display for all items"""
        for item in items:
            if item.id in self.entity_frames:
                status = "Picked" if item.picked else "Waiting"
                if item.assigned and not item.picked:
                    status = "Assigned"
                
                self.entity_frames[item.id]['status'].set(f"Status: {status}")
                self.entity_frames[item.id]['location'].set(f"Location: ({item.x}, {item.y})")
                
                if item.picked:
                    self.entity_frames[item.id]['frame'].configure(bg='#D5F5E3')  
                elif item.assigned:
                    self.entity_frames[item.id]['frame'].configure(bg='#FCF3CF')  
                else:
                    if self.selected_id != item.id:
                        self.entity_frames[item.id]['frame'].configure(bg=self.main_frame.cget('bg'))
    
    def _ensure_visible(self, widget):
        """Ensure the widget is visible in the scrollable area"""
        bbox = self.canvas.bbox(self.canvas_window)
        if not bbox:
            return
            
        widget_y = widget.winfo_y()
        
        canvas_top = self.canvas.canvasy(0)
        canvas_height = self.canvas.winfo_height()
        canvas_bottom = canvas_top + canvas_height
        
        if widget_y < canvas_top:
            self.canvas.yview_moveto(float(widget_y) / bbox[3])
        elif widget_y + widget.winfo_height() > canvas_bottom:
            self.canvas.yview_moveto(float(widget_y + widget.winfo_height() - canvas_height) / bbox[3])