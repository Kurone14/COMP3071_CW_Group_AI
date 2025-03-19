import tkinter as tk
from typing import List, Dict, Tuple, Set, Any, Optional, Callable


class EntityDisplay:
    """
    Base class for entity displays (robots and items).
    Manages a scrollable list of entities with status information.
    """
    def __init__(self, parent):
        """
        Initialize the entity display
        
        Args:
            parent: Parent widget
        """
        self.main_frame = tk.Frame(parent)
        
        # Create display frame with scrollbar
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
        
        # Add mousewheel scrolling
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Action buttons
        self.actions_frame = tk.Frame(self.main_frame)
        self.actions_frame.pack(fill=tk.X, pady=5)
        
        self.edit_button = tk.Button(self.actions_frame, text=f"Edit", state=tk.DISABLED)
        self.edit_button.pack(side=tk.LEFT, padx=5)
        
        self.delete_button = tk.Button(self.actions_frame, text=f"Delete", state=tk.DISABLED)
        self.delete_button.pack(side=tk.LEFT, padx=5)
        
        # Entity tracking
        self.entity_frames = {}
        self.selected_id = None
        
        # Selection callback
        self.select_callback = None
    
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
        """
        Return the main frame for this display
        
        Returns:
            tk.Frame: The main frame
        """
        return self.main_frame
    
    def set_action_buttons(self, edit_callback: Callable, delete_callback: Callable):
        """
        Set the callbacks for action buttons
        
        Args:
            edit_callback: Function to call when edit button is clicked
            delete_callback: Function to call when delete button is clicked
        """
        self.edit_button.config(command=edit_callback)
        self.delete_button.config(command=delete_callback)
    
    def set_select_callback(self, callback: Callable):
        """
        Set the callback for entity selection
        
        Args:
            callback: Function to call when an entity is selected
        """
        self.select_callback = callback
    
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


