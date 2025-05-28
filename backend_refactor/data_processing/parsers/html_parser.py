from pathlib import Path
import re
import hashlib
from typing import List, Set, Optional, Tuple
from bs4 import Tag
from ftfy import fix_text
from .base import BaseParser
from ..models.content_chunk import ContentChunk
from ...logger.logging_config import get_logger
from unstructured.partition.html import partition_html
from langchain.text_splitter import RecursiveCharacterTextSplitter

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
    def _is_heading(self, element: Tag) -> bool:
        """Check if an element is a heading tag."""
        return element.name in ["h1", "h2", "h3", "h4", "h5", "h6"]

    def _is_list(self, element: Tag) -> bool:
        """Check if an element is a list or list item."""
        return element.name in ["ul", "ol", "li"]

    def _is_table(self, element: Tag) -> bool:
        """Check if an element is a table or table-related element."""
        return element.name in ["table", "tr", "td", "th"]

    def _is_content_block(self, element: Tag) -> bool:
        """Check if an element is a main content block."""
        return (
            element.name in ["p", "article", "section", "div"]
            or self._is_heading(element)
            or self._is_list(element)
            or self._is_table(element)
        )

    def _format_chunk_content(self, heading: Optional[str], content: str) -> str:
        """Format chunk content with proper spacing and structure."""
        if heading:
            return f"{heading}\n\n{content}"
        return content

    def _extract_heading_text(self, element: Tag) -> Optional[str]:
        """Extract and clean heading text from an element."""
        if self._is_heading(element):
            return clean_text(element.text)
        return None

    def _process_list(self, element: Tag) -> str:
        """Process a list element and its items into formatted text."""
        if element.name == "li":
            return f"• {clean_text(element.text)}"

        items = []
        for li in element.find_all("li", recursive=False):
            items.append(f"• {clean_text(li.text)}")
        return "\n".join(items)

    def _process_table(self, element: Tag) -> str:
        """Process a table element into formatted text."""
        if element.name != "table":
            return clean_text(element.text)

        rows = []
        for tr in element.find_all("tr"):
            cells = [clean_text(td.text) for td in tr.find_all(["td", "th"])]
            rows.append(" | ".join(cells))
        return "\n".join(rows)

    def _process_element(self, element: Tag) -> Tuple[Optional[str], str]:
        """Process a single element and return its heading and content."""
        heading = self._extract_heading_text(element)

        if self._is_list(element):
            content = self._process_list(element)
        elif self._is_table(element):
            content = self._process_table(element)
        else:
            content = clean_text(element.text)

        return heading, content

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

        # Extract document title from title tag
        document_title = None
        title_match = re.search(
            r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            document_title = clean_text(title_match.group(1))
            logger.debug(f"Extracted document title: {document_title}")

        # Extract content using partition_html
        elements = partition_html(text=html_content)
        full_text = "\n".join([el.text for el in elements if hasattr(el, "text")])

        # Initialize text splitter with same parameters as reference implementation
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

        # Split text into chunks
        chunks = []
        seen_chunk_ids: Set[str] = set()
        chunk_count = 0

        for chunk_text in text_splitter.split_text(full_text):
            chunk_text = clean_text(chunk_text)

            # Skip very short chunks
            if len(chunk_text) < 20:
                logger.debug(f"Skipping short chunk: {chunk_text[:50]}...")
                continue

            # Generate chunk ID and check for duplicates
            chunk_id = hash_id(file_path.stem + chunk_text)
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
                text_content=chunk_text,
                document_title=document_title,
            )

            chunks.append(chunk)
            chunk_count += 1

        logger.info(f"Successfully parsed {chunk_count} chunks from {file_path}")
        return chunks
