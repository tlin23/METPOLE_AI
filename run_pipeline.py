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

import os
import sys
import argparse
import time
from typing import Dict, Optional

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import app modules
from app.logging_config import get_logger
from app.config import CHROMA_DB_PATH
from app.crawler.crawl import recursive_crawl
from app.crawler.extract_content import process_all_html_files
from app.embedder.embed_corpus import embed_corpus

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

    # Create data directory if it doesn't exist
    os.makedirs("data/html", exist_ok=True)

    # Crawl the website
    start_time = time.time()
    content_dict = recursive_crawl(start_url, max_pages=max_pages, save_to_files=True)
    elapsed_time = time.time() - start_time

    logger.info(
        f"Crawling complete. Collected {len(content_dict)} pages in {elapsed_time:.2f} seconds"
    )
    return content_dict


def process_html_content() -> None:
    """
    Process HTML files to extract structured content.
    """
    logger.info("Processing HTML files to extract structured content")

    # Directory containing HTML files
    html_directory = "data/html"

    # Create output directory if it doesn't exist
    output_directory = "data/processed"
    os.makedirs(output_directory, exist_ok=True)

    # Process all HTML files
    start_time = time.time()
    results = process_all_html_files(html_directory)

    # Save results to JSON file for inspection
    json_output_path = os.path.join(output_directory, "extracted_content.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        import json

        json.dump(results, f, indent=2, ensure_ascii=False)

    # Create Python objects for each page
    all_chunks = []

    for file_path, content in results.items():
        page_title = content["title"]
        page_name = os.path.basename(file_path).replace(".html", "")

        # Process each section
        for section in content["sections"]:
            section_header = section["header"]

            # Process each chunk in the section
            for chunk in section["chunks"]:
                # Create a structured object for each chunk
                chunk_object = {
                    "page_title": page_title,
                    "page_name": page_name,
                    "section_header": section_header,
                    "content": chunk["content"],
                    "content_html": chunk["content_html"],
                }

                all_chunks.append(chunk_object)

    # Save all chunks to a Python file
    py_output_path = os.path.join(output_directory, "content_objects.py")
    with open(py_output_path, "w", encoding="utf-8") as f:
        f.write('"""Generated content objects from HTML files."""\n\n')
        f.write("# This file is auto-generated. Do not edit directly.\n\n")
        f.write("content_objects = [\n")

        # Remove duplicate chunks by tracking content we've seen
        seen_content = set()
        unique_chunks = []

        for chunk in all_chunks:
            # Create a key based on content to detect duplicates
            content_key = f"{chunk['page_name']}:{chunk['section_header']}:{chunk['content'][:100]}"

            if content_key not in seen_content:
                seen_content.add(content_key)
                unique_chunks.append(chunk)

        # Write unique chunks to file
        for chunk in unique_chunks:
            f.write("    {\n")
            f.write(f"        'page_title': {json.dumps(chunk['page_title'])},\n")
            f.write(f"        'page_name': {json.dumps(chunk['page_name'])},\n")
            f.write(
                f"        'section_header': {json.dumps(chunk['section_header'])},\n"
            )
            f.write(f"        'content': {json.dumps(chunk['content'])},\n")
            f.write(f"        'content_html': {json.dumps(chunk['content_html'])}\n")
            f.write("    },\n")

        f.write("]\n")

    elapsed_time = time.time() - start_time
    logger.info(f"HTML processing complete in {elapsed_time:.2f} seconds")
    logger.info(
        f"Extracted {len(unique_chunks)} unique content chunks from {len(results)} HTML files"
    )


def add_metadata_and_tags() -> None:
    """
    Add metadata and tags to the content.
    """
    logger.info("Adding metadata and tags to content")

    # Import the add_metadata_and_tags module
    from app.crawler.add_metadata_and_tags import process_content_objects, save_to_json

    # Process content objects
    start_time = time.time()
    processed_objects = process_content_objects()

    # Save to JSON
    output_path = os.path.join("data", "processed", "metropole_corpus.json")
    save_to_json(processed_objects, output_path)

    elapsed_time = time.time() - start_time

    # Print summary
    page_count = len(set(obj["page_id"] for obj in processed_objects))
    tag_count = sum(len(obj["tags"]) for obj in processed_objects)

    logger.info(f"Metadata and tagging complete in {elapsed_time:.2f} seconds")
    logger.info(
        f"Processed {len(processed_objects)} content chunks from {page_count} unique pages"
    )
    logger.info(
        f"Generated {tag_count} tags (avg. {tag_count/len(processed_objects):.1f} per chunk)"
    )


def embed_corpus_data() -> None:
    """
    Embed the corpus and store in ChromaDB.
    """
    logger.info("Embedding corpus data")

    # Path to the corpus file
    corpus_path = os.path.join("data", "processed", "metropole_corpus.json")

    # Embed the corpus
    start_time = time.time()
    embed_corpus(
        corpus_path=corpus_path,
        chroma_path=CHROMA_DB_PATH,
        collection_name="metropole_documents",
        batch_size=100,
    )

    elapsed_time = time.time() - start_time
    logger.info(f"Corpus embedding complete in {elapsed_time:.2f} seconds")


def run_pipeline(start_url: str, max_pages: Optional[int] = None) -> None:
    """
    Run the full pipeline.

    Args:
        start_url: The URL to start crawling from.
        max_pages: Maximum number of pages to crawl. None for unlimited.
    """
    logger.info("Starting Metropole.AI pipeline")
    total_start_time = time.time()

    # Step 1: Crawl the website
    crawl_website(start_url, max_pages)

    # Step 2: Process HTML content
    process_html_content()

    # Step 3: Add metadata and tags
    add_metadata_and_tags()

    # Step 4: Embed the corpus
    embed_corpus_data()

    total_elapsed_time = time.time() - total_start_time
    logger.info(f"Pipeline complete! Total time: {total_elapsed_time:.2f} seconds")


if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run the Metropole.AI pipeline.")
    parser.add_argument(
        "--start-url",
        type=str,
        default="https://www.metropoleballard.com/home",
        help="URL to start crawling from",
    )
    parser.add_argument(
        "--max-pages", type=int, default=50, help="Maximum number of pages to crawl"
    )

    args = parser.parse_args()

    # Run the pipeline
    run_pipeline(args.start_url, args.max_pages)
