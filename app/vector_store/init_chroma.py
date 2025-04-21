"""
Script to initialize a Chroma persistent vector store.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load environment variables
load_dotenv()

def init_chroma_db():
    """
    Initialize a Chroma persistent vector store.
    
    Returns:
        chromadb.PersistentClient: The initialized Chroma client.
    """
    # Get the path for the Chroma database
    chroma_db_path = os.getenv("CHROMA_DB_PATH", "./data/index")
    
    # Create the directory if it doesn't exist
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)
    
    print(f"Initializing Chroma DB at: {chroma_db_path}")
    
    # Create a persistent client
    client = chromadb.PersistentClient(
        path=chroma_db_path,
        settings=Settings(
            anonymized_telemetry=False
        )
    )
    
    # Create a default collection if it doesn't exist
    collection = client.get_or_create_collection(
        name="documents",
        metadata={"description": "Main document collection for MetPol AI"}
    )
    
    print(f"Collection '{collection.name}' initialized with {collection.count()} documents")
    
    return client

if __name__ == "__main__":
    # Initialize the Chroma DB
    client = init_chroma_db()
    
    # List all collections
    collections = client.list_collections()
    print(f"Available collections: {[c.name for c in collections]}")
