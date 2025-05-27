"""
Centralized logging configuration for the backend_refactor application.

This module provides a standardized way to configure logging across the application.
It sets up a shared logger with consistent formatting and handlers.
"""

import os
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


# Feedback logging settings
LOGS_DIR = "backend_refactor/logs"

Path(LOGS_DIR).mkdir(parents=True, exist_ok=True)


# Configure the root logger
def configure_logging(
    logger_name="metropole_ai_refactor",
    log_level=logging.INFO,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file=None,
    max_bytes=10 * 1024 * 1024,  # 10 MB
    backup_count=5,
    stream_handler=True,
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

    return logger


# Create the default application logger
logger = configure_logging(
    logger_name="metropole_ai_refactor",
    log_level=logging.INFO,
    log_file=os.path.join(LOGS_DIR, "metropole_ai.log"),
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

    logger_name = f"metropole_ai_refactor.{name}"
    new_logger = logging.getLogger(logger_name)

    # If logger doesn't have handlers, configure it
    if not new_logger.handlers:
        configure_logging(
            logger_name=logger_name, log_file=os.path.join(LOGS_DIR, f"{name}.log")
        )
        # Note: Propagation is enabled by default. This means log messages will
        # propagate up the logger hierarchy. If you want to prevent duplicate logs,
        # you can set propagate=False on specific loggers where needed.
        new_logger.propagate = True

    return new_logger
