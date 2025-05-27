"""
Configuration settings for the server application.

This module centralizes all environment variables and configuration settings used by the server.
"""

import os
from pathlib import Path
from typing import Optional
from ..data_processing.pipeline.directory_utils import (
    ALLOWED_EXTENSIONS,
    get_step_dir,
)

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data_processing" / "data"

# Environment-specific directories
DEV_DIR = DATA_DIR / "dev"
PROD_DIR = DATA_DIR / "prod"

# OpenAI API settings
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

# Collection name for ChromaDB
COLLECTION_NAME = "metropole"

# Supported file extensions for the pipeline
SUPPORTED_EXTENSIONS = ALLOWED_EXTENSIONS

# ChromaDB paths
CHROMA_DEV_PATH = get_step_dir(DATA_DIR, "embed", production=False)
CHROMA_PROD_PATH = get_step_dir(DATA_DIR, "embed", production=True)
