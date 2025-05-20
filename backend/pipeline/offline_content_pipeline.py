#!/usr/bin/env python3
"""
Offline Content Pipeline for Metropole.AI

This script handles the processing of offline documents:
1. Extract raw text from documents
2. Process text files to extract structured content
3. Add metadata and tags to the content
4. Store in vector database

Usage:
    python offline_content_pipeline.py --input-dir /path/to/documents --collection metropole_documents
"""

import argparse
import os
import time
from pathlib import Path
from typing import Optional, Dict, List, Any

from backend.configer.logging_config import get_logger
from backend.embedder.embed_corpus import embed_corpus
from backend.configer.config import INDEX_DIR, BATCH_SIZE, OFFLINE_COLLECTION_NAME
from .process_documents import (
    extract_document_text,
    extract_chunks_without_tags,
    add_tags_to_chunks,
    RAW_TEXT_DIR,
    PROCESSED_DIR,
)

# Get logger for this module
logger = get_logger("offline_pipeline")


def extract_documents(input_dir: str) -> Dict[str, str]:
    """
    Extract raw text from documents and save to files.

    Args:
        input_dir: Directory containing the documents to process

    Returns:
        Dictionary mapping document paths to their extracted text
    """
    logger.info(f"Extracting text from documents in {input_dir}")
    start_time = time.time()

    extracted_texts = extract_document_text(input_dir)

    elapsed_time = time.time() - start_time
    logger.info(f"Document extraction complete in {elapsed_time:.2f} seconds")

    return extracted_texts


def process_document_text(production: bool = True) -> List[Dict[str, Any]]:
    """
    Process extracted text files to create chunks and add metadata.

    Args:
        production: If True, run the full pipeline including tag extraction.

    Returns:
        List of processed chunks with metadata
    """
    logger.info("Processing document text files")
    start_time = time.time()

    # Step 1: Extract chunks without tags
    chunks_path = os.path.join(PROCESSED_DIR, "doc_chunks.json")
    chunks = extract_chunks_without_tags(RAW_TEXT_DIR, chunks_path)

    # Step 2: Add tags to chunks if in production mode
    if production:
        corpus_path = os.path.join(PROCESSED_DIR, "doc_corpus.json")
        chunks = add_tags_to_chunks(chunks_path, corpus_path)
    else:
        import shutil

        corpus_path = os.path.join(PROCESSED_DIR, "doc_corpus.json")
        shutil.copyfile(chunks_path, corpus_path)
        logger.info("Copied doc_chunks.json to doc_corpus.json without tags")

    elapsed_time = time.time() - start_time
    logger.info(f"Document processing complete in {elapsed_time:.2f} seconds")

    return chunks


def embed_document_chunks(
    collection_name: str = OFFLINE_COLLECTION_NAME, batch_size: Optional[int] = None
) -> None:
    """
    Embed document chunks and store in vector database.

    Args:
        collection_name: Name of the Chroma collection to store embeddings
        batch_size: Optional batch size for embedding process
    """
    logger.info("Embedding document chunks")
    start_time = time.time()

    corpus_path = os.path.join(PROCESSED_DIR, "doc_corpus.json")
    embed_corpus(
        corpus_path=corpus_path,
        chroma_db_path=INDEX_DIR,
        collection_name=collection_name,
        batch_size=batch_size or BATCH_SIZE,
    )

    elapsed_time = time.time() - start_time
    logger.info(f"Embedding complete in {elapsed_time:.2f} seconds")


def run_offline_pipeline(
    input_dir: str,
    collection_name: str = OFFLINE_COLLECTION_NAME,
    batch_size: Optional[int] = None,
    production: bool = True,
) -> None:
    """
    Run the complete offline content processing pipeline.

    Args:
        input_dir: Directory containing the documents to process
        collection_name: Name of the Chroma collection to store embeddings
        batch_size: Optional batch size for embedding process
        production: If True, run the full pipeline including tag extraction
    """
    logger.info("Starting offline content pipeline")
    total_start_time = time.time()

    try:
        # Step 1: Extract raw text from documents
        extract_documents(input_dir)

        # Step 2: Process text files and extract content
        process_document_text(production)

        # Step 3: Embed the corpus
        embed_document_chunks(collection_name, batch_size)

        total_elapsed_time = time.time() - total_start_time
        logger.info(
            f"Offline pipeline complete! Total time: {total_elapsed_time:.2f} seconds"
        )

    except Exception:
        logger.exception("Offline pipeline failed due to an unexpected error.")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Run the offline content processing pipeline."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="backend/data/offline_docs",
        help="Directory containing documents to process",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default=OFFLINE_COLLECTION_NAME,
        help="Chroma collection name for storing embeddings (default: metropole_offline_documents)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        help="Batch size for embedding process (optional)",
    )
    parser.add_argument(
        "-p",
        "--production",
        action="store_true",
        help="Run full processing including tag extraction",
    )
    parser.add_argument(
        "--step",
        type=str,
        default="all",
        choices=["all", "extract", "process", "embed"],
        help="Which pipeline step to run",
    )

    args = parser.parse_args()

    # Validate input directory
    input_path = Path(args.input_dir)
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {args.input_dir}")
        exit(1)
    if not input_path.is_dir():
        logger.error(f"Input path is not a directory: {args.input_dir}")
        exit(1)

    if args.step == "all":
        run_offline_pipeline(
            input_dir=args.input_dir,
            collection_name=args.collection,
            batch_size=args.batch_size,
            production=args.production,
        )
    elif args.step == "extract":
        extract_documents(args.input_dir)
    elif args.step == "process":
        process_document_text(args.production)
    elif args.step == "embed":
        embed_document_chunks(args.collection, args.batch_size)
    else:
        print("Invalid step. Use 'all', 'extract', 'process', or 'embed'.")
        exit(1)


if __name__ == "__main__":
    main()
