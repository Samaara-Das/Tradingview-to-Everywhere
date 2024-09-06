'''
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
'''

from logging import getLogger, FileHandler, StreamHandler, Formatter, DEBUG, INFO, WARNING, ERROR, CRITICAL
import sys
import threading
import time

def setup_logger(logger_name, logger_level=INFO, file='app_log.log'):
    '''This sets up a logger and returns it'''
    logger = getLogger(logger_name)
    logger.setLevel(logger_level)
    
    date_format = "%m.%d.%y %H:%M:%S"
    formatter = Formatter('%(name)s.py %(funcName)s() %(levelname)s: %(message)s %(asctime)s', datefmt=date_format)

    file_handler = FileHandler(file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Create a StreamHandler with utf-8 encoding for sys.stdout
    stream_handler = StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    return logger

def trim_file(file_path, max_lines=1000):
    """Trims a file to a maximum number of lines, keeping the most recent entries."""
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        if len(lines) > max_lines:
            with open(file_path, 'w') as file:
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
