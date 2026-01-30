"""
Logging configuration for TTE Tiered Orchestrator.

Provides consistent logging across all modules with both console and file output.
"""

import logging
import sys
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = 'tte', log_level: str = None, log_file: str = None) -> logging.Logger:
    """
    Configure and return logger instance.

    Args:
        name: Logger name (default: 'tte')
        log_level: Log level override (default: from config or INFO)
        log_file: Log file path override (default: from config or app_log.log)

    Returns:
        Configured logger instance.
    """
    # Import config here to avoid circular imports
    try:
        from config import Config
        level = log_level or Config.LOG_LEVEL
        file_path = log_file or Config.LOG_FILE
    except ImportError:
        level = log_level or 'INFO'
        file_path = log_file or 'app_log.log'

    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Console handler - shows INFO and above
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # File handler - shows DEBUG and above with rotation
    try:
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    except (IOError, OSError) as e:
        print(f"Warning: Could not create log file: {e}")

    logger.addHandler(console_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


# Create default logger instance
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """
    Get a child logger with the given name.

    Args:
        name: Logger name (will be prefixed with 'tte.')

    Returns:
        Logger instance.
    """
    return logging.getLogger(f'tte.{name}')
