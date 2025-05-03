#!/usr/bin/env python3
"""
Script to load the metropole_corpus.json file, embed each chunk using all-MiniLM-L6-v2,
and store the text and metadata in Chroma.
"""

import sys
import json
import time
import shutil
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from backend.configer.config import CHROMA_DB_PATH
from backend.configer.logging_config import get_logger

# Get logger for this module
logger = get_logger("embedder.embed_corpus")


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


def assert_unique_chunk_ids(corpus: List[Dict[str, Any]]):
    ids = [chunk["chunk_id"] for chunk in corpus]
    dupes = [id for id, count in Counter(ids).items() if count > 1]
    if dupes:
        raise ValueError(f"Duplicate chunk_id(s) found: {dupes}")


def embed_corpus(
    corpus_path: str = "./backend/data/processed/metropole_corpus.json",
    chroma_path: str = CHROMA_DB_PATH,
    collection_name: str = "metropole_documents",
    batch_size: int = 100,
    clean_index: bool = True,
) -> None:
    """
    Embed the corpus using all-MiniLM-L6-v2 and store in Chroma.

    Args:
        corpus_path (str): Path to the corpus file.
        chroma_path (Optional[str]): Path to the Chroma DB. If None, uses the CHROMA_DB_PATH env var or default.
        collection_name (str): Name of the collection to store embeddings in.
        batch_size (int): Number of documents to embed in each batch.
        clean_index (bool): Whether to remove existing index files before embedding.
    """
    start_time = time.time()

    # Clean the index directory if requested
    chroma_path_obj = Path(chroma_path)
    if clean_index and chroma_path_obj.exists():
        logger.info(f"Removing existing index directory: {chroma_path}")
        shutil.rmtree(chroma_path)

    # Create the directory if it doesn't exist
    chroma_path_obj.mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing Chroma DB at: {chroma_path}")

    # Initialize the embedding function
    # Note: DefaultEmbeddingFunction uses the 'all-MiniLM-L6-v2' model internally
    logger.info("Loading default embedding model (all-MiniLM-L6-v2)...")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    # Initialize the Chroma client
    client = chromadb.PersistentClient(
        path=chroma_path, settings=Settings(anonymized_telemetry=False)
    )

    # Check if the collection already exists and has documents
    existing_collections = {col.name: col for col in client.list_collections()}
    if collection_name in existing_collections:
        collection = client.get_collection(collection_name)
        count = collection.count()
        if count > 0:
            logger.info(
                f"Deleting and recreating collection '{collection_name}' with {count} documents"
            )
            client.delete_collection(collection_name)
            collection = client.create_collection(
                name=collection_name,
                embedding_function=embedding_function,
                metadata={"description": "Metropole corpus embeddings"},
            )
        else:
            collection._embedding_function = embedding_function
    else:
        collection = client.create_collection(
            name=collection_name,
            embedding_function=embedding_function,
            metadata={"description": "Metropole corpus embeddings"},
        )

    # Load the corpus
    corpus = load_corpus(corpus_path)
    assert_unique_chunk_ids(corpus)

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
            f"[Tags: {', '.join(chunk['tags'])}]\n{chunk['content']}" for chunk in batch
        ]
        metadatas = [
            {
                "page_id": chunk["page_id"],
                "page_title": chunk["page_title"],
                "page_name": chunk["page_name"],
                "section_header": chunk["section_header"],
                "tags": (
                    ",".join(chunk["tags"])
                    if isinstance(chunk["tags"], list)
                    else chunk["tags"]
                ),
            }
            for chunk in batch
        ]

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


if __name__ == "__main__":
    embed_corpus(clean_index=True)  # Always clean the index when running directly
