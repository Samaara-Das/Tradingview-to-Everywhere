"""
This is for setting up a logger for the application. Any file can use this to create its own logger.
This was done to avoid repetition of code.
"""

import logging
import os
from pathlib import Path


def setup_logger(name, level=logging.INFO):
    """Set up and return a logger instance."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create handlers if they don't exist
    if not logger.handlers:
        # File handler — writes under LOG_DIR (default "logs/"). The Docker compose
        # mounts /app/logs to a host volume so the file persists across restarts.
        log_dir = Path(os.getenv("LOG_DIR", "logs"))
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / "app_log.log"
        file_handler = logging.FileHandler(str(log_path))
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
