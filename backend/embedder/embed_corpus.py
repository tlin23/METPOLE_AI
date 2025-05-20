#!/usr/bin/env python3
"""
Script to load the metropole_corpus.json file, embed each chunk using all-MiniLM-L6-v2,
and store the text and metadata in Chroma.
"""

import json
import os
import time
import shutil
from typing import Dict, List, Any

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from backend.configer.logging_config import get_logger

# Get logger for this module
logger = get_logger("embedder.embed_corpus")


def cleanup_inactive_directories(
    chroma_db_path: str, active_collection_ids: List[str]
) -> None:
    """
    Clean up inactive collection directories.

    Args:
        chroma_db_path: Path to the ChromaDB directory
        active_collection_ids: List of active collection IDs
    """
    if not os.path.exists(chroma_db_path):
        return

    # Convert active IDs to strings for comparison
    active_ids = [str(id) for id in active_collection_ids]
    logger.info(f"Active collection IDs: {active_ids}")

    # Get all directories in the ChromaDB path
    for item in os.listdir(chroma_db_path):
        full_path = os.path.join(chroma_db_path, item)
        # Skip if not a directory or if it's the SQLite file
        if not os.path.isdir(full_path) or item == "chroma.sqlite3":
            continue

        # If directory is not in active IDs, remove it
        if item not in active_ids:
            logger.info(f"Found inactive collection directory: {item}")
            try:
                # Check if directory contains collection data
                has_data = all(
                    os.path.exists(os.path.join(full_path, f))
                    for f in ["data_level0.bin", "length.bin", "header.bin"]
                )
                if has_data:
                    logger.info(
                        f"Removing inactive collection directory with data: {item}"
                    )
                    shutil.rmtree(full_path)
                else:
                    logger.info(f"Removing empty collection directory: {item}")
                    shutil.rmtree(full_path)
            except Exception as e:
                logger.error(f"Error removing directory {item}: {e}")


def load_corpus(corpus_path: str) -> List[Dict[str, Any]]:
    """
    Load the corpus from a JSON file.

    Args:
        corpus_path (str): Path to the corpus file.

    Returns:
        List[Dict[str, Any]]: The loaded corpus.
    """
    logger.info(f"Loading corpus from {corpus_path}")
    try:
        with open(corpus_path, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        logger.info(f"Successfully loaded corpus with {len(corpus)} chunks")
        return corpus
    except Exception as e:
        logger.error(f"Error loading corpus: {e}")
        raise


def embed_corpus(
    corpus_path: str,
    chroma_db_path: str,
    collection_name: str,
    batch_size: int,
) -> None:
    """
    Embed the corpus using all-MiniLM-L6-v2 and store in Chroma.

    Args:
        collection_name (str): Name of the collection to store embeddings in.
        batch_size (int): Number of documents to embed in each batch.
        corpus_path (str): Path to the corpus file.
    """
    start_time = time.time()

    # Create the index directory if it doesn't exist
    logger.info(f"Ensuring Chroma DB path exists: {chroma_db_path}")
    os.makedirs(chroma_db_path, exist_ok=True)

    logger.info(f"Initializing Chroma DB at: {chroma_db_path}")

    # Initialize the embedding function
    # Note: DefaultEmbeddingFunction uses the 'all-MiniLM-L6-v2' model internally
    logger.info("Loading default embedding model (all-MiniLM-L6-v2)...")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    # Initialize the Chroma client
    client = chromadb.PersistentClient(
        path=chroma_db_path, settings=Settings(anonymized_telemetry=False)
    )

    # Get list of active collection IDs before any changes
    active_collections = client.list_collections()
    active_collection_ids = [col.id for col in active_collections]

    # Clean up the target collection if it exists
    if collection_name in [col.name for col in active_collections]:
        logger.info(f"Cleaning up existing collection '{collection_name}'")
        client.delete_collection(collection_name)
        logger.info(f"Deleted collection '{collection_name}'")

    # Create a fresh collection
    logger.info(f"Creating new collection '{collection_name}'")
    collection = client.create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"description": "Metropole corpus embeddings"},
    )

    # Clean up any inactive directories
    logger.info("Cleaning up inactive collection directories")
    cleanup_inactive_directories(chroma_db_path, active_collection_ids)

    # Load the corpus
    corpus = load_corpus(corpus_path)

    # Prepare data for embedding
    total_chunks = len(corpus)
    logger.info(f"Preparing to embed {total_chunks} chunks")

    # Process in batches
    total_batches = (total_chunks + batch_size - 1) // batch_size
    total_embedded = 0

    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch = corpus[start_idx:end_idx]

        # Extract data for this batch
        ids = [chunk["chunk_id"] for chunk in batch]
        documents = [
            (
                f"[Tags: {', '.join(chunk['tags'])}]\n{chunk['content']}"
                if chunk.get("tags")
                else chunk["content"]
            )
            for chunk in batch
        ]

        metadatas = []
        for chunk in batch:
            metadata = {
                "page_id": chunk["page_id"],
                "page_title": chunk["page_title"],
                "page_name": chunk["page_name"],
                "section_header": chunk["section_header"],
            }
            if "tags" in chunk and isinstance(chunk["tags"], list):
                metadata["tags"] = ",".join(chunk["tags"])
            metadatas.append(metadata)

        # Add to collection
        logger.info(
            f"Embedding batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)"
        )
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

        total_embedded += len(batch)
        logger.info(f"Progress: {total_embedded}/{total_chunks} chunks embedded")

    # Log completion
    elapsed_time = time.time() - start_time
    logger.info(
        f"Embedding complete! {total_embedded} chunks embedded in {elapsed_time:.2f} seconds"
    )
    logger.info(
        f"Collection '{collection_name}' now contains {collection.count()} documents"
    )
