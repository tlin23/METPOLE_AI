from pathlib import Path
import re
import hashlib
from typing import List, Set, Optional, Protocol, Dict
from bs4 import Tag, BeautifulSoup
from ftfy import fix_text
from .base import BaseParser
from ..models.content_chunk import ContentChunk
from ...logger.logging_config import get_logger

logger = get_logger("parsers.html")

# Common boilerplate patterns to remove
BOILERPLATE_PATTERNS = [
    r"Search this site",
    r"Embedded Files",
    r"Google Sites Report abuse",
    r"Contact Webmaster",
    r"Copyright \d{4} Metropole Condominium Association",
    r"Navigation",
    r"Footer",
    r"Header",
    r"Menu",
    r"Sidebar",
]


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


def is_boilerplate(text: str) -> bool:
    """Check if text matches any boilerplate patterns."""
    text = text.lower()
    return any(re.search(pattern.lower(), text) for pattern in BOILERPLATE_PATTERNS)


class ExtractionStrategy(Protocol):
    """Protocol defining the interface for HTML extraction strategies."""

    def extract_chunks(
        self, soup: BeautifulSoup, file_path: Path, document_title: Optional[str]
    ) -> List[ContentChunk]:
        """Extract chunks from HTML content."""
        ...


class HeadingHierarchyStrategy:
    """Strategy that extracts content based on heading hierarchy."""

    def _get_heading_level(self, tag: Tag) -> int:
        """Get the heading level from a heading tag (h1-h6)."""
        if not tag.name or not tag.name.startswith("h"):
            return 0
        try:
            return int(tag.name[1])
        except ValueError:
            return 0

    def _get_heading_path(self, current_tag: Tag) -> List[str]:
        """Get the full path of headings leading to the current tag."""
        path = []
        current = current_tag
        while current:
            if current.name and current.name.startswith("h"):
                path.append(clean_text(current.text))
            current = current.find_previous_sibling()
        return list(reversed(path))

    def _extract_content_until_next_heading(
        self, start_tag: Tag, current_level: int
    ) -> str:
        """Extract content until the next heading of same or higher level."""
        content = []
        current = start_tag.next_sibling

        while current:
            if isinstance(current, Tag):
                if current.name and current.name.startswith("h"):
                    next_level = self._get_heading_level(current)
                    if next_level <= current_level:
                        break
                content.append(clean_text(current.text))
            current = current.next_sibling

        return " ".join(filter(None, content))

    def _process_preamble(self, soup: BeautifulSoup) -> Optional[str]:
        """Process any content before the first heading as a preamble chunk."""
        # First check if there are any headings in the document
        if not soup.find(["h1", "h2", "h3", "h4", "h5", "h6"]):
            return None

        preamble = []
        # Start from the body tag
        body = soup.find("body")
        if not body:
            return None

        # Process all elements until we find a heading
        for element in body.children:
            if isinstance(element, Tag):
                if element.name and element.name.startswith("h"):
                    break
                if element.name in ["p", "div", "section"]:
                    text = clean_text(element.text)
                    if text and not is_boilerplate(text):
                        preamble.append(text)

        return " ".join(preamble) if preamble else None

    def extract_chunks(
        self, soup: BeautifulSoup, file_path: Path, document_title: Optional[str]
    ) -> List[ContentChunk]:
        """Extract chunks using heading hierarchy strategy."""
        chunks = []
        seen_chunk_ids: Set[str] = set()

        # Process preamble if it exists
        preamble = self._process_preamble(soup)
        if preamble:
            chunk_id = hash_id(file_path.stem + preamble)
            if chunk_id not in seen_chunk_ids:
                chunks.append(
                    ContentChunk(
                        chunk_id=chunk_id,
                        file_name=file_path.stem,
                        file_ext=file_path.suffix[1:],
                        page_number=1,
                        text_content=f"Preamble\n{preamble}",
                        document_title=document_title,
                    )
                )
                seen_chunk_ids.add(chunk_id)

        # Process all headings and their content
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_path = self._get_heading_path(heading)
            content = self._extract_content_until_next_heading(
                heading, self._get_heading_level(heading)
            )

            if not content.strip():
                continue

            # Format chunk content with full heading path
            chunk_text = "\n".join(heading_path) + "\n" + content
            chunk_id = hash_id(file_path.stem + chunk_text)

            if chunk_id not in seen_chunk_ids:
                chunks.append(
                    ContentChunk(
                        chunk_id=chunk_id,
                        file_name=file_path.stem,
                        file_ext=file_path.suffix[1:],
                        page_number=1,
                        text_content=chunk_text,
                        document_title=document_title,
                    )
                )
                seen_chunk_ids.add(chunk_id)

        return chunks


