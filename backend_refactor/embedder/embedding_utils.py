import json
import logging
import chromadb
from pathlib import Path
from typing import List
from chromadb.config import Settings
from ..models.content_chunk import ContentChunk

logger = logging.getLogger(__name__)


def embed_chunks(json_paths: List[Path], collection_name: str, db_path: str) -> None:
    """
    Convert chunks from JSON files to text embeddings and store them in ChromaDB.

    Args:
        json_paths: List of paths to JSON files containing ContentChunk objects
        collection_name: Name of the ChromaDB collection to store embeddings
        db_path: Path to the ChromaDB database

    Raises:
        ValueError: If json_paths list is empty
        RuntimeError: If embedding or storage fails
    """
    if not json_paths:
        raise ValueError("No JSON files provided for embedding")

    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=str(db_path))

        # Create or get collection
        collection = client.get_or_create_collection(name=collection_name)

        # Process each JSON file
        for json_path in json_paths:
            with open(json_path, "r", encoding="utf-8") as f:
                chunks_data = json.load(f)

            # Convert JSON data back to ContentChunk objects
            chunks = []
            for chunk_data in chunks_data:
                if isinstance(chunk_data, str):
                    # If the data is a string, try to parse it as JSON
                    try:
                        chunk_data = json.loads(chunk_data)
                    except json.JSONDecodeError:
                        continue
                chunks.append(ContentChunk(**chunk_data))

            if not chunks:
                continue

            # Prepare data for embedding
            ids = [chunk.chunk_id for chunk in chunks]
            documents = [chunk.text_content for chunk in chunks]
            metadatas = [
                {
                    "file_name": chunk.file_name,
                    "file_ext": chunk.file_ext,
                    "page_number": chunk.page_number,
                    "document_title": chunk.document_title,
                }
                for chunk in chunks
            ]

            # Add documents to collection
            collection.add(ids=ids, documents=documents, metadatas=metadatas)

    except Exception as e:
        raise RuntimeError(f"Failed to embed chunks: {str(e)}")


def combine_collections(
    source_collections: List[str],
    target_collection: str,
    output_dir: Path,
    production: bool = False,
) -> int:
    """
    Combine multiple collections into a single target collection.

    Args:
        source_collections: List of source collection names to combine
        target_collection: Name of the target collection to create
        output_dir: Base directory for the ChromaDB database
        production: Whether to use production environment

    Returns:
        Number of collections combined
    """
    # Initialize ChromaDB client
    db_path = output_dir / ("prod" if production else "dev") / "chroma"
    client = chromadb.PersistentClient(
        path=str(db_path),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
        ),
    )

    # Create target collection
    target_coll = client.get_or_create_collection(name=target_collection)

    # Combine each source collection
    for source_coll_name in source_collections:
        try:
            source_coll = client.get_collection(name=source_coll_name)

            # Get all documents from source collection
            results = source_coll.get()

            if results and results["ids"]:
                # Add documents to target collection
                target_coll.add(
                    ids=results["ids"],
                    documents=results["documents"],
                    metadatas=results["metadatas"],
                    embeddings=results["embeddings"],
                )
                logger.info(
                    f"Added {len(results['ids'])} documents from {source_coll_name}"
                )

        except Exception as e:
            logger.error(f"Error combining collection {source_coll_name}: {str(e)}")
            continue

    return len(source_collections)
