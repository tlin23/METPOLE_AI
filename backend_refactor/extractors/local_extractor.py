import shutil
from pathlib import Path
from typing import List, Set
from .base import BaseExtractor


class LocalExtractor(BaseExtractor):
    def __init__(self, allowed_extensions: List[str] = None):
        """
        Initialize the LocalExtractor.

        Args:
            allowed_extensions: List of file extensions to process (e.g., ['.txt', '.pdf']).
                              If None, all files will be processed.
        """
        self.allowed_extensions = allowed_extensions
        self.processed_files: Set[Path] = set()

    def _is_allowed_extension(self, file_path: Path) -> bool:
        """Check if the file extension is in the allowed extensions list."""
        if not self.allowed_extensions:
            return True
        return file_path.suffix.lower() in self.allowed_extensions

    def _organize_by_extension(self, file_path: Path, output_dir: Path) -> Path:
        """Copy file to output directory, organized by extension."""
        # Create extension-specific subdirectory
        ext_dir = output_dir / file_path.suffix.lstrip(".")
        ext_dir.mkdir(parents=True, exist_ok=True)

        # Copy file to extension directory
        dest_path = ext_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        return dest_path

    def extract(self, input_path: Path, output_dir: Path) -> List[Path]:
        """
        Walk through the input directory and copy files to the output directory,
        organized by file extension.

        Args:
            input_path: Path to the input directory
            output_dir: Directory where files should be copied

        Returns:
            List of Path objects pointing to the copied files
        """
        if not input_path.exists():
            raise ValueError(f"Input path does not exist: {input_path}")

        if not input_path.is_dir():
            raise ValueError(f"Input path must be a directory: {input_path}")

        saved_files = []

        # Walk through the directory
        for file_path in input_path.rglob("*"):
            if file_path.is_file() and self._is_allowed_extension(file_path):
                try:
                    dest_path = self._organize_by_extension(file_path, output_dir)
                    saved_files.append(dest_path)
                    self.processed_files.add(file_path)
                except (IOError, OSError) as e:
                    print(f"Error processing {file_path}: {str(e)}")
                    continue

        return saved_files
