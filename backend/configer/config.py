"""
Configuration settings for the application.

This module centralizes all environment variables used throughout the application.
"""

import os
from typing import Optional

# OpenAI API settings
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

HTML_DIR = "backend/data/html"
INDEX_DIR = "backend/data/index"
PROCESSED_DIR = "backend/data/processed"
CHUNKS_JSON_PATH = os.path.join(PROCESSED_DIR, "chunks.json")
CORPUS_PATH = os.path.join(PROCESSED_DIR, "metropole_corpus.json")
COLLECTION_NAME = "metropole_documents"
BATCH_SIZE = 100
