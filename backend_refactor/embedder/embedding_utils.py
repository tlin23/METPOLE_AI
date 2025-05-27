import json
import chromadb
from pathlib import Path
from typing import List
from ..models.content_chunk import ContentChunk
from ..configer.logging_config import get_logger

logger = get_logger("embedder.utils")


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
    logger.info(
        f"Starting embedding process for {len(json_paths)} files into collection: {collection_name}"
    )

    if not json_paths:
        error_msg = "No JSON files provided for embedding"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Initialize ChromaDB client
        logger.debug(f"Initializing ChromaDB client at {db_path}")
        client = chromadb.PersistentClient(path=str(db_path))

        # Create or get collection
        collection = client.get_or_create_collection(name=collection_name)
        logger.info(f"Using collection: {collection_name}")

        # Process each JSON file
        total_chunks = 0
        for json_path in json_paths:
            logger.debug(f"Processing file: {json_path}")
            try:
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
                            logger.warning(
                                f"Failed to parse chunk data as JSON in {json_path}"
                            )
                            continue
                    chunks.append(ContentChunk(**chunk_data))

                if not chunks:
                    logger.warning(f"No valid chunks found in {json_path}")
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
                logger.debug(
                    f"Adding {len(chunks)} chunks from {json_path} to collection"
                )
                collection.add(ids=ids, documents=documents, metadatas=metadatas)
                total_chunks += len(chunks)

            except Exception as e:
                logger.error(f"Error processing {json_path}: {str(e)}")
                continue

        logger.info(
            f"Successfully embedded {total_chunks} chunks from {len(json_paths)} files"
        )

    except Exception as e:
        error_msg = f"Failed to embed chunks: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
