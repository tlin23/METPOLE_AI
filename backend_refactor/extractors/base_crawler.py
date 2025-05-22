from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseCrawler(ABC):
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
