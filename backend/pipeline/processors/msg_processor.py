from pathlib import Path
from typing import List, Dict, Any
from backend.configer.logging_config import get_logger

logger = get_logger("pipeline.processors.msg")


class MSGProcessor:
    """Processor for MSG (Outlook) documents."""

    def process(self, file_path: Path) -> List[Dict[str, Any]]:
        """Process an MSG document."""
        logger.info(f"Processing MSG: {file_path.name}")
        # TODO: Implement MSG processing
        # This should extract:
        # - Email subject
        # - Sender/recipient information
        # - Email body
        # - Attachments
        return []
