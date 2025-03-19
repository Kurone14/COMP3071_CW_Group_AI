"""
Logging utility for the warehouse robot system.
Provides consistent logging across all modules.
"""

import logging
import sys
import os
from datetime import datetime


class Logger:
    """
    Centralized logging system for the warehouse robot simulation.
    Supports console and file logging with different log levels.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern"""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the logger if not already initialized"""
        if self._initialized:
            return
            
        # Create logger
        self.logger = logging.getLogger('warehouse_robot_system')
        self.logger.setLevel(logging.INFO)
        
        # Create formatters
        console_format = logging.Formatter('%(levelname)s: %(message)s')
        file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_format)
        console_handler.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        
        # File handler (optional)
        self.file_handler = None
        
        self._initialized = True
        self.debug_enabled = False
        
        # Component loggers
        self.component_loggers = {}
    
    def enable_file_logging(self, log_dir='logs'):
        """
        Enable logging to file
        
        Args:
            log_dir: Directory to store log files
        """
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_path = os.path.join(log_dir, f'simulation_{timestamp}.log')
        
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        file_handler.setLevel(logging.DEBUG)
        
        self.logger.addHandler(file_handler)
        self.file_handler = file_handler
        
        self.info(f"File logging enabled: {log_path}")
    
    def set_level(self, level):
        """
        Set the logging level
        
        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger.setLevel(level)
        self.debug_enabled = level <= logging.DEBUG
        self.info(f"Log level set to {logging.getLevelName(level)}")
    
    def enable_debug(self):
        """Enable debug logging"""
        self.set_level(logging.DEBUG)
    
    def get_component_logger(self, component_name):
        """
        Get a logger for a specific component
        
        Args:
            component_name: Name of the component
            
        Returns:
            ComponentLogger: Logger for the component
        """
        if component_name not in self.component_loggers:
            self.component_loggers[component_name] = ComponentLogger(self, component_name)
        return self.component_loggers[component_name]
    
    def debug(self, message):
        """Log a debug message"""
        self.logger.debug(message)
    
    def info(self, message):
        """Log an info message"""
        self.logger.info(message)
    
    def warning(self, message):
        """Log a warning message"""
        self.logger.warning(message)
    
    def error(self, message):
        """Log an error message"""
        self.logger.error(message)
    
    def critical(self, message):
        """Log a critical message"""
        self.logger.critical(message)


class ComponentLogger:
    """Logger for a specific component"""
    
    def __init__(self, main_logger, component_name):
        """
        Initialize a component logger
        
        Args:
            main_logger: Main logger instance
            component_name: Name of the component
        """
        self.main_logger = main_logger
        self.component_name = component_name
    
    def debug(self, message):
        """Log a debug message for this component"""
        self.main_logger.debug(f"[{self.component_name}] {message}")
    
    def info(self, message):
        """Log an info message for this component"""
        self.main_logger.info(f"[{self.component_name}] {message}")
    
    def warning(self, message):
        """Log a warning message for this component"""
        self.main_logger.warning(f"[{self.component_name}] {message}")
    
    def error(self, message):
        """Log an error message for this component"""
        self.main_logger.error(f"[{self.component_name}] {message}")
    
    def critical(self, message):
        """Log a critical message for this component"""
        self.main_logger.critical(f"[{self.component_name}] {message}")


# Create a global logger instance
logger = Logger()

# Function to get the global logger
def get_logger():
    """Get the global logger instance"""
    return logger

# Function to get a component logger
def get_component_logger(component_name):
    """
    Get a logger for a specific component
    
    Args:
        component_name: Name of the component
        
    Returns:
        ComponentLogger: Logger for the component
    """
    return logger.get_component_logger(component_name)