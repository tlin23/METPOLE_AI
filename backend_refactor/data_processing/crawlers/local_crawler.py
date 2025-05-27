import shutil
from pathlib import Path
from typing import List, Set
from .base_crawler import BaseCrawler
from ..logger.logging_config import get_logger

logger = get_logger("crawlers.local")


class LocalCrawler(BaseCrawler):
    def __init__(self, allowed_extensions: List[str] = None):
        """
        Initialize the LocalCrawler.

        Args:
            allowed_extensions: List of file extensions to process (e.g., ['.txt', '.pdf']).
                              If None, all files will be processed.
        """
        super().__init__(allowed_extensions)
        self.processed_files: Set[Path] = set()
        if allowed_extensions:
            logger.info(f"Initialized with allowed extensions: {allowed_extensions}")
        else:
            logger.info("Initialized with no extension restrictions")

    def _is_allowed_extension(self, file_path: Path) -> bool:
        """Check if the file extension is in the allowed extensions list."""
        return self._is_allowed(file_path.suffix.lower())

    def _organize_by_extension(self, file_path: Path, output_dir: Path) -> Path:
        """Copy file to output directory, organized by extension."""
        # Create extension-specific subdirectory
        ext_dir = output_dir / file_path.suffix.lstrip(".")
        ext_dir.mkdir(parents=True, exist_ok=True)

        # Copy file to extension directory
        dest_path = ext_dir / file_path.name
        shutil.copy2(file_path, dest_path)
        logger.debug(f"Copied {file_path} to {dest_path}")
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
        logger.info(f"Starting local file crawl from {input_path}")

        if not input_path.exists():
            error_msg = f"Input path does not exist: {input_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        if not input_path.is_dir():
            error_msg = f"Input path must be a directory: {input_path}"
            logger.error(error_msg)
            raise NotADirectoryError(error_msg)

        saved_files = []
        skipped_files = 0

        # Walk through the directory
        for file_path in input_path.rglob("*"):
            if file_path.is_file():
                if self._is_allowed_extension(file_path):
                    try:
                        dest_path = self._organize_by_extension(file_path, output_dir)
                        saved_files.append(dest_path)
                        self.processed_files.add(file_path)
                    except (IOError, OSError) as e:
                        logger.error(f"Error processing {file_path}: {str(e)}")
                        continue
                else:
                    logger.debug(
                        f"Skipping file with disallowed extension: {file_path}"
                    )
                    skipped_files += 1

        logger.info(
            f"Local crawl complete. Processed {len(saved_files)} files, skipped {skipped_files} files."
        )
        return saved_files
