from pathlib import Path
from typing import List
from .base import BaseParser
from ..models.content_chunk import ContentChunk


class HTMLParser(BaseParser):
    def parse(self, file_path: Path) -> List[ContentChunk]:
        """
        Parse an HTML file and convert its contents into a list of ContentChunk objects.

        Args:
            file_path: Path to the HTML file to parse

        Returns:
            List of ContentChunk objects representing the parsed content

        Raises:
            ValueError: If the file is not a valid HTML file
            IOError: If the file cannot be read
        """
        raise NotImplementedError("HTMLParser.parse() is not yet implemented")
