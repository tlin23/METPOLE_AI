import time
import re
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader
from backend_legacy.configer.logging_config import get_logger

logger = get_logger("pipeline.processors.pdf")


def clean_text(text: str) -> str:
    """Clean and normalize extracted PDF text."""
    substitutions = {" n ": "n", " l ": "l", " t ": "t"}
    for old, new in substitutions.items():
        text = text.replace(old, new)
    text = " ".join(text.split())

    # Merge isolated single-letter words
    merged = []
    for word in text.split():
        if len(word) == 1 and merged and len(merged[-1]) == 1:
            merged[-1] += word
        else:
            merged.append(word)
    return " ".join(merged).strip()


def is_tabular(
    text: str,
    dash_threshold: float = 0.07,
    min_dash_lines: int = 3,
) -> bool:
    """
    Strong tabular detection for financial statements.
    Flags as tabular if:
      - High dash/underline density (dashes, '¯', etc)
      - OR (previous signals: high numeric, low stopword, short lines)
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    dash_like = "-–¯—"
    dash_chars = sum(1 for c in text if c in dash_like)
    dash_ratio = dash_chars / max(1, len(text))
    dash_lines = [line for line in lines if sum(c in dash_like for c in line) >= 3]
    if dash_ratio > dash_threshold or len(dash_lines) >= min_dash_lines:
        return True

    stopwords = set(
        (
            "the",
            "and",
            "for",
            "with",
            "that",
            "this",
            "from",
            "but",
            "are",
            "was",
            "have",
            "not",
            "you",
            "all",
            "any",
            "can",
            "had",
            "her",
            "his",
            "one",
            "our",
            "out",
            "she",
            "who",
            "has",
            "were",
            "your",
            "they",
            "will",
            "their",
            "as",
            "of",
            "on",
            "in",
            "by",
            "is",
            "or",
            "to",
            "at",
            "it",
            "be",
            "an",
            "if",
        )
    )
    tokens = re.findall(r"\b[\w\-\.\$,\(\)%]+\b", text)
    num_tokens = sum(1 for t in tokens if re.fullmatch(r"[\d\-,\.\$\(\)%]+", t))
    stopword_count = sum(1 for t in tokens if t.lower() in stopwords)
    num_ratio = num_tokens / len(tokens) if tokens else 0
    stopword_ratio = stopword_count / len(tokens) if tokens else 0
    short_lines = sum(1 for line in lines if len(line.split()) < 6)
    short_line_ratio = short_lines / len(lines) if lines else 0

    table_signals = 0
    if num_ratio > 0.37 and stopword_ratio < 0.09:
        table_signals += 1
    if short_line_ratio > 0.6:
        table_signals += 1

    return table_signals >= 2


class PDFProcessor:
    """Processes PDF documents into structured content."""

    def process(self, file_path: Path) -> List[Dict[str, Any]]:
        logger.info(f"Processing PDF: {file_path.name}")
        start = time.time()
        try:
            reader = PdfReader(file_path)
            logger.info(f"{len(reader.pages)} pages found.")
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return []

        structured = [
            {
                "section": "Document Properties",
                "type": "metadata",
                "content": str(reader.metadata or {}),
            }
        ]

        # Check for "Financial Summary" on the first page
        first_page_text = reader.pages[0].extract_text() or ""
        if "Financial Summary" in first_page_text:
            logger.info('"Financial Summary" detected, only extracting page 1')
            cleaned = clean_text(first_page_text)
            if cleaned:
                structured.append(
                    {
                        "section": "Page 1",
                        "type": "text",
                        "content": cleaned,
                    }
                )
            logger.info(f"Finished processing in {time.time() - start:.2f}s")
            return structured

        # Otherwise: process all pages, skipping tables
        for i, page in enumerate(reader.pages):
            raw = page.extract_text() or ""
            if is_tabular(raw):
                logger.info(f"Skipped page {i + 1}: Detected tabular data.")
                continue
            cleaned = clean_text(raw)
            if cleaned:
                structured.append(
                    {
                        "section": f"Page {i + 1}",
                        "type": "text",
                        "content": cleaned,
                    }
                )

        logger.info(f"Finished processing in {time.time() - start:.2f}s")
        return structured