class RobotDisplay(EntityDisplay):
    """Display for robot entities"""
    def __init__(self, parent):
        """
        Initialize the robot display
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.edit_button.config(text="Edit Robot")
        self.delete_button.config(text="Delete Robot")
    
    def setup_robot_frames(self, robots: List[Any], select_callback: Optional[Callable] = None):
        """
        Create frames for each robot
        
        Args:
            robots: List of robots
            select_callback: Optional callback for robot selection
        """
        # Set select callback if provided
        if select_callback:
            self.select_callback = select_callback
            
        # Clear existing frames
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.entity_frames = {}
        self.selected_id = None
        
        # Disable action buttons
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
        # Create a frame for each robot
        for robot in robots:
            frame = tk.Frame(self.scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Bind click event to select this robot
            frame.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Robot title with capacity
            title = tk.Label(frame, text=f"Robot {robot.id} (Cap: {robot.capacity}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Robot status
            status_var = tk.StringVar(value="Status: Idle")
            status = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status.pack(anchor=tk.W)
            status.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Robot items
            items_var = tk.StringVar(value="Items: None")
            items = tk.Label(frame, textvariable=items_var, font=("Arial", 9))
            items.pack(anchor=tk.W)
            items.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Robot steps
            steps_var = tk.StringVar(value="Steps: 0")
            steps = tk.Label(frame, textvariable=steps_var, font=("Arial", 9))
            steps.pack(anchor=tk.W)
            steps.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Robot location
            loc_var = tk.StringVar(value=f"Location: ({robot.x}, {robot.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, r_id=robot.id: self._on_robot_click(r_id))
            
            # Store references to frame and labels
            self.entity_frames[robot.id] = {
                'frame': frame,
                'status': status_var,
                'items': items_var,
                'steps': steps_var,
                'location': loc_var
            }
        
        # Reset scroll position
        self.canvas.yview_moveto(0)
    
    def _on_robot_click(self, robot_id: int):
        """
        Handle robot selection
        
        Args:
            robot_id: ID of the clicked robot
        """
        if self.select_callback:
            self.select_callback(robot_id)
    
    def select_robot(self, robot_id: int):
        """
        Highlight the selected robot
        
        Args:
            robot_id: ID of the robot to select
        """
        if robot_id in self.entity_frames:
            # Deselect previous selection
            if self.selected_id in self.entity_frames:
                self.entity_frames[self.selected_id]['frame'].config(bg=self.main_frame.cget('bg'))
            
            # Select new robot
            self.selected_id = robot_id
            self.entity_frames[robot_id]['frame'].config(bg='light blue')
            
            # Enable action buttons
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            
            # Ensure the selected robot is visible
            self._ensure_visible(self.entity_frames[robot_id]['frame'])
    
    def deselect_robot(self, robot_id: int):
        """
        Remove highlighting from the robot
        
        Args:
            robot_id: ID of the robot to deselect
        """
        if robot_id in self.entity_frames:
            self.entity_frames[robot_id]['frame'].config(bg=self.main_frame.cget('bg'))
            
            if self.selected_id == robot_id:
                self.selected_id = None
                self.edit_button.config(state=tk.DISABLED)
                self.delete_button.config(state=tk.DISABLED)
    
    def update_status(self, robots: List[Any]):
        """
        Update the status display for all robots
        
        Args:
            robots: List of robots
        """
        for robot in robots:
            if robot.id in self.entity_frames:
                # Update status text
                status_text = "Idle"
                if robot.path:
                    if robot.carrying_items:
                        status_text = "To Drop Point"
                    else:
                        status_text = "To Item"
                
                self.entity_frames[robot.id]['status'].set(f"Status: {status_text}")
                
                # Update items text
                if robot.carrying_items:
                    items_text = ", ".join([f"#{item.id}({item.weight}kg)" for item in robot.carrying_items])
                    self.entity_frames[robot.id]['items'].set(f"Items: {items_text}")
                else:
                    self.entity_frames[robot.id]['items'].set("Items: None")
                
                # Update steps and location
                self.entity_frames[robot.id]['steps'].set(f"Steps: {robot.steps}")
                self.entity_frames[robot.id]['location'].set(f"Location: ({robot.x}, {robot.y})")


class ItemDisplay(EntityDisplay):
    """Display for item entities"""
    def __init__(self, parent):
        """
        Initialize the item display
        
        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.edit_button.config(text="Edit Item")
        self.delete_button.config(text="Delete Item")
    
    def update_items_list(self, items: List[Any], select_callback: Optional[Callable] = None):
        """
        Update the item list display
        
        Args:
            items: List of items
            select_callback: Optional callback for item selection
        """
        # Set select callback if provided
        if select_callback:
            self.select_callback = select_callback
            
        # Clear existing frames
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.entity_frames = {}
        self.selected_id = None
        
        # Disable action buttons
        self.edit_button.config(state=tk.DISABLED)
        self.delete_button.config(state=tk.DISABLED)
        
        # Create a frame for each item
        for item in items:
            frame = tk.Frame(self.scrollable_frame, relief=tk.RIDGE, bd=2)
            frame.pack(fill=tk.X, pady=2, padx=5)
            
            # Bind click event to select this item
            frame.bind("<Button-1>", lambda e, i_id=item.id: self._on_item_click(i_id))
            
            # Determine item status
            status = "Picked" if item.picked else "Waiting"
            if item.assigned and not item.picked:
                status = "Assigned"
            
            # Item title with weight
            title = tk.Label(frame, text=f"Item {item.id} (Weight: {item.weight}kg)", font=("Arial", 10, "bold"))
            title.pack(anchor=tk.W)
            title.bind("<Button-1>", lambda e, i_id=item.id: self._on_item_click(i_id))
            
            # Item location
            loc_var = tk.StringVar(value=f"Location: ({item.x}, {item.y})")
            loc = tk.Label(frame, textvariable=loc_var, font=("Arial", 9))
            loc.pack(anchor=tk.W)
            loc.bind("<Button-1>", lambda e, i_id=item.id: self._on_item_click(i_id))
            
            # Item status
            status_var = tk.StringVar(value=f"Status: {status}")
            status_label = tk.Label(frame, textvariable=status_var, font=("Arial", 9))
            status_label.pack(anchor=tk.W)
            status_label.bind("<Button-1>", lambda e, i_id=item.id: self._on_item_click(i_id))
            
            # Store references to frame and labels
            self.entity_frames[item.id] = {
                'frame': frame,
                'location': loc_var,
                'status': status_var
            }
            
            # Set background color based on status
            if item.picked:
                frame.configure(bg='#D5F5E3')  # Light green
            elif item.assigned:
                frame.configure(bg='#FCF3CF')  # Light yellow
        
        # Reset scroll position
        self.canvas.yview_moveto(0)
    
    def _on_item_click(self, item_id: int):
        """
        Handle item selection
        
        Args:
            item_id: ID of the clicked item
        """
        if self.select_callback:
            self.select_callback(item_id)
    
    def select_item(self, item_id: int):
        """
        Highlight the selected item
        
        Args:
            item_id: ID of the item to select
        """
        if item_id in self.entity_frames:
            # Store original background color
            orig_bg = self.entity_frames[item_id]['frame'].cget('bg')
            
            # Deselect previous selection
            if self.selected_id in self.entity_frames:
                # If item is picked or assigned, restore appropriate color
                item_frame = self.entity_frames[self.selected_id]['frame']
                status_text = self.entity_frames[self.selected_id]['status'].get()
                
                if "Picked" in status_text:
                    item_frame.config(bg='#D5F5E3')  # Light green
                elif "Assigned" in status_text:
                    item_frame.config(bg='#FCF3CF')  # Light yellow
                else:
                    item_frame.config(bg=self.main_frame.cget('bg'))
            
            # Select new item
            self.selected_id = item_id
            self.entity_frames[item_id]['frame'].config(bg='light blue')
            
            # Enable action buttons
            self.edit_button.config(state=tk.NORMAL)
            self.delete_button.config(state=tk.NORMAL)
            
            # Ensure the selected item is visible
            self._ensure_visible(self.entity_frames[item_id]['frame'])
    
    def deselect_item(self, item_id: int):
        """
        Remove highlighting from the item
        
        Args:
            item_id: ID of the item to deselect
        """
        if item_id in self.entity_frames:
            # Restore appropriate background color based on status
            status_text = self.entity_frames[item_id]['status'].get()
            
            if "Picked" in status_text:
                self.entity_frames[item_id]['frame'].config(bg='#D5F5E3')  # Light green
            elif "Assigned" in status_text:
                self.entity_frames[item_id]['frame'].config(bg='#FCF3CF')  # Light yellow
            else:
                self.entity_frames[item_id]['frame'].config(bg=self.main_frame.cget('bg'))
            
            if self.selected_id == item_id:
                self.selected_id = None
                self.edit_button.config(state=tk.DISABLED)
                self.delete_button.config(state=tk.DISABLED)
    
    def update_status(self, items: List[Any]):
        """
        Update the status display for all items
        
        Args:
            items: List of items
        """
        for item in items:
            if item.id in self.entity_frames:
                # Update status text
                status = "Picked" if item.picked else "Waiting"
                if item.assigned and not item.picked:
                    status = "Assigned"
                
                self.entity_frames[item.id]['status'].set(f"Status: {status}")
                self.entity_frames[item.id]['location'].set(f"Location: ({item.x}, {item.y})")
                
                # Update background color based on status
                if item.picked:
                    self.entity_frames[item.id]['frame'].configure(bg='#D5F5E3')  # Light green
                elif item.assigned:
                    self.entity_frames[item.id]['frame'].configure(bg='#FCF3CF')  # Light yellow
                else:
                    # Only reset background if not selected
                    if self.selected_id != item.id:
                        self.entity_frames[item.id]['frame'].configure(bg=self.main_frame.cget('bg'))