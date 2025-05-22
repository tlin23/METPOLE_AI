from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..models.content_chunk import ContentChunk


class BaseParser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> List[ContentChunk]:
        """
        Parse a file and convert its contents into a list of ContentChunk objects.

        Args:
            file_path: Path to the file to parse

        Returns:
            List of ContentChunk objects representing the parsed content

        Raises:
            NotImplementedError: This method must be implemented by subclasses
            ValueError: If the file cannot be parsed
            IOError: If the file cannot be read
        """
        raise NotImplementedError("Subclasses must implement parse()")
