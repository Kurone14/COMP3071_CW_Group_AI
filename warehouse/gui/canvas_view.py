import tkinter as tk

class CanvasView:
    def __init__(self, parent, width, height):
        self.width = width
        self.height = height
        self.cell_size = 30
        
        self.canvas_frame = tk.Frame(parent)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        self.canvas = tk.Canvas(self.canvas_frame, width=width*self.cell_size, height=height*self.cell_size, bg="white")
        self.canvas.pack()
        
        self.selected_robot_id = None
        self.selected_item_id = None
        
        self.click_handler = None
    
    def set_click_handler(self, handler):
        """Set the handler for canvas clicks"""
        self.canvas.bind("<Button-1>", handler)
    
    def set_selected_robot(self, robot_id):
        """Set the currently selected robot"""
        self.selected_robot_id = robot_id
    
    def set_selected_item(self, item_id):
        """Set the currently selected item"""
        self.selected_item_id = item_id
    
    def draw_environment(self, grid, width, height, drop_point, robots, items, selected_robot_id=None, selected_item_id=None, obstacle_manager=None):
        """Draw the simulation environment on the canvas with different obstacle types"""
        self.selected_robot_id = selected_robot_id
        self.selected_item_id = selected_item_id
        
        self.canvas.delete("all")
        cell_size = self.cell_size
        
        # Draw grid lines
        for x in range(0, width+1):
            self.canvas.create_line(x*cell_size, 0, x*cell_size, height*cell_size, fill="#DDDDDD")
        for y in range(0, height+1):
            self.canvas.create_line(0, y*cell_size, width*cell_size, y*cell_size, fill="#DDDDDD")
        
        # Draw obstacles with different visualizations based on type
        for y in range(height):
            for x in range(width):
                if grid[y][x] == 1:  # Permanent obstacle
                    self.canvas.create_rectangle(x*cell_size, y*cell_size, 
                                            (x+1)*cell_size, (y+1)*cell_size, 
                                            fill="gray", outline="black")
                elif grid[y][x] == 5 and obstacle_manager:  # Temporary obstacle
                    self.canvas.create_rectangle(x*cell_size, y*cell_size, 
                                            (x+1)*cell_size, (y+1)*cell_size, 
                                            fill="#FFA500", outline="black")  # Orange
                    
                    # Add lifespan indicator
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan > 0:
                        self.canvas.create_text(
                            x*cell_size + cell_size//2, 
                            y*cell_size + cell_size//2, 
                            text=str(lifespan), 
                            fill="white", 
                            font=("Arial", 8, "bold")
                        )
                elif grid[y][x] == 6 and obstacle_manager:  # Semi-permanent obstacle
                    self.canvas.create_rectangle(x*cell_size, y*cell_size, 
                                            (x+1)*cell_size, (y+1)*cell_size, 
                                            fill="#8B4513", outline="black")  # Brown
                    
                    # Add lifespan indicator
                    lifespan = obstacle_manager.get_obstacle_remaining_lifespan(x, y)
                    if lifespan > 0:
                        self.canvas.create_text(
                            x*cell_size + cell_size//2, 
                            y*cell_size + cell_size//2, 
                            text=str(lifespan), 
                            fill="white", 
                            font=("Arial", 8, "bold")
                        )
        
        # Draw drop point
        if drop_point:
            x, y = drop_point
            self.canvas.create_rectangle(
                x*cell_size, y*cell_size, 
                (x+1)*cell_size, (y+1)*cell_size, 
                fill="green", outline="black"
            )
            self.canvas.create_text(
                x*cell_size + cell_size//2, 
                y*cell_size + cell_size//2, 
                text="DROP", fill="white", 
                font=("Arial", 8, "bold")
            )
        
        # Draw items
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
        
        # Draw robots
        for robot in robots:
            extra_highlight = 0
            fill_color = "red"
            
            if self.selected_robot_id == robot.id:
                extra_highlight = -2
                fill_color = "dark red"
            
            # Draw robot
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
            
            # Draw waiting indicator for robots waiting for temporary obstacles
            if hasattr(robot, 'waiting') and robot.waiting:
                self.canvas.create_text(
                    robot.x*cell_size + cell_size//2,
                    robot.y*cell_size + cell_size//4,
                    text="WAIT",
                    fill="yellow",
                    font=("Arial", 6, "bold")
                )