class BackupStrategy:
    """Strategy that extracts content based on the backup parser's logic."""

    def _extract_chunks(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract logical chunks from HTML content based on heading hierarchy."""
        chunks = []
        current_chunk = None
        current_level = 0
        preamble_content = []

        # Process all elements in order
        for element in soup.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "table"]
        ):
            # Handle preamble content (before first heading)
            if not current_chunk and element.name.startswith("h"):
                if preamble_content:
                    preamble_text = " ".join(preamble_content)
                    if (
                        not is_boilerplate(preamble_text)
                        and len(preamble_text.strip()) > 0
                    ):
                        chunks.append({"header": "Preamble", "content": preamble_text})
                preamble_content = []

            # Handle headings
            if element.name.startswith("h"):
                heading_level = int(element.name[1])
                heading_text = clean_text(element.text)

                # Skip boilerplate headings
                if is_boilerplate(heading_text):
                    continue

                # If we find a heading of same or higher level, start new chunk
                if current_chunk and heading_level <= current_level:
                    if current_chunk["content"].strip():
                        chunks.append(current_chunk)
                    current_chunk = None

                # Start new chunk
                if not current_chunk:
                    current_chunk = {
                        "header": heading_text,
                        "content": heading_text + "\n",
                    }
                    current_level = heading_level

            # Handle content elements
            elif current_chunk:
                element_text = clean_text(element.text)
                if not is_boilerplate(element_text) and element_text.strip():
                    current_chunk["content"] += element_text + "\n"
            else:
                # Content before first heading
                element_text = clean_text(element.text)
                if not is_boilerplate(element_text) and element_text.strip():
                    preamble_content.append(element_text)

        # Add the last chunk if it exists
        if current_chunk and current_chunk["content"].strip():
            chunks.append(current_chunk)

        # If we have preamble content and no chunks were created (no headings case)
        if preamble_content and not chunks:
            preamble_text = " ".join(preamble_content)
            if not is_boilerplate(preamble_text) and len(preamble_text.strip()) > 0:
                chunks.append({"header": "Content", "content": preamble_text})

        return chunks

    def extract_chunks(
        self, soup: BeautifulSoup, file_path: Path, document_title: Optional[str]
    ) -> List[ContentChunk]:
        """Extract chunks using backup strategy."""
        chunks_data = self._extract_chunks(soup)
        chunks = []
        seen_chunk_ids: Set[str] = set()

        for chunk_data in chunks_data:
            chunk_text = chunk_data["content"].strip()

            # Skip empty or very short chunks
            if len(chunk_text) < 10:
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

        return chunks


class UnifiedHTMLParser(BaseParser):
    """Unified HTML parser that uses multiple strategies in a fallback pattern."""

    def __init__(self):
        """Initialize the parser with ordered strategies."""
        self.strategies = [
            HeadingHierarchyStrategy(),
            BackupStrategy(),
        ]

    def parse(self, file_path: Path) -> List[ContentChunk]:
        """
        Parse an HTML file using multiple strategies in order until one succeeds.

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

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            error_msg = f"Error reading file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise IOError(error_msg)

        # Extract document title
        document_title = None
        title_match = re.search(
            r"<title>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
        )
        if title_match:
            document_title = clean_text(title_match.group(1))
            logger.debug(f"Extracted document title: {document_title}")

        soup = BeautifulSoup(html_content, "html.parser")
        chunks = []

        # Try each strategy in order
        for i, strategy in enumerate(self.strategies):
            strategy_name = strategy.__class__.__name__
            logger.info(f"Trying {strategy_name} strategy for {file_path}")

            chunks = strategy.extract_chunks(soup, file_path, document_title)

            if chunks:
                logger.info(
                    f"Successfully extracted {len(chunks)} chunks using {strategy_name}"
                )
                return chunks

            logger.info(f"No chunks found with {strategy_name}")

        # If no strategy succeeded
        logger.warning(f"No chunks found with any strategy for {file_path}")
        return []
