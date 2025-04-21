"""
Embedder module for converting text to vector embeddings.
"""

import os
from dotenv import load_dotenv
import chromadb


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
        self.chroma_client = chromadb.Client()
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "./chroma_db")
        
        # Initialize the collection
        self.collection = self.chroma_client.get_or_create_collection("documents")
    
    def embed_text(self, text, doc_id=None):
        """
        Convert text to embeddings and store in ChromaDB.
        
        Args:
            text (str): Text to embed.
            doc_id (str, optional): Document ID. Defaults to None.
            
        Returns:
            str: Document ID of the embedded text.
        """
        if doc_id is None:
            # Generate a simple ID if none provided
            import uuid
            doc_id = str(uuid.uuid4())
        
        # In a real implementation, we would use a proper embedding model
        # For this placeholder, we're just storing the text directly
        self.collection.add(
            documents=[text],
            ids=[doc_id]
        )
        
        return doc_id
    
    def embed_documents(self, documents):
        """
        Embed multiple documents.
        
        Args:
            documents (list): List of (doc_id, text) tuples.
            
        Returns:
            list: List of document IDs.
        """
        doc_ids = []
        for doc_id, text in documents:
            doc_id = self.embed_text(text, doc_id)
            doc_ids.append(doc_id)
        
        return doc_ids


if __name__ == "__main__":
    # Example usage
    embedder = Embedder()
    doc_id = embedder.embed_text("This is a sample document for embedding.")
    print(f"Document embedded with ID: {doc_id}")
