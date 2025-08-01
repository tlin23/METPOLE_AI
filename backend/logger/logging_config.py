"""
Centralized logging configuration for the backend application.

This module provides a standardized way to configure logging across the application.
It sets up a shared logger with consistent formatting and handlers.
"""

import os
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Feedback logging settings
LOGS_DIR = "backend/logger/logs"

# Create logs directory if it doesn't exist
Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)


# Configure the root logger
def configure_logging(
    logger_name="metropole_ai",
    log_level=logging.INFO,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file=None,
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    stream_handler=True,
    propagate=True,
):
    """
    Configure a logger with the specified parameters.

    Args:
        logger_name (str): Name of the logger.
        log_level (int): Logging level (e.g., logging.INFO, logging.DEBUG).
        log_format (str): Format string for log messages.
        log_file (str, optional): Path to the log file. If None, no file handler is added.
        max_bytes (int): Maximum size of the log file before rotation.
        backup_count (int): Number of backup log files to keep.
        stream_handler (bool): Whether to add a stream handler (console output).
        propagate (bool): Whether to propagate logs to parent loggers.

    Returns:
        logging.Logger: The configured logger.
    """
    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Add stream handler (console output)
    if stream_handler:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log_file is specified
    if log_file:
        # Ensure the directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Set propagation
    logger.propagate = propagate

    return logger


# Create the default application logger
logger = configure_logging(
    logger_name="metropole_ai",
    log_level=logging.INFO,
    log_file=os.path.join(LOGS_DIR, "metropole_ai.log"),
    propagate=False,  # Disable propagation for root logger
)


def get_logger(name=None):
    """
    Get a logger with the specified name.

    Args:
        name (str, optional): Name of the logger. If None, returns the root logger.

    Returns:
        logging.Logger: The logger.
    """
    if name is None:
        return logger

    logger_name = f"metropole_ai.{name}"
    new_logger = logging.getLogger(logger_name)

    # If logger doesn't have handlers, configure it
    if not new_logger.handlers:
        # In test environment, enable propagation for caplog to work
        is_test = "pytest" in sys.modules
        new_logger.propagate = is_test  # Enable propagation in test environment

        # Always create the log directory
        Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)

        if not is_test:
            # Only add handlers if not in test environment
            configure_logging(
                logger_name=logger_name,
                log_file=os.path.join(LOGS_DIR, f"{name}.log"),
                propagate=False,
            )

    return new_logger
