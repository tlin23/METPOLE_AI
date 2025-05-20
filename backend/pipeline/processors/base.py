from typing import Protocol, List, Dict, Any
from pathlib import Path


class DocumentProcessor(Protocol):
    """Interface for document processors."""

    def process(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process a document and return structured content blocks."""
        ...
