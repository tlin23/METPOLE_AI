#!/usr/bin/env python3
"""
Script to load the metropole_corpus.json file, embed each chunk using all-MiniLM-L6-v2,
and store the text and metadata in Chroma.
"""

import os
import sys
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from tqdm import tqdm

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.config import CHROMA_DB_PATH

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_corpus(corpus_path: str) -> List[Dict[str, Any]]:
    """
    Load the corpus from a JSON file.
    
    Args:
        corpus_path (str): Path to the corpus file.
        
    Returns:
        List[Dict[str, Any]]: The loaded corpus.
    """
    logger.info(f"Loading corpus from {corpus_path}")
    try:
        with open(corpus_path, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        logger.info(f"Successfully loaded corpus with {len(corpus)} chunks")
        return corpus
    except Exception as e:
        logger.error(f"Error loading corpus: {e}")
        raise


def embed_corpus(
    corpus_path: str,
    chroma_path: Optional[str] = None,
    collection_name: str = "metropole_documents",
    batch_size: int = 100
) -> None:
    """
    Embed the corpus using all-MiniLM-L6-v2 and store in Chroma.
    
    Args:
        corpus_path (str): Path to the corpus file.
        chroma_path (Optional[str]): Path to the Chroma DB. If None, uses the CHROMA_DB_PATH env var or default.
        collection_name (str): Name of the collection to store embeddings in.
        batch_size (int): Number of documents to embed in each batch.
    """
    start_time = time.time()
    
    # Get the Chroma DB path
    if chroma_path is None:
        chroma_path = CHROMA_DB_PATH
    
    # Create the directory if it doesn't exist
    Path(chroma_path).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing Chroma DB at: {chroma_path}")
    
    # Initialize the embedding function
    # Note: DefaultEmbeddingFunction uses the 'all-MiniLM-L6-v2' model internally
    logger.info("Loading default embedding model (all-MiniLM-L6-v2)...")
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    
    # Initialize the Chroma client
    client = chromadb.PersistentClient(
        path=chroma_path,
        settings=Settings(
            anonymized_telemetry=False
        )
    )
    
    # Create or get the collection
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        metadata={"description": "Metropole corpus embeddings"}
    )
    
    # Load the corpus
    corpus = load_corpus(corpus_path)
    
    # Prepare data for embedding
    total_chunks = len(corpus)
    logger.info(f"Preparing to embed {total_chunks} chunks")
    
    # Process in batches
    total_batches = (total_chunks + batch_size - 1) // batch_size
    total_embedded = 0
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, total_chunks)
        batch = corpus[start_idx:end_idx]
        
        # Extract data for this batch
        ids = [chunk["chunk_id"] for chunk in batch]
        documents = [chunk["content"] for chunk in batch]
        metadatas = [{
            "page_id": chunk["page_id"],
            "page_title": chunk["page_title"],
            "page_name": chunk["page_name"],
            "section_header": chunk["section_header"],
            "tags": ",".join(chunk["tags"]) if isinstance(chunk["tags"], list) else chunk["tags"]
        } for chunk in batch]
        
        # Add to collection
        logger.info(f"Embedding batch {batch_idx + 1}/{total_batches} ({len(batch)} chunks)")
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
        
        total_embedded += len(batch)
        logger.info(f"Progress: {total_embedded}/{total_chunks} chunks embedded")
    
    # Log completion
    elapsed_time = time.time() - start_time
    logger.info(f"Embedding complete! {total_embedded} chunks embedded in {elapsed_time:.2f} seconds")
    logger.info(f"Collection '{collection_name}' now contains {collection.count()} documents")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Embed the Metropole corpus using all-MiniLM-L6-v2.')
    parser.add_argument('--corpus-path', type=str, 
                        default='./data/processed/metropole_corpus.json',
                        help='Path to the corpus file')
    parser.add_argument('--chroma-path', type=str, 
                        default=None,
                        help='Path to the Chroma DB')
    parser.add_argument('--collection-name', type=str, 
                        default='metropole_documents',
                        help='Name of the collection to store embeddings in')
    parser.add_argument('--batch-size', type=int, 
                        default=100,
                        help='Number of documents to embed in each batch')
    
    args = parser.parse_args()
    
    embed_corpus(
        corpus_path=args.corpus_path,
        chroma_path=args.chroma_path,
        collection_name=args.collection_name,
        batch_size=args.batch_size
    )
