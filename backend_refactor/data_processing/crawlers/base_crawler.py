from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Set, Optional
import shutil
from ...logger.logging_config import get_logger

logger = get_logger("crawlers.base")


class BaseCrawler(ABC):
    def __init__(self, allowed_patterns: Optional[List[str]] = None):
        """
        Initialize the BaseCrawler.

        Args:
            allowed_patterns: List of patterns to filter content (e.g., file extensions or domains)
        """
        self.allowed_patterns = allowed_patterns
        self.processed_items: Set[str] = set()
        if allowed_patterns:
            logger.info(f"Initialized with allowed patterns: {allowed_patterns}")
        else:
            logger.info("Initialized with no pattern restrictions")

    def _is_allowed(self, item: str) -> bool:
        """Check if the item matches allowed patterns."""
        if not self.allowed_patterns:
            return True
        return any(item.endswith(pattern) for pattern in self.allowed_patterns)

    def _organize_by_type(
        self, item_path: Path, output_dir: Path, type_dir: str
    ) -> Path:
        """Organize content into type-specific subdirectory."""
        type_dir = output_dir / type_dir
        type_dir.mkdir(parents=True, exist_ok=True)

        dest_path = type_dir / item_path.name
        if isinstance(item_path, Path) and item_path.exists():
            shutil.copy2(item_path, dest_path)
            logger.debug(f"Copied {item_path} to {dest_path}")
        return dest_path

    def _clean_output_dir(self, output_dir: Path) -> None:
        """Clean the output directory if it exists."""
        if output_dir.exists():
            logger.info(f"Cleaning output directory: {output_dir}")
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)
        logger.debug(f"Created output directory: {output_dir}")

    @abstractmethod
    def extract(self, input_path: Path, output_dir: Path) -> List[Path]:
        """
        Extract content from input_path and save to output_dir.

        Args:
            input_path: Path to input file or directory
            output_dir: Directory where extracted content should be saved

        Returns:
            List of Path objects pointing to the extracted files
        """
        pass
