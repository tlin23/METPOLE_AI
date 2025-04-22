"""
Embedder module for converting text to vector embeddings.
"""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path
from datetime import datetime

from app.vector_store.init_chroma import init_chroma_db
from app.config import CHROMA_DB_PATH
from app.logging_config import get_logger

# Get logger for this module
logger = get_logger("embedder.embed")

# Load environment variables
load_dotenv()


class Embedder:
    """
    Class for handling text embeddings.
    """
    
    def __init__(self, model_name="default"):
        """
        Initialize the embedder.
        
        Args:
            model_name (str): Name of the embedding model to use.
        """
        self.model_name = model_name
        
        # Get the path for the Chroma database
        self.chroma_db_path = CHROMA_DB_PATH
        
        # Create the directory if it doesn't exist
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize the persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Initialize the collection
        self.collection = self.chroma_client.get_or_create_collection("documents")
    
    def embed_text(self, text, doc_id=None, metadata=None):
        """
        Convert text to embeddings and store in ChromaDB.
        
        Args:
            text (str): Text to embed.
            doc_id (str, optional): Document ID. Defaults to None.
            metadata (dict, optional): Metadata for the document. Defaults to None.
            
        Returns:
            str: Document ID of the embedded text.
        """
        if doc_id is None:
            # Generate a simple ID if none provided
            import uuid
            doc_id = str(uuid.uuid4())
        
        # Default metadata if none provided
        if metadata is None:
            metadata = {
                "source": "direct_input",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        
        # In a real implementation, we would use a proper embedding model
        # For this placeholder, we're just storing the text directly
        self.collection.add(
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        return doc_id
    
    def embed_documents(self, documents):
        """
        Embed multiple documents.
        
        Args:
            documents (list): List of (doc_id, text, metadata) tuples.
                metadata is optional and can be None.
            
        Returns:
            list: List of document IDs.
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
