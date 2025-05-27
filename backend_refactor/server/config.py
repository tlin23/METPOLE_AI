"""
Configuration settings for the server application.

This module centralizes all environment variables and configuration settings used by the server.
"""

import os
from pathlib import Path
from typing import Optional
from ..data_processing.pipeline.directory_utils import (
    PIPELINE_STEPS,
    ALLOWED_EXTENSIONS,
    get_base_dir,
    initialize_directories,
)

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

# Environment-specific directories
DEV_DIR = DATA_DIR / "dev"
PROD_DIR = DATA_DIR / "prod"

# OpenAI API settings
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

# Collection name for ChromaDB
COLLECTION_NAME = "metropole"

# Supported file extensions for the pipeline
SUPPORTED_EXTENSIONS = ALLOWED_EXTENSIONS


# Pipeline paths helper
def get_pipeline_paths(env: str = "dev") -> dict:
    """Get pipeline paths for the specified environment ('dev' or 'prod')."""
    base_dir = get_base_dir(DATA_DIR, env == "prod")
    return {
        step_name: base_dir / dir_name for step_name, dir_name in PIPELINE_STEPS.items()
    }


# Initialize pipeline directories
initialize_directories(DATA_DIR)
