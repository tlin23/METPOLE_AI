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

# Offline Content Pipeline settings
OFFLINE_DOCS_DIR = "backend/data/offline_docs"
OFFLINE_CHUNKS_JSON_PATH = os.path.join(PROCESSED_DIR, "offline_docs_chunks.json")
OFFLINE_CORPUS_PATH = os.path.join(PROCESSED_DIR, "offline_docs_corpus.json")
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".dotx", ".doc", ".msg"}
DOC_TEXT_DIR = "backend/data/doc_text"

# Collection names for different content types
WEB_COLLECTION_NAME = "metropole_web_documents"
OFFLINE_COLLECTION_NAME = "metropole_offline_documents"

BATCH_SIZE = 100
