"""Embedder module for converting text to vector embeddings."""

from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path
from datetime import datetime
import uuid
from typing import Dict, List, Optional, Tuple, Union, Any

from app.config import CHROMA_DB_PATH
from app.logging_config import get_logger

# Get logger for this module
logger = get_logger("embedder.embed")

# Load environment variables
load_dotenv()


class Embedder:
    """Class for handling text embeddings and storage in ChromaDB.

    This class provides methods to convert text into vector embeddings
    and store them in a ChromaDB vector database for later retrieval.
    """

    def __init__(self, model_name: str = "default") -> None:
        """Initialize the embedder with ChromaDB connection.

        Args:
            model_name: Name of the embedding model to use. Defaults to "default".
        """
        self.model_name = model_name

        # Get the path for the Chroma database
        self.chroma_db_path = CHROMA_DB_PATH

        # Create the directory if it doesn't exist
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)

        # Initialize the persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path, settings=Settings(anonymized_telemetry=False)
        )

        # Initialize the collection
        self.collection = self.chroma_client.get_or_create_collection("documents")

    def embed_text(
        self,
        text: str,
        doc_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Convert text to embeddings and store in ChromaDB.

        Embeds the provided text and stores it in the ChromaDB collection
        with the given document ID and metadata.

        Args:
            text: Text to embed.
            doc_id: Document ID. If None, a UUID will be generated.
            metadata: Metadata for the document. If None, default metadata will be created.

        Returns:
            Document ID of the embedded text.
        """
        if doc_id is None:
            # Generate a simple ID if none provided
            import uuid

            doc_id = str(uuid.uuid4())

        # Default metadata if none provided
        if metadata is None:
            metadata = {
                "source": "direct_input",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

        # In a real implementation, we would use a proper embedding model
        # For this placeholder, we're just storing the text directly
        self.collection.add(documents=[text], metadatas=[metadata], ids=[doc_id])

        return doc_id

    def embed_documents(
        self, documents: List[Union[Tuple[str, str], Tuple[str, str, Dict[str, Any]]]]
    ) -> List[str]:
        """Embed multiple documents in a batch.

        Args:
            documents: List of tuples containing:
                - doc_id: Document ID
                - text: Text to embed
                - metadata: (Optional) Metadata for the document

        Returns:
            List of document IDs for the embedded documents.
        """
        doc_ids = []
        for item in documents:
            if len(item) == 2:
                doc_id, text = item
                metadata = None
            else:
                doc_id, text, metadata = item

            doc_id = self.embed_text(text, doc_id, metadata)
            doc_ids.append(doc_id)

        return doc_ids


if __name__ == "__main__":
    # Example usage
    embedder = Embedder()
    doc_id = embedder.embed_text("This is a sample document for embedding.")
    logger.info(f"Document embedded with ID: {doc_id}")
