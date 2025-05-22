import chromadb
from typing import List
from ..models.content_chunk import ContentChunk


def embed_chunks(
    chunks: List[ContentChunk], collection_name: str, db_path: str
) -> None:
    """
    Convert chunks to text embeddings and store them in ChromaDB.

    Args:
        chunks: List of ContentChunk objects to embed
        collection_name: Name of the ChromaDB collection to store embeddings
        db_path: Path to the ChromaDB database

    Raises:
        ValueError: If chunks list is empty
        RuntimeError: If embedding or storage fails
    """
    if not chunks:
        raise ValueError("No chunks provided for embedding")

    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=db_path)

        # Create or get collection
        collection = client.get_or_create_collection(name=collection_name)

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
