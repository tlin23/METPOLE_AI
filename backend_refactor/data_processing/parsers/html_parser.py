from pathlib import Path
import re
import hashlib
from typing import List, Set
from bs4 import BeautifulSoup
from ftfy import fix_text
from .base import BaseParser
from ..models.content_chunk import ContentChunk
from ..logger.logging_config import get_logger

logger = get_logger("parsers.html")


def clean_text(text: str) -> str:
    """Clean and normalize text by fixing encoding, stripping special characters, and collapsing whitespace."""
    text = fix_text(text)
    # Replace zero-width spaces with regular spaces
    text = text.replace("\u200b", " ")
    # Remove other invisible characters
    text = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", text)
    text = (
        text.replace(
            """, '"')
        .replace(""",
            '"',
        )
        .replace("'", "'")
        .replace("'", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("…", "...")
    )
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize(text: str) -> str:
    """Normalize text for hashing by converting to lowercase and removing non-word characters."""
    text = text.lower()
    text = re.sub(r"\W+", " ", text)
    return " ".join(text.split())


def hash_id(text: str) -> str:
    """Generate a unique hash ID for a text chunk."""
    normalized = normalize(text)
    return "chunk_" + hashlib.md5(normalized.encode("utf-8")).hexdigest()


class HTMLParser(BaseParser):
    def parse(self, file_path: Path) -> List[ContentChunk]:
        """
        Parse an HTML file and convert its contents into a list of ContentChunk objects.

        The parser:
        - Extracts meaningful content while ignoring non-content sections
        - Splits content into chunks of appropriate size
        - Extracts metadata like document title and section headers
        - Cleans and normalizes text
        - Generates unique chunk IDs
        - Prevents duplicate chunks

        Args:
            file_path: Path to the HTML file to parse

        Returns:
            List of ContentChunk objects representing the parsed content

        Raises:
            ValueError: If the file is not a valid HTML file
            IOError: If the file cannot be read
        """
        logger.info(f"Starting to parse HTML file: {file_path}")

        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise IOError(error_msg)

        if file_path.suffix.lower() != ".html":
            error_msg = f"Not an HTML file: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Read and parse HTML
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)

        soup = BeautifulSoup(html_content, "html.parser")

        # Extract document title
        title_tag = soup.find("title")
        document_title = clean_text(title_tag.text) if title_tag else None
        if document_title:
            logger.debug(f"Extracted document title: {document_title}")

        # Remove non-content elements
        for element in soup.find_all(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Extract and process content
        chunks = []
        seen_chunk_ids: Set[str] = set()
        current_heading = None
        chunk_count = 0

        # Process main content elements
        for element in soup.find_all(
            ["p", "h1", "h2", "h3", "h4", "h5", "h6", "article", "section"]
        ):
            # Update current heading if we find one
            if element.name.startswith("h"):
                current_heading = clean_text(element.text)
                logger.debug(f"Found heading: {current_heading}")
                continue

            # Skip empty elements
            if not element.text.strip():
                continue

            # Clean and process text
            text = clean_text(element.text)
            if len(text) < 20:  # Skip very short chunks
                logger.debug(f"Skipping short chunk: {text[:50]}...")
                continue

            # Combine heading with content if available
            if current_heading:
                text = f"{current_heading}\n{text}"
                current_heading = None  # Reset heading after using it

            # Generate chunk ID and check for duplicates
            chunk_id = hash_id(file_path.stem + text)
            if chunk_id in seen_chunk_ids:
                logger.debug(f"Skipping duplicate chunk: {chunk_id}")
                continue
            seen_chunk_ids.add(chunk_id)

            # Create chunk
            chunk = ContentChunk(
                chunk_id=chunk_id,
                file_name=file_path.stem,
                file_ext=file_path.suffix[1:],
                page_number=1,  # HTML files are single-page
                text_content=text,
                document_title=document_title,
            )

            chunks.append(chunk)
            chunk_count += 1

        logger.info(f"Successfully parsed {chunk_count} chunks from {file_path}")
        return chunks
