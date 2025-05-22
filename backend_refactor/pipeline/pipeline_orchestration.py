import json
import logging
from pathlib import Path
from typing import List, Dict, Type, Optional
from urllib.parse import urlparse
from ..crawlers.web_crawler import WebCrawler
from ..crawlers.local_crawler import LocalCrawler
from ..parsers.html_parser import HTMLParser
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DOCXParser
from ..models.content_chunk import ContentChunk
from ..embedder.embedding_utils import embed_chunks

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
        error_msg = f"Error processing {file_path}: {str(e)}"
        logger.error(error_msg)
        _save_error_to_json(error_msg, output_path)
        return None


def _is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    result = urlparse(url)
    return all([result.scheme, result.netloc])


def run_pipeline(
    input_source: str,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_domains: Optional[List[str]] = None,
    allowed_extensions: Optional[List[str]] = None,
) -> Dict[str, Path]:
    """
    Run the content processing pipeline for either web or local input.

    Args:
        input_source: URL (for web processing) or path (for local processing)
        output_dir: Directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_domains: List of allowed domains for web crawling
        allowed_extensions: List of allowed file extensions for local processing

    Returns:
        Dict containing paths to output files

    Raises:
        ValueError: If input_source is neither a valid URL nor a valid local path
    """
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Determine input type and process accordingly
        if _is_valid_url(input_source):
            # Web processing
            crawler = WebCrawler(allowed_domains=allowed_domains)
            extracted_files = crawler.extract(Path(input_source), output_dir)
        else:
            # Local processing
            input_path = Path(input_source)
            if not input_path.exists():
                raise ValueError(f"Input path does not exist: {input_path}")
            crawler = LocalCrawler(allowed_extensions=allowed_extensions)
            extracted_files = crawler.extract(input_path, output_dir)

        # Process each file individually
        output_paths = []
        for file_path in extracted_files:
            output_path = _process_single_file(file_path, output_dir)
            if output_path:
                output_paths.append(output_path)

        if not output_paths:
            raise ValueError("No files were successfully processed")

        # Embed chunks from all output files
        embed_chunks(output_paths, collection_name, db_path)

        return {"output_dir": output_dir}

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise e


# Backward compatibility functions
def run_web_pipeline(
    url: str,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_domains: List[str] = None,
) -> Dict[str, Path]:
    """
    Run the web processing pipeline (legacy function).

    Args:
        url: Root URL to crawl
        output_dir: Directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_domains: List of allowed domains for crawling

    Returns:
        Dict containing paths to output files
    """
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
    """
    Run the local file processing pipeline (legacy function).

    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_extensions: List of allowed file extensions

    Returns:
        Dict containing paths to output files
    """
    return run_pipeline(
        input_source=input_dir,
        output_dir=output_dir,
        db_path=db_path,
        collection_name=collection_name,
        allowed_extensions=allowed_extensions,
    )
