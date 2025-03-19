import tkinter as tk
from tkinter import messagebox
from typing import Dict, Any, Optional


class DialogBase:
    """Base class for all dialog windows"""
    
    @staticmethod
    def create_dialog(parent, title: str, width: int = 300, height: int = 200):
        """
        Create a basic dialog window
        
        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width
            height: Dialog height
            
        Returns:
            tk.Toplevel: The dialog window
        """
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.geometry(f"{width}x{height}")
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()
        
        return dialog
    
    @staticmethod
    def create_button_frame(dialog):
        """
        Create a frame for dialog buttons
        
        Args:
            dialog: Dialog window
            
        Returns:
            tk.Frame: Button frame
        """
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        return btn_frame


class RobotEditDialog:
    """Dialog for editing robot properties"""
    
    @staticmethod
    def show_dialog(parent, robot) -> Dict[str, Any]:
        """
        Display dialog for editing a robot
        
        Args:
            parent: Parent window
            robot: Robot to edit
            
        Returns:
            Dict: Result with edited properties or {'cancelled': True}
        """
        dialog = DialogBase.create_dialog(parent, f"Edit Robot {robot.id}")
        
        # Title
        tk.Label(dialog, text=f"Edit Robot {robot.id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Position input
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
        
        # Capacity input
        cap_frame = tk.Frame(dialog)
        cap_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(cap_frame, text="Capacity (kg):").pack(side=tk.LEFT, padx=10)
        
        cap_var = tk.StringVar(value=str(robot.capacity))
        cap_entry = tk.Entry(cap_frame, textvariable=cap_var, width=6)
        cap_entry.pack(side=tk.LEFT, padx=2)
        
        # Button frame
        btn_frame = DialogBase.create_button_frame(dialog)
        
        # Result dictionary
        result = {"cancelled": True}
        
        # Save button handler
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
        
        # Cancel button handler
        def on_cancel():
            dialog.destroy()
        
        # Create buttons
        save_btn = tk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Wait for dialog to close
        parent.wait_window(dialog)
        
        return result


class ItemEditDialog:
    """Dialog for editing item properties"""
    
    @staticmethod
    def show_dialog(parent, item) -> Dict[str, Any]:
        """
        Display dialog for editing an item
        
        Args:
            parent: Parent window
            item: Item to edit
            
        Returns:
            Dict: Result with edited properties or {'cancelled': True}
        """
        dialog = DialogBase.create_dialog(parent, f"Edit Item {item.id}")
        
        # Title
        tk.Label(dialog, text=f"Edit Item {item.id}", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Position input
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
        
        # Weight input
        weight_frame = tk.Frame(dialog)
        weight_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(weight_frame, text="Weight (kg):").pack(side=tk.LEFT, padx=10)
        
        weight_var = tk.StringVar(value=str(item.weight))
        weight_entry = tk.Entry(weight_frame, textvariable=weight_var, width=6)
        weight_entry.pack(side=tk.LEFT, padx=2)
        
        # Button frame
        btn_frame = DialogBase.create_button_frame(dialog)
        
        # Result dictionary
        result = {"cancelled": True}
        
        # Save button handler
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
        
        # Cancel button handler
        def on_cancel():
            dialog.destroy()
        
        # Create buttons
        save_btn = tk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Wait for dialog to close
        parent.wait_window(dialog)
        
        return result


class GridSizeDialog:
    """Dialog for setting grid size"""
    
    @staticmethod
    def show_dialog(parent, current_width: int, current_height: int) -> Dict[str, Any]:
        """
        Display dialog for setting grid size
        
        Args:
            parent: Parent window
            current_width: Current grid width
            current_height: Current grid height
            
        Returns:
            Dict: Result with new dimensions or {'cancelled': True}
        """
        dialog = DialogBase.create_dialog(parent, "Set Grid Size")
        
        # Title
        tk.Label(dialog, text="Set Grid Size", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Width input
        width_frame = tk.Frame(dialog)
        width_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(width_frame, text="Width:").pack(side=tk.LEFT, padx=10)
        
        width_var = tk.StringVar(value=str(current_width))
        width_entry = tk.Entry(width_frame, textvariable=width_var, width=6)
        width_entry.pack(side=tk.LEFT, padx=2)
        
        # Height input
        height_frame = tk.Frame(dialog)
        height_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(height_frame, text="Height:").pack(side=tk.LEFT, padx=10)
        
        height_var = tk.StringVar(value=str(current_height))
        height_entry = tk.Entry(height_frame, textvariable=height_var, width=6)
        height_entry.pack(side=tk.LEFT, padx=2)
        
        # Button frame
        btn_frame = DialogBase.create_button_frame(dialog)
        
        # Result dictionary
        result = {"cancelled": True}
        
        # Save button handler
        def on_save():
            try:
                width = int(width_var.get())
                height = int(height_var.get())
                
                if width < 5 or height < 5:
                    messagebox.showerror("Invalid input", "Width and height must be at least 5")
                    return
                
                if width > 50 or height > 50:
                    messagebox.showerror("Invalid input", "Width and height must be at most 50")
                    return
                
                result["width"] = width
                result["height"] = height
                result["cancelled"] = False
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Invalid input", "Please enter valid numbers for all fields")
        
        # Cancel button handler
        def on_cancel():
            dialog.destroy()
        
        # Create buttons
        save_btn = tk.Button(btn_frame, text="Save", command=on_save)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        cancel_btn = tk.Button(btn_frame, text="Cancel", command=on_cancel)
        cancel_btn.pack(side=tk.RIGHT, padx=5)
        
        # Wait for dialog to close
        parent.wait_window(dialog)
        
        return result