#!/usr/bin/env python3
"""
Metropole.AI Pipeline Script

This script orchestrates the full data pipeline:
1. Crawl the website and save HTML files
2. Process HTML files to extract structured content
3. Add metadata and tags to the content
4. Embed the corpus and store in ChromaDB

Usage:
    python run_pipeline.py --start-url https://www.metropoleballard.com/home --max-pages 50
"""

import argparse
import time
from typing import Dict, Optional

# Import backend_legacy modules
from backend_legacy.configer.logging_config import get_logger
from backend_legacy.crawler.crawl import recursive_crawl
from backend_legacy.crawler.extract_content import (
    extract_chunks_without_tags,
    add_tags_to_chunks,
)
from backend_legacy.embedder.embed_corpus import embed_corpus
from backend_legacy.configer.config import (
    HTML_DIR,
    INDEX_DIR,
    CHUNKS_JSON_PATH,
    CORPUS_PATH,
    WEB_COLLECTION_NAME,
    BATCH_SIZE,
)

# Get logger for this module
logger = get_logger("pipeline")


def crawl_website(start_url: str, max_pages: Optional[int] = None) -> Dict[str, str]:
    """
    Crawl the website and save HTML files.

    Args:
        start_url: The URL to start crawling from.
        max_pages: Maximum number of pages to crawl. None for unlimited.

    Returns:
        Dictionary mapping URLs to their HTML content.
    """
    logger.info(f"Starting website crawl from {start_url}")
    logger.info(f"Max pages: {max_pages if max_pages is not None else 'unlimited'}")

    # Crawl the website
    start_time = time.time()
    content_dict = recursive_crawl(HTML_DIR, start_url, max_pages=max_pages)
    elapsed_time = time.time() - start_time

    logger.info(
        f"Crawling complete. Collected {len(content_dict)} pages in {elapsed_time:.2f} seconds"
    )
    return content_dict


def process_html_files(production: bool) -> None:
    """
    Process HTML files to extract structured content and add metadata.

    Args:
        production: If True, run the full pipeline including tag extraction.
    """
    logger.info("Processing HTML files")

    start_time = time.time()

    # Step 2A: Extract chunks without tags
    extract_chunks_without_tags(HTML_DIR, CHUNKS_JSON_PATH)

    # Step 2B: Add tags to the chunks
    if production:
        add_tags_to_chunks(CHUNKS_JSON_PATH, CORPUS_PATH)
    else:
        import shutil

        shutil.copyfile(CHUNKS_JSON_PATH, CORPUS_PATH)
        logger.info("Copied chunks.json to metropole_corpus.json without tags")

    elapsed_time = time.time() - start_time

    logger.info(
        f"Processing complete. Prod mode: {production}. Extracted chunks in {elapsed_time:.2f} seconds"
    )


def embed_corpus_data() -> None:
    """
    Embed the corpus and store in ChromaDB.
    """
    logger.info("Embedding corpus")
    start_time = time.time()

    embed_corpus(
        corpus_path=CORPUS_PATH,
        chroma_db_path=INDEX_DIR,
        collection_name=WEB_COLLECTION_NAME,
        batch_size=BATCH_SIZE,
    )

    elapsed_time = time.time() - start_time
    logger.info(f"Embedding complete in {elapsed_time:.2f} seconds")


def run_pipeline(
    start_url: str, max_pages: Optional[int] = None, production: bool = False
) -> None:
    """
    Run the full pipeline.

    Args:
        start_url: The URL to start crawling from.
        max_pages: Maximum number of pages to crawl. None for unlimited.
    """
    logger.info("Starting Metropole.AI pipeline")
    total_start_time = time.time()

    try:
        # Step 1: Crawl the website
        crawl_website(start_url, max_pages)

        # Step 2: Process HTML files and extract content
        process_html_files(production)

        # Step 3: Embed the corpus
        embed_corpus_data()

        total_elapsed_time = time.time() - total_start_time
        logger.info(f"Pipeline complete! Total time: {total_elapsed_time:.2f} seconds")

    except Exception:
        logger.exception("Pipeline failed due to an unexpected error.")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Metropole.AI pipeline.")
    parser.add_argument(
        "--start-url",
        type=str,
        default="https://www.metropoleballard.com/home",
        help="Starting URL to crawl",
    )
    parser.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl")
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
        choices=["all", "crawl", "process", "embed"],
        help="Which pipeline step to run",
    )

    args = parser.parse_args()

    if args.step == "all":
        run_pipeline(args.start_url, args.max_pages, args.production)
    elif args.step == "crawl":
        crawl_website(args.start_url, args.max_pages)
    elif args.step == "process":
        process_html_files(args.production)
    elif args.step == "embed":
        embed_corpus_data()
    else:
        print("Invalid step. Use 'all', 'crawl', 'process', or 'embed'.")
        exit(1)
