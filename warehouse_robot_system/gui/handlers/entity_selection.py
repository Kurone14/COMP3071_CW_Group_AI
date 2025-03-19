"""
Entity selection handler component for the warehouse robot simulation GUI.
Manages robot and item selection actions.
"""


class SelectionHandler:
    """Handles robot and item selection events"""
    
    def __init__(self, app):
        """
        Initialize the selection handler
        
        Args:
            app: The main application instance
        """
        self.app = app
    
    def on_robot_selected(self, robot_id: int) -> None:
        """
        Handle robot selection
        
        Args:
            robot_id: ID of the selected robot
        """
        # Deselect previous robot if any
        if self.app.selected_robot_id:
            self.app.status_panel.robot_display.deselect_robot(self.app.selected_robot_id)
        
        # Update the selected robot
        self.app.selected_robot_id = robot_id
        self.app.status_panel.robot_display.select_robot(robot_id)
        
        # Update canvas view
        self.app.canvas_view.set_selected_robot(robot_id)
    
    def on_item_selected(self, item_id: int) -> None:
        """
        Handle item selection
        
        Args:
            item_id: ID of the selected item
        """
        # Deselect previous item if any
        if self.app.selected_item_id:
            self.app.status_panel.item_display.deselect_item(self.app.selected_item_id)
        
        # Update the selected item
        self.app.selected_item_id = item_id
        self.app.status_panel.item_display.select_item(item_id)
        
        # Update canvas view
        self.app.canvas_view.set_selected_item(item_id)