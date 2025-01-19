'''
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
'''

import logging
import threading
import time
import os

def setup_logger(name, level=logging.INFO):
    """Set up and return a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create handlers if they don't exist
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler('app_log.log')
        file_handler.setLevel(level)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create formatters and add it to handlers
        log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(log_format)
        console_handler.setFormatter(log_format)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Define log levels
DEBUG = logging.DEBUG
INFO = logging.INFO
WARNING = logging.WARNING
ERROR = logging.ERROR
CRITICAL = logging.CRITICAL

def trim_file(file_path, max_lines=1000):
    """
    Trims a file to a maximum number of lines, keeping the most recent entries.
    Creates the file if it doesn't exist.
    """
    try:
        # Create file if it doesn't exist
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write('')
            return

        # Read existing lines
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if len(lines) > max_lines:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines[-max_lines:])
    except Exception as e:
        print(f"Error trimming file: {e}")

def continuous_trim(file_path, interval=300):
    """Continuously trims a file at specified intervals."""
    while True:
        trim_file(file_path)
        time.sleep(interval)

def start_continuous_trim(file_path, interval=300):
    """Starts the continuous trimming in a separate thread."""
    trim_thread = threading.Thread(target=continuous_trim, args=(file_path, interval), daemon=True)
    trim_thread.start()
    return trim_thread
