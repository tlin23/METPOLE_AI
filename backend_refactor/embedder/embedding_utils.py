import json
import chromadb
from pathlib import Path
from typing import List
from ..models.content_chunk import ContentChunk


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
            chunks = [ContentChunk(**chunk_data) for chunk_data in chunks_data]

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
