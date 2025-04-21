"""
Utility helper functions for the application.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional


def get_timestamp() -> str:
    """
    Get current timestamp in ISO format.
    
    Returns:
        str: Current timestamp.
    """
    return datetime.now().isoformat()


def save_json(data: Dict[str, Any], filepath: str) -> bool:
    """
    Save data to a JSON file.
    
    Args:
        data (Dict[str, Any]): Data to save.
        filepath (str): Path to save the file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving JSON: {e}")
        return False


def load_json(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Load data from a JSON file.
    
    Args:
        filepath (str): Path to the JSON file.
        
    Returns:
        Optional[Dict[str, Any]]: Loaded data or None if error.
    """
    try:
        if not os.path.exists(filepath):
            return None
        
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text (str): Text to split.
        chunk_size (int, optional): Size of each chunk. Defaults to 1000.
        overlap (int, optional): Overlap between chunks. Defaults to 200.
        
    Returns:
        List[str]: List of text chunks.
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
    """
    Sanitize a filename by removing invalid characters.
    
    Args:
        filename (str): Filename to sanitize.
        
    Returns:
        str: Sanitized filename.
    """
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename
