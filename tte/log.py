"""
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
"""

import logging


def setup_logger(name, level=logging.INFO):
    """Set up and return a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handlers if they don't exist
    if not logger.handlers:
        # File handler
        file_handler = logging.FileHandler("app_log.log")
        file_handler.setLevel(level)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create formatters and add it to handlers
        log_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
