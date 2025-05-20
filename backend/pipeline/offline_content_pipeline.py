#!/usr/bin/env python3
"""
Offline Content Pipeline for Metropole.AI

This script handles the processing of offline documents:
1. Extract structured docs from files
2. Extract chunks from structured docs
3. Add metadata and tags to the content
4. Store in vector database

Usage:
    python offline_content_pipeline.py --step all -p
"""

import argparse
import time
import shutil
from backend.configer.logging_config import get_logger
from backend.embedder.embed_corpus import embed_corpus
from backend.configer.config import (
    INDEX_DIR,
    BATCH_SIZE,
    OFFLINE_COLLECTION_NAME,
    OFFLINE_DOCS_DIR,
    DOC_TEXT_DIR as RAW_DOCS_DIR,
    OFFLINE_CHUNKS_JSON_PATH,
    OFFLINE_CORPUS_PATH,
)
from .process_documents import (
    extract_structured_docs_from_files,
    extract_chunks_from_raw_docs,
    add_tags_to_chunks,
)

logger = get_logger("offline_pipeline")


def extract_offline_docs():
    logger.info("Step 1: Extracting structured docs from offline files...")
    extract_structured_docs_from_files(OFFLINE_DOCS_DIR, RAW_DOCS_DIR)
    logger.info("Step 1 complete.")


def process_offline_docs(production: bool):
    logger.info("Step 2: Extracting chunks from structured docs...")
    extract_chunks_from_raw_docs(RAW_DOCS_DIR, OFFLINE_CHUNKS_JSON_PATH)
    logger.info("Step 2A complete.")
    if production:
        logger.info("Step 2B: Adding tags to chunks...")
        add_tags_to_chunks(OFFLINE_CHUNKS_JSON_PATH, OFFLINE_CORPUS_PATH)
        logger.info("Step 2B complete.")
    else:
        shutil.copyfile(OFFLINE_CHUNKS_JSON_PATH, OFFLINE_CORPUS_PATH)
        logger.info("Copied chunks to corpus file without tags (non-production mode)")


def embed_offline_corpus():
    logger.info("Step 3: Embedding offline corpus...")
    start_time = time.time()
    embed_corpus(
        corpus_path=OFFLINE_CORPUS_PATH,
        chroma_db_path=INDEX_DIR,
        collection_name=OFFLINE_COLLECTION_NAME,
        batch_size=BATCH_SIZE,
    )
    elapsed_time = time.time() - start_time
    logger.info(f"Embedding complete in {elapsed_time:.2f} seconds")


def run_offline_pipeline(production: bool):
    logger.info("Starting offline content pipeline")
    total_start_time = time.time()
    try:
        extract_offline_docs()
        process_offline_docs(production)
        embed_offline_corpus()
        total_elapsed_time = time.time() - total_start_time
        logger.info(
            f"Offline pipeline complete! Total time: {total_elapsed_time:.2f} seconds"
        )
    except Exception:
        logger.exception("Offline pipeline failed due to an unexpected error.")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the offline content processing pipeline."
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

    if args.step == "all":
        run_offline_pipeline(args.production)
    elif args.step == "extract":
        extract_offline_docs()
    elif args.step == "process":
        process_offline_docs(args.production)
    elif args.step == "embed":
        embed_offline_corpus()
    else:
        print("Invalid step. Use 'all', 'extract', 'process', or 'embed'.")
        exit(1)
