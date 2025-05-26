import json
import logging
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
from .directory_utils import (
    get_step_dir,
    clean_environment,
    ensure_directory_structure,
    validate_db_path,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        parser = parser_class()
        chunks = parser.parse(file_path)

        if chunks:
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
    allowed_extensions: Optional[List[str]] = None,
    production: bool = False,
) -> Tuple[List[Path], List[str]]:
    """
    Crawl web or local content and save raw files.

    Args:
        input_source: URL (for web processing) or path (for local processing)
        output_dir: Base directory for output files
        allowed_domains: List of allowed domains for web crawling
        allowed_extensions: List of allowed file extensions for local processing
        production: Whether to run in production mode

    Returns:
        Tuple of (list of extracted file paths, list of error messages)
    """
    # Clean and ensure directory structure
    clean_environment(output_dir, production)
    output_subdir = get_step_dir(output_dir, "crawled", production)

    errors = []
    try:
        if _is_valid_url(input_source):
            crawler = WebCrawler(allowed_domains=allowed_domains)
            extracted_files = crawler.extract(input_source, output_subdir)
        else:
            input_path = Path(input_source)
            if not input_path.exists():
                raise ValueError(f"Input path does not exist: {input_path}")
            crawler = LocalCrawler(allowed_extensions=allowed_extensions)
            extracted_files = crawler.extract(input_path, output_subdir)
        return extracted_files, errors

    except Exception as e:
        error_msg = f"Crawl failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
        return [], errors


def parse_files(
    input_dir: Path,
    output_dir: Path,
    allowed_extensions: Optional[List[str]] = None,
    n_limit: Optional[int] = None,
    production: bool = False,
) -> Tuple[List[Path], List[str]]:
    """
    Parse files into ContentChunk JSONs.

    Args:
        input_dir: Directory containing input files
        output_dir: Base directory for output files
        allowed_extensions: List of allowed file extensions
        n_limit: Maximum number of files to process
        production: Whether to run in production mode

    Returns:
        Tuple of (list of output JSON paths, list of error messages)
    """
    # Clean and ensure directory structure
    clean_environment(output_dir, production)
    output_subdir = get_step_dir(output_dir, "parsed", production)

    errors = []
    output_paths = []

    # Find all files to process
    files_to_process = []
    for ext in allowed_extensions or PARSER_MAP.keys():
        files_to_process.extend(input_dir.rglob(f"*{ext}"))

    if n_limit:
        files_to_process = files_to_process[:n_limit]

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

    return output_paths, errors


def embed_chunks_from_dir(
    input_dir: Path,
    db_path: str,
    collection_name: str,
    n_limit: Optional[int] = None,
    production: bool = False,
) -> Tuple[int, List[str]]:
    """
    Embed all ContentChunk JSONs in a directory.

    Args:
        input_dir: Directory containing ContentChunk JSONs
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        n_limit: Maximum number of files to embed
        production: Whether to run in production mode

    Returns:
        Tuple of (number of files embedded, list of error messages)
    """
    errors = []
    json_files = list(input_dir.rglob("*.json"))

    if n_limit:
        json_files = json_files[:n_limit]

    try:
        embed_chunks(json_files, collection_name, db_path)
        return len(json_files), errors
    except Exception as e:
        error_msg = f"Embedding failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        errors.append(error_msg)
        return 0, errors


def run_pipeline(
    input_source: str,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_domains: Optional[List[str]] = None,
    allowed_extensions: Optional[List[str]] = None,
    production: bool = False,
) -> Dict[str, Path]:
    """
    Run the full content processing pipeline.

    Args:
        input_source: URL (for web processing) or path (for local processing)
        output_dir: Base directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_domains: List of allowed domains for web crawling
        allowed_extensions: List of allowed file extensions for local processing
        production: Whether to run in production mode

    Returns:
        Dict containing paths to output files and processing statistics
    """
    try:
        # Validate database path
        validate_db_path(db_path, output_dir)

        # Clean and ensure directory structure
        clean_environment(output_dir, production)
        ensure_directory_structure(output_dir, production)

        # Step 1: Crawl content
        crawled_files, crawl_errors = crawl_content(
            input_source, output_dir, allowed_domains, allowed_extensions, production
        )
        if crawl_errors:
            logger.warning(f"Crawl completed with {len(crawl_errors)} errors")

        # Step 2: Parse all crawled files
        crawled_dir = get_step_dir(output_dir, "crawled", production)
        parsed_files, parse_errors = parse_files(
            crawled_dir,
            output_dir,
            allowed_extensions,
            production=production,
        )
        if parse_errors:
            logger.warning(f"Parse completed with {len(parse_errors)} errors")

        # Step 3: Embed chunks
        n_embedded, embed_errors = embed_chunks_from_dir(
            get_step_dir(output_dir, "parsed", production),
            db_path,
            collection_name,
            production=production,
        )
        if embed_errors:
            logger.warning(f"Embed completed with {len(embed_errors)} errors")

        # Determine if input was web or local
        is_web = _is_valid_url(input_source)
        web_crawled_files = len(crawled_files) if is_web else 0
        local_crawled_files = len(crawled_files) if not is_web else 0

        return {
            "output_dir": output_dir,
            "crawled_dir": crawled_dir,
            "parsed_dir": get_step_dir(output_dir, "parsed", production),
            "web_crawled_files": web_crawled_files,
            "local_crawled_files": local_crawled_files,
            "parsed_files": len(parsed_files),
            "embedded_files": n_embedded,
        }
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)


# Backward compatibility functions
def run_web_pipeline(
    url: str,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_domains: List[str] = None,
) -> Dict[str, Path]:
    """Run the web processing pipeline (legacy function)."""
    return run_pipeline(
        input_source=url,
        output_dir=output_dir,
        db_path=db_path,
        collection_name=collection_name,
        allowed_domains=allowed_domains,
    )


def run_local_pipeline(
    input_dir: Path,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_extensions: List[str] = None,
) -> Dict[str, Path]:
    """Run the local file processing pipeline (legacy function)."""
    return run_pipeline(
        input_source=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        collection_name=collection_name,
        allowed_extensions=allowed_extensions,
    )
