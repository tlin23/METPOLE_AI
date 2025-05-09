"""
Configuration settings for the application.

This module centralizes all environment variables used throughout the application.
"""

import os
from typing import Optional

# Chroma DB settings
CHROMA_DB_PATH: str = os.getenv("CHROMA_DB_PATH")

# OpenAI API settings
OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")

# Feedback logging settings
FEEDBACK_LOG_DIR: str = os.getenv("FEEDBACK_LOG_DIR", "backend/logs")
FEEDBACK_LOG_FILE: str = os.getenv("FEEDBACK_LOG_FILE", "feedback.jsonl")
FEEDBACK_LOG_MAX_SIZE_MB: int = int(os.getenv("FEEDBACK_LOG_MAX_SIZE_MB", "10"))
FEEDBACK_LOG_MAX_BACKUPS: int = int(os.getenv("FEEDBACK_LOG_MAX_BACKUPS", "5"))
