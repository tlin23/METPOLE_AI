"""
Script to initialize a Chroma persistent vector store.
"""

import sys
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.config import CHROMA_DB_PATH
from app.logging_config import get_logger

# Get logger for this module
logger = get_logger("vector_store.init_chroma")

# Load environment variables
load_dotenv()


def init_chroma_db():
    """
    Initialize a Chroma persistent vector store.

    Returns:
        chromadb.PersistentClient: The initialized Chroma client.
    """
    # Get the path for the Chroma database
    chroma_db_path = CHROMA_DB_PATH

    # Create the directory if it doesn't exist
    Path(chroma_db_path).mkdir(parents=True, exist_ok=True)

    logger.info(f"Initializing Chroma DB at: {chroma_db_path}")

    # Create a persistent client
    client = chromadb.PersistentClient(
        path=chroma_db_path, settings=Settings(anonymized_telemetry=False)
    )

    # Create a default collection if it doesn't exist
    collection = client.get_or_create_collection(
        name="documents",
        metadata={"description": "Main document collection for MetPol AI"},
    )

    logger.info(
        f"Collection '{collection.name}' initialized with {collection.count()} documents"
    )

    return client


if __name__ == "__main__":
    # Initialize the Chroma DB
    client = init_chroma_db()

    # List all collections
    collections = client.list_collections()
    logger.info(f"Available collections: {[c.name for c in collections]}")
