from pathlib import Path
import re
import hashlib
from typing import List, Set
from pypdf import PdfReader
from ftfy import fix_text
from .base import BaseParser
from ..models.content_chunk import ContentChunk
from ..configer.logging_config import get_logger

logger = get_logger("parsers.pdf")


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


class PDFParser(BaseParser):
    def parse(self, file_path: Path) -> List[ContentChunk]:
        """
        Parse a PDF file and convert its contents into a list of ContentChunk objects.

        The parser:
        - Extracts meaningful content while preserving page structure
        - Handles text and metadata extraction
        - Cleans and normalizes text
        - Generates unique chunk IDs
        - Prevents duplicate chunks

        Args:
            file_path: Path to the PDF file to parse

        Returns:
            List of ContentChunk objects representing the parsed content

        Raises:
            ValueError: If the file is not a valid PDF file
            IOError: If the file cannot be read
        """
        logger.info(f"Starting to parse PDF file: {file_path}")

        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise IOError(error_msg)

        if file_path.suffix.lower() != ".pdf":
            error_msg = f"Not a PDF file: {file_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        try:
            chunks = []
            seen_chunk_ids: Set[str] = set()
            total_pages = 0
            processed_pages = 0
            chunk_count = 0

            with open(file_path, "rb") as file:
                # Create PDF reader with strict=False to handle some PDF errors
                pdf_reader = PdfReader(file, strict=False)
                total_pages = len(pdf_reader.pages)
                logger.info(f"PDF has {total_pages} pages")

                # Extract document title from metadata
                info = pdf_reader.metadata
                document_title = info.get("/Title", "") or file_path.stem
                logger.debug(f"Extracted document title: {document_title}")

                # Process each page
                for page_num, page in enumerate(pdf_reader.pages, 1):
                    try:
                        logger.debug(f"Processing page {page_num}/{total_pages}")
                        text = page.extract_text()
                        if not text:
                            logger.debug(f"No text content found on page {page_num}")
                            continue

                        # Split text into lines and treat each line as a potential paragraph
                        lines = [
                            line.strip() for line in text.split("\n") if line.strip()
                        ]

                        # If no lines found, try splitting on double newlines
                        if not lines:
                            paragraphs = [
                                p.strip() for p in text.split("\n\n") if p.strip()
                            ]
                            if paragraphs:
                                lines = paragraphs
                                logger.debug(
                                    f"Found {len(paragraphs)} paragraphs on page {page_num}"
                                )

                        for line in lines:
                            # Clean the line text
                            cleaned_line = clean_text(line)

                            # Skip very short chunks
                            if len(cleaned_line) < 20:
                                logger.debug(
                                    f"Skipping short chunk on page {page_num}: {cleaned_line[:50]}..."
                                )
                                continue

                            # Generate chunk ID and check for duplicates
                            chunk_id = hash_id(file_path.stem + cleaned_line)
                            if chunk_id in seen_chunk_ids:
                                logger.debug(
                                    f"Skipping duplicate chunk on page {page_num}: {chunk_id}"
                                )
                                continue
                            seen_chunk_ids.add(chunk_id)

                            # Create chunk
                            chunk = ContentChunk(
                                chunk_id=chunk_id,
                                file_name=file_path.stem,
                                file_ext=file_path.suffix[1:],
                                page_number=page_num,
                                text_content=cleaned_line,
                                document_title=document_title,
                            )
                            chunks.append(chunk)
                            chunk_count += 1

                        processed_pages += 1

                    except Exception as e:
                        error_msg = f"Failed to process page {page_num} in {file_path}: {str(e)}"
                        logger.error(error_msg)
                        continue

            if not chunks:
                warning_msg = f"No content extracted from {file_path}"
                logger.warning(warning_msg)
                return []

            logger.info(
                f"Successfully parsed {chunk_count} chunks from {processed_pages}/{total_pages} pages in {file_path}"
            )
            return chunks

        except Exception as e:
            error_msg = f"Failed to parse PDF file: {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
