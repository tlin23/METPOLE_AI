import time
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
from backend.configer.logging_config import get_logger

logger = get_logger("pipeline.processors.pdf")


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # First, normalize spaces between words
    # This handles cases where PDF extraction adds spaces within words
    text = text.replace(" n ", "n")  # Handle common cases like "conti n gencies"
    text = text.replace(" l ", "l")  # Handle cases like "l eave"
    text = text.replace(" t ", "t")  # Handle cases like "t ime"

    # Then normalize all whitespace
    text = " ".join(text.split())

    # Remove any remaining single spaces between letters
    # This is a more aggressive approach that might need tuning
    words = text.split()
    cleaned_words = []
    for word in words:
        if len(word) == 1 and cleaned_words and len(cleaned_words[-1]) == 1:
            # If we have two single letters, combine them
            cleaned_words[-1] += word
        else:
            cleaned_words.append(word)

    return " ".join(cleaned_words).strip()


class PDFProcessor:
    """Processor for PDF documents."""

    def process(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a PDF document and return structured content blocks."""
        logger.info(f"Starting to process PDF file: {file_path.name}")
        start_time = time.time()

        try:
            # Load document
            logger.debug(f"Loading document: {file_path}")
            reader = PdfReader(file_path)
            logger.info(
                f"Document loaded successfully. Found {len(reader.pages)} pages"
            )

            # Extract content
            structured_blocks = []
            current_section = "Document Content"
            logger.debug(f"Initial section set to: {current_section}")

            # Add document properties
            logger.debug("Extracting document properties")
            properties = self._extract_document_properties(reader)
            if properties:
                logger.info("Document properties extracted successfully")
                structured_blocks.append(
                    {
                        "type": "properties",
                        "section": "Document Properties",
                        "content": properties,
                    }
                )

            # Process main content
            logger.debug("Starting to process main content")
            element_count = {"pages": 0, "paragraphs": 0}

            # Process each page
            for page_num, page in enumerate(reader.pages, 1):
                element_count["pages"] += 1
                logger.debug(f"Processing page {page_num}")

                # Extract text from page
                text = page.extract_text()
                if not text:
                    logger.debug(f"No text found on page {page_num}")
                    continue

                # Split into paragraphs (simple split by double newlines)
                paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
                element_count["paragraphs"] += len(paragraphs)

                # Process each paragraph
                for paragraph in paragraphs:
                    # Clean and normalize text
                    text = clean_text(paragraph)
                    if not text:
                        continue

                    # Check if paragraph might be a heading (simple heuristic)
                    if self._is_heading(text):
                        current_section = text
                        logger.debug(f"Found potential heading: {current_section}")
                        continue

                    # Add paragraph as content block
                    structured_blocks.append(
                        {"type": "text", "section": current_section, "content": text}
                    )

            # Log processing summary
            logger.info("Document processing completed successfully")
            logger.info("Processing summary:")
            logger.info(f"- Total pages processed: {element_count['pages']}")
            logger.info(f"- Total paragraphs found: {element_count['paragraphs']}")
            logger.info(f"- Total content blocks created: {len(structured_blocks)}")
            logger.info(f"Processing took {time.time() - start_time:.2f} seconds")

            return structured_blocks

        except Exception as e:
            logger.error(
                f"Error processing document {file_path}: {str(e)}", exc_info=True
            )
            raise

    def _is_heading(self, text: str) -> bool:
        """Check if text might be a heading using simple heuristics."""
        # Check if text is short (less than 100 chars)
        if len(text) > 100:
            return False

        # Check if text ends with a period
        if text.endswith("."):
            return False

        # Check if text is all caps
        if text.isupper():
            return True

        # Check if text starts with common heading patterns
        heading_patterns = [
            "chapter",
            "section",
            "part",
            "appendix",
            "introduction",
            "conclusion",
            "references",
            "abstract",
            "summary",
            "overview",
        ]
        text_lower = text.lower()
        return any(text_lower.startswith(pattern) for pattern in heading_patterns)

    def _extract_document_properties(self, reader: PdfReader) -> Dict[str, Any]:
        """Extract basic document properties."""
        logger.debug("Starting document properties extraction")
        properties = {}

        # Get document metadata
        metadata = reader.metadata
        if metadata:
            if metadata.title:
                properties["title"] = metadata.title
                logger.debug(f"Found title: {metadata.title}")
            if metadata.author:
                properties["author"] = metadata.author
                logger.debug(f"Found author: {metadata.author}")
            if metadata.creation_date:
                properties["created"] = metadata.creation_date.isoformat()
                logger.debug(f"Found creation date: {metadata.creation_date}")
            if metadata.modification_date:
                properties["modified"] = metadata.modification_date.isoformat()
                logger.debug(f"Found modification date: {metadata.modification_date}")

        # Document statistics
        properties["statistics"] = {
            "pages": len(reader.pages),
            "encrypted": reader.is_encrypted,
        }
        logger.debug(f"Document statistics: {properties['statistics']}")

        return properties
