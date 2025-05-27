import json
import traceback
from pathlib import Path
from typing import List, Dict, Type, Optional, Tuple
from urllib.parse import urlparse
from ..crawlers.web_crawler import WebCrawler
from ..crawlers.local_crawler import LocalCrawler
from ..parsers.html_parser import HTMLParser
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DOCXParser
from ..models.content_chunk import ContentChunk
from ..embedder.embedding_utils import embed_chunks
from ..logger.logging_config import get_logger
from .directory_utils import (
    get_step_dir,
    clean_pipeline,
    ALLOWED_EXTENSIONS,
)

# Set up logging
logger = get_logger("pipeline.orchestration")

# Map file extensions to their corresponding parsers
PARSER_MAP: Dict[str, Type] = {
    ".html": HTMLParser,
    ".pdf": PDFParser,
    ".docx": DOCXParser,
}


def _save_chunks_to_json(chunks: List[ContentChunk], output_path: Path) -> None:
    """Save chunks to a JSON file at the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert chunks to dict format for JSON serialization
    chunks_data = [chunk.model_dump() for chunk in chunks]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2)


def _save_error_to_json(error_message: str, output_path: Path) -> None:
    """Save error message to a JSON file at the specified path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    error_data = {"error": error_message}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(error_data, f, indent=2)


def _process_single_file(file_path: Path, output_dir: Path) -> Optional[Path]:
    """Process a single file using the appropriate parser and save results.

    Returns:
        Path to the output JSON file if successful, None if processing failed
    """
    # Create output path mirroring input structure
    rel_path = file_path.relative_to(file_path.parent.parent)
    output_path = output_dir / rel_path.with_suffix(".json")

    parser_class = PARSER_MAP.get(file_path.suffix.lower())
    if not parser_class:
        error_msg = f"No parser available for file extension: {file_path.suffix}"
        logger.warning(error_msg)
        _save_error_to_json(error_msg, output_path)
        return None

    try:
        logger.info(f"Processing file: {file_path}")
        parser = parser_class()
        chunks = parser.parse(file_path)

        if chunks:
            logger.info(f"Extracted {len(chunks)} chunks from {file_path}")
            _save_chunks_to_json(chunks, output_path)
            return output_path
        else:
            error_msg = f"No content chunks extracted from {file_path}"
            logger.warning(error_msg)
            _save_error_to_json(error_msg, output_path)
            return None

    except Exception as e:
        error_msg = f"Error processing {file_path}: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        _save_error_to_json(error_msg, output_path)
        return None


def _is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    if not url:
        return False

    result = urlparse(url)
    # Only allow http and https schemes
    if result.scheme not in ["http", "https"]:
        return False
    # Must have a domain
    if not result.netloc:
        return False
    return True


def crawl_content(
    input_source: str,
    output_dir: Path,
    allowed_domains: Optional[List[str]] = None,
    production: bool = False,
    skip_cleaning: bool = False,
) -> Tuple[List[Path], List[str]]:
    """
    Crawl web content and store HTML files in local_input_source.
    """
    if not skip_cleaning:
        clean_pipeline(output_dir, "crawl", production)
    output_subdir = get_step_dir(output_dir, "crawl", production)

    errors = []
    try:
        if not _is_valid_url(input_source):
            raise ValueError(f"Invalid URL: {input_source}")

        logger.info(f"Starting web crawl from {input_source}")
        crawler = WebCrawler(allowed_domains=allowed_domains)
        extracted_files = crawler.extract(input_source, output_subdir)
        logger.info(f"Crawl completed. Extracted {len(extracted_files)} files")
        return extracted_files, errors

    except Exception as e:
        error_msg = f"Crawl failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
        return [], errors


def sort_files(
    input_dir: Path,
    output_dir: Path,
    production: bool = False,
    skip_cleaning: bool = False,
) -> Tuple[List[Path], List[str]]:
    """
    Sort files from local_input_source to sorted_input_source by extension.
    """
    if not skip_cleaning:
        clean_pipeline(output_dir, "sort", production)
    output_subdir = get_step_dir(output_dir, "sort", production)

    errors = []
    sorted_files = []
    try:
        logger.info(f"Starting file sort from {input_dir}")
        crawler = LocalCrawler(allowed_extensions=ALLOWED_EXTENSIONS)
        sorted_files = crawler.extract(input_dir, output_subdir)
        logger.info(f"Sort completed. Sorted {len(sorted_files)} files")
        return sorted_files, errors

    except Exception as e:
        error_msg = f"Sort failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
        return [], errors


