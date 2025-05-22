import json
from pathlib import Path
from typing import List, Dict, Type
from ..extractors.web_extractor import WebExtractor
from ..extractors.local_extractor import LocalExtractor
from ..parsers.html_parser import HTMLParser
from ..parsers.pdf_parser import PDFParser
from ..parsers.docx_parser import DOCXParser
from ..models.content_chunk import ContentChunk
from ..embedder.embedding_utils import embed_chunks

# Map file extensions to their corresponding parsers
PARSER_MAP: Dict[str, Type] = {
    ".html": HTMLParser,
    ".pdf": PDFParser,
    ".docx": DOCXParser,
}


def _save_chunks_to_json(chunks: List[ContentChunk], output_dir: Path) -> Path:
    """Save chunks to a JSON file and return the path."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "parsed_chunks.json"

    # Convert chunks to dict format for JSON serialization
    chunks_data = [chunk.dict() for chunk in chunks]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f, indent=2)

    return output_path


def _process_files(file_paths: List[Path], output_dir: Path) -> List[ContentChunk]:
    """Process a list of files using appropriate parsers."""
    all_chunks = []

    for file_path in file_paths:
        parser_class = PARSER_MAP.get(file_path.suffix.lower())
        if parser_class:
            try:
                parser = parser_class()
                chunks = parser.parse(file_path)
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"Error processing {file_path}: {str(e)}")
                continue

    return all_chunks


def run_web_pipeline(
    url: str,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_domains: List[str] = None,
) -> Dict[str, Path]:
    """
    Run the web processing pipeline.

    Args:
        url: Root URL to crawl
        output_dir: Directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_domains: List of allowed domains for crawling

    Returns:
        Dict containing paths to output files
    """
    # Create subdirectories
    html_dir = output_dir / "html"
    html_dir.mkdir(parents=True, exist_ok=True)

    parsed_dir = output_dir / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # Extract HTML files
    extractor = WebExtractor(allowed_domains=allowed_domains)
    html_files = extractor.extract(Path(url), html_dir)

    # Parse HTML files
    chunks = _process_files(html_files, parsed_dir)

    # Save chunks to JSON
    json_path = _save_chunks_to_json(chunks, parsed_dir)

    # Embed chunks
    embed_chunks(chunks, collection_name, db_path)

    return {"html_files": html_dir, "parsed_json": json_path}


def run_local_pipeline(
    input_dir: Path,
    output_dir: Path,
    db_path: str,
    collection_name: str,
    allowed_extensions: List[str] = None,
) -> Dict[str, Path]:
    """
    Run the local file processing pipeline.

    Args:
        input_dir: Directory containing input files
        output_dir: Directory for output files
        db_path: Path to ChromaDB database
        collection_name: Name of ChromaDB collection
        allowed_extensions: List of allowed file extensions

    Returns:
        Dict containing paths to output files
    """
    # Create subdirectories
    extracted_dir = output_dir / "extracted"
    extracted_dir.mkdir(parents=True, exist_ok=True)

    parsed_dir = output_dir / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)

    # Extract and organize files
    extractor = LocalExtractor(allowed_extensions=allowed_extensions)
    extracted_files = extractor.extract(input_dir, extracted_dir)

    # Parse files
    chunks = _process_files(extracted_files, parsed_dir)

    # Save chunks to JSON
    json_path = _save_chunks_to_json(chunks, parsed_dir)

    # Embed chunks
    embed_chunks(chunks, collection_name, db_path)

    return {"extracted_files": extracted_dir, "parsed_json": json_path}
