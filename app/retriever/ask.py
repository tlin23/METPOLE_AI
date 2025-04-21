"""
Retriever module for querying and retrieving information from embeddings.
"""

import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from pathlib import Path

from app.vector_store.init_chroma import init_chroma_db

# Load environment variables
load_dotenv()


class Retriever:
    """
    Class for retrieving information from embeddings.
    """
    
    def __init__(self):
        """
        Initialize the retriever.
        """
        # Get the path for the Chroma database
        self.chroma_db_path = os.getenv("CHROMA_DB_PATH", "./data/index")
        
        # Create the directory if it doesn't exist
        Path(self.chroma_db_path).mkdir(parents=True, exist_ok=True)
        
        # Initialize the persistent client
        self.chroma_client = chromadb.PersistentClient(
            path=self.chroma_db_path,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Get the collection
        self.collection = self.chroma_client.get_or_create_collection("documents")
    
    def query(self, query_text, n_results=5):
        """
        Query the embeddings database.
        
        Args:
            query_text (str): The query text.
            n_results (int, optional): Number of results to return. Defaults to 5.
            
        Returns:
            list: List of matching documents.
        """
        # In a real implementation, this would use semantic similarity search
        # For this placeholder, we're just doing a simple query
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        return results
    
    def get_document(self, doc_id):
        """
        Retrieve a specific document by ID.
        
        Args:
            doc_id (str): Document ID.
            
        Returns:
            dict: Document data.
        """
        result = self.collection.get(ids=[doc_id])
        return result


if __name__ == "__main__":
    # Example usage
    retriever = Retriever()
    results = retriever.query("sample query")
    print(f"Query results: {results}")
