#!/usr/bin/env python3
"""
Script to inspect the contents of the vector database collections.
"""

import chromadb
from chromadb.config import Settings
import json
from typing import Dict, Any

from backend.configer.config import (
    INDEX_DIR,
    WEB_COLLECTION_NAME,
    OFFLINE_COLLECTION_NAME,
)
from backend.configer.logging_config import get_logger

logger = get_logger("inspect_db")


def get_collection_stats(collection) -> Dict[str, Any]:
    """Get statistics about a collection."""
    count = collection.count()
    return {
        "total_documents": count,
        "collection_name": collection.name,
        "collection_id": str(collection.id),
    }


def main():
    # Initialize ChromaDB client
    client = chromadb.PersistentClient(
        path=INDEX_DIR, settings=Settings(anonymized_telemetry=False)
    )

    # Get both collections
    web_collection = client.get_collection(WEB_COLLECTION_NAME)
    offline_collection = client.get_collection(OFFLINE_COLLECTION_NAME)

    # Get and print stats for both collections
    print("\n=== Collections ===")
    web_stats = get_collection_stats(web_collection)
    print("\nWeb Collection:")
    print(json.dumps(web_stats, indent=2))

    print("\nOffline Collection:")
    offline_stats = get_collection_stats(offline_collection)
    print(json.dumps(offline_stats, indent=2))


if __name__ == "__main__":
    main()
