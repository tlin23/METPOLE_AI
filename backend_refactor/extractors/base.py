from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, input_path: Path, output_dir: Path) -> List[Path]:
        """
        Extract content from the input path and save it to the output directory.

        Args:
            input_path: Path to the input source (URL or local directory)
            output_dir: Directory where extracted content should be saved

        Returns:
            List of Path objects pointing to the extracted files
        """
        raise NotImplementedError("Subclasses must implement extract()")
