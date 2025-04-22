"""Utility helper functions for the application.

This module provides common utility functions used throughout the application
for file operations, text processing, logging, and data handling.
"""

import os
import json
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional

from app.logging_config import get_logger

# Get logger for this module
logger = get_logger("utils.helpers")


def get_timestamp() -> str:
    """Get current timestamp in ISO format.

    Returns:
        Current timestamp as an ISO-formatted string.
    """
    return datetime.now().isoformat()


def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """Save data to a JSON file.

    Creates any necessary directories and writes the data as formatted JSON.

    Args:
        data: Dictionary data to save.
        filepath: Path to save the file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")
        return False


def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """Load data from a JSON file.

    Args:
        filepath: Path to the JSON file.

    Returns:
        Loaded data dictionary or None if file doesn't exist or an error occurs.
    """
    try:
        if not os.path.exists(filepath):
            return None

        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return None


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks.

    Divides text into chunks of specified size with overlap between
    adjacent chunks to maintain context.

    Args:
        text: Text to split.
        chunk_size: Size of each chunk in characters. Defaults to 1000.
        overlap: Overlap between chunks in characters. Defaults to 200.

    Returns:
        List of text chunks.
    """
    if not text:
        return []

    # Simple chunking by characters
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start = end - overlap if end < len(text) else len(text)

    return chunks


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing invalid characters.

    Replaces characters that are invalid in filenames with underscores
    and limits the length to 255 characters.

    Args:
        filename: Filename to sanitize.

    Returns:
        Sanitized filename safe for file system operations.
    """
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, "_")

    # Limit length
    if len(filename) > 255:
        filename = filename[:255]

    return filename


def append_to_jsonl(data: Dict[str, Any], filepath: str) -> bool:
    """Append a JSON object as a new line to a JSONL file.

    Creates any necessary directories and handles non-serializable objects
    by converting them to strings.

    Args:
        data: Dictionary data to append.
        filepath: Path to the JSONL file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Ensure data is properly serializable
        # Convert any non-serializable objects to strings
        serializable_data = {}
        for key, value in data.items():
            try:
                # Test if the value is JSON serializable
                json.dumps({key: value})
                serializable_data[key] = value
            except (TypeError, OverflowError):
                # If not serializable, convert to string
                serializable_data[key] = str(value)

        # Append to file
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(serializable_data, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        logger.error(f"Error appending to JSONL: {e}")
        return False


def should_rotate_log(filepath: str, max_size_mb: int = 10) -> bool:
    """Check if a log file should be rotated based on its size.

    Args:
        filepath: Path to the log file.
        max_size_mb: Maximum size in megabytes. Defaults to 10.

    Returns:
        True if the file should be rotated, False otherwise.
    """
    if not os.path.exists(filepath):
        return False

    # Get file size in bytes
    file_size = os.path.getsize(filepath)

    # Convert max_size_mb to bytes
    max_size_bytes = max_size_mb * 1024 * 1024

    return file_size >= max_size_bytes


def rotate_log_file(filepath: str, max_backups: int = 5) -> bool:
    """Rotate a log file by renaming it and creating a new empty file.

    Implements log rotation by shifting existing backup files and creating
    a new empty log file. Removes the oldest backup if maximum number is reached.

    Args:
        filepath: Path to the log file.
        max_backups: Maximum number of backup files to keep. Defaults to 5.

    Returns:
        True if successful, False otherwise.
    """
    try:
        if not os.path.exists(filepath):
            return True

        # Get the directory and filename
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)

        # Remove oldest backup if we've reached max_backups
        oldest_backup = os.path.join(directory, f"{name}.{max_backups}{ext}")
        if os.path.exists(oldest_backup):
            os.remove(oldest_backup)

        # Shift existing backups
        for i in range(max_backups - 1, 0, -1):
            backup_file = os.path.join(directory, f"{name}.{i}{ext}")
            new_backup_file = os.path.join(directory, f"{name}.{i+1}{ext}")
            if os.path.exists(backup_file):
                shutil.move(backup_file, new_backup_file)

        # Rename current log file to .1
        first_backup = os.path.join(directory, f"{name}.1{ext}")
        shutil.move(filepath, first_backup)

        # Create a new empty log file
        with open(filepath, "w", encoding="utf-8"):
            # Using with statement without variable to create empty file
            pass

        return True
    except Exception as e:
        logger.error(f"Error rotating log file: {e}")
        return False


def save_feedback_log(
    feedback_data: Dict[str, Any],
    log_dir: str = "data/logs",
    filename: str = "feedback.jsonl",
    max_size_mb: int = 10,
    max_backups: int = 5,
) -> bool:
    """Save feedback data to a JSONL log file with rotation support.

    Adds a timestamp to the feedback data and appends it to a JSONL file.
    Automatically rotates log files when they reach the specified size.

    Args:
        feedback_data: Feedback data to log.
        log_dir: Directory for log files. Defaults to "data/logs".
        filename: Log filename. Defaults to "feedback.jsonl".
        max_size_mb: Maximum log file size in MB. Defaults to 10.
        max_backups: Maximum number of backup files. Defaults to 5.

    Returns:
        True if successful, False otherwise.
    """
    try:
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)

        # Full path to log file
        log_path = os.path.join(log_dir, filename)

        # Check if we need to rotate the log file
        if should_rotate_log(log_path, max_size_mb):
            rotate_log_file(log_path, max_backups)

        # Create a copy of the feedback data to avoid modifying the original
        log_data = feedback_data.copy()

        # Always add a timestamp (overwrite if already present)
        log_data["timestamp"] = get_timestamp()

        # Append to log file
        return append_to_jsonl(log_data, log_path)
    except Exception as e:
        logger.error(f"Error saving feedback log: {e}")
        return False