def parse_files(
    input_dir: Path,
    output_dir: Path,
    n_limit: Optional[int] = None,
    production: bool = False,
    skip_cleaning: bool = False,
) -> Tuple[List[Path], List[str]]:
    """
    Parse files from sorted_input_source and output content chunks to parsed.
    """
    if not skip_cleaning:
        clean_pipeline(output_dir, "parse", production)
    output_subdir = get_step_dir(output_dir, "parse", production)

    errors = []
    output_paths = []

    # Find all files to process
    files_to_process = []
    for ext in ALLOWED_EXTENSIONS:
        files_to_process.extend(input_dir.rglob(f"*{ext}"))

    if n_limit:
        files_to_process = files_to_process[:n_limit]
        logger.info(
            f"Found {n_limit} files to process (limited from {len(files_to_process)})"
        )
    else:
        logger.info(f"Found {len(files_to_process)} files to process")

    for file_path in files_to_process:
        try:
            output_path = _process_single_file(file_path, output_subdir)
            if output_path:
                output_paths.append(output_path)
        except Exception as e:
            error_msg = (
                f"Error processing {file_path}: {str(e)}\n{traceback.format_exc()}"
            )
            logger.error(error_msg)
            errors.append(error_msg)

    logger.info(
        f"Parse completed. Successfully processed {len(output_paths)} out of {len(files_to_process)} files"
    )
    return output_paths, errors


def embed_chunks_from_dir(
    input_dir: Path,
    output_dir: Path,
    collection_name: str,
    n_limit: Optional[int] = None,
    production: bool = False,
    skip_cleaning: bool = False,
) -> Tuple[int, List[str]]:
    """
    Embed content chunks from parsed and store in chroma_db.
    """
    if not skip_cleaning:
        clean_pipeline(output_dir, "embed", production)
    output_subdir = get_step_dir(output_dir, "embed", production)

    errors = []
    json_files = list(input_dir.rglob("*.json"))

    if n_limit:
        json_files = json_files[:n_limit]
        logger.info(f"Embedding {n_limit} files (limited from {len(json_files)})")
    else:
        logger.info(f"Embedding {len(json_files)} files")

    try:
        logger.info(f"Starting embedding into collection: {collection_name}")
        embed_chunks(json_files, collection_name, output_subdir)
        logger.info(f"Embedding completed. Processed {len(json_files)} files")
        return len(json_files), errors
    except Exception as e:
        error_msg = f"Embedding failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
        return 0, errors


def run_pipeline(
    input_source: str,
    output_dir: Path,
    collection_name: str,
    allowed_domains: Optional[List[str]] = None,
    production: bool = False,
) -> Dict[str, Path]:
    """
    Run the complete pipeline from crawl to embed.
    """
    logger.info("Starting pipeline execution")
    # Clean all outputs before starting
    clean_pipeline(output_dir, "crawl", production)

    # Step 1: Crawl
    logger.info("Step 1: Starting crawl")
    crawled_files, crawl_errors = crawl_content(
        input_source=input_source,
        output_dir=output_dir,
        allowed_domains=allowed_domains,
        production=production,
        skip_cleaning=True,
    )
    if crawl_errors:
        logger.warning(f"Crawl completed with {len(crawl_errors)} errors")

    # Step 2: Sort
    logger.info("Step 2: Starting sort")
    sorted_files, sort_errors = sort_files(
        input_dir=get_step_dir(output_dir, "crawl", production),
        output_dir=output_dir,
        production=production,
        skip_cleaning=True,
    )
    if sort_errors:
        logger.warning(f"Sort completed with {len(sort_errors)} errors")

    # Step 3: Parse
    logger.info("Step 3: Starting parse")
    parsed_files, parse_errors = parse_files(
        input_dir=get_step_dir(output_dir, "sort", production),
        output_dir=output_dir,
        production=production,
        skip_cleaning=True,
    )
    if parse_errors:
        logger.warning(f"Parse completed with {len(parse_errors)} errors")

    # Step 4: Embed
    logger.info("Step 4: Starting embed")
    n_embedded, embed_errors = embed_chunks_from_dir(
        input_dir=get_step_dir(output_dir, "parse", production),
        output_dir=output_dir,
        collection_name=collection_name,
        production=production,
        skip_cleaning=True,
    )
    if embed_errors:
        logger.warning(f"Embed completed with {len(embed_errors)} errors")

    logger.info("Pipeline execution completed")
    return {
        "output_dir": output_dir,
        "crawled_files": len(crawled_files),
        "sorted_files": len(sorted_files),
        "parsed_files": len(parsed_files),
        "embedded_files": n_embedded,
    }
