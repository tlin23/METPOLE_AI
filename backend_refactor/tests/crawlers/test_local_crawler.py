import pytest
from pathlib import Path
from backend_refactor.crawlers.local_crawler import LocalCrawler


def test_local_crawler_initialization():
    """Test LocalCrawler initialization with and without allowed extensions."""
    # Test without allowed extensions
    crawler = LocalCrawler()
    assert crawler.allowed_patterns is None
    assert crawler.processed_files == set()

    # Test with allowed extensions
    extensions = [".txt", ".pdf"]
    crawler = LocalCrawler(allowed_extensions=extensions)
    assert crawler.allowed_patterns == extensions


def test_is_allowed_extension():
    """Test extension filtering functionality."""
    crawler = LocalCrawler(allowed_extensions=[".txt", ".pdf"])

    assert crawler._is_allowed_extension(Path("test.txt"))
    assert crawler._is_allowed_extension(Path("test.PDF"))  # Case insensitive
    assert not crawler._is_allowed_extension(Path("test.doc"))

    # Test with no allowed extensions
    crawler = LocalCrawler()
    assert crawler._is_allowed_extension(Path("test.any"))


def test_organize_by_extension(temp_dir):
    """Test file organization by extension."""
    crawler = LocalCrawler()
    input_file = temp_dir / "test.txt"
    input_file.write_text("Test content")

    output_path = crawler._organize_by_extension(input_file, temp_dir / "output")

    assert output_path.exists()
    assert output_path.name == "test.txt"
    assert output_path.read_text() == "Test content"


def test_extract_all_files(sample_files, temp_dir):
    """Test extraction of all files."""
    crawler = LocalCrawler()
    output_dir = temp_dir / "output"

    saved_files = crawler.extract(sample_files, output_dir)

    assert len(saved_files) == 4
    assert len(crawler.processed_files) == 4


def test_extract_with_extension_filter(sample_files, temp_dir):
    """Test extraction with extension filtering."""
    crawler = LocalCrawler(allowed_extensions=[".txt"])
    output_dir = temp_dir / "output"

    saved_files = crawler.extract(sample_files, output_dir)

    assert len(saved_files) == 2
    assert all(f.suffix == ".txt" for f in saved_files)


def test_extract_nonexistent_directory(temp_dir):
    """Test extraction with nonexistent directory."""
    crawler = LocalCrawler()
    input_dir = temp_dir / "nonexistent"

    with pytest.raises(FileNotFoundError):
        crawler.extract(input_dir, temp_dir / "output")


def test_extract_single_file(temp_dir):
    """Test extraction of a single file."""
    crawler = LocalCrawler()
    input_file = temp_dir / "test.txt"
    input_file.write_text("Test content")

    with pytest.raises(NotADirectoryError):
        crawler.extract(input_file, temp_dir / "output")


def test_extract_complex_directory_structure(test_directory_structure, temp_dir):
    """Test extraction from a complex directory structure with various file types."""
    crawler = LocalCrawler(allowed_extensions=[".html", ".pdf", ".docx", ".txt"])
    output_dir = temp_dir / "output"

    saved_files = crawler.extract(test_directory_structure, output_dir)

    # Should find all files with allowed extensions
    assert len(saved_files) == 4  # index.html, config.txt, manual.pdf, guide.docx
    assert len(crawler.processed_files) == 4

    # Verify file types
    extensions = {f.suffix.lower() for f in saved_files}
    assert extensions == {".html", ".txt", ".pdf", ".docx"}

    # Verify content preservation
    for saved_file in saved_files:
        # Find the original file by walking through the test directory structure
        original_file = None
        for path in test_directory_structure.rglob(saved_file.name):
            if path.is_file():
                original_file = path
                break

        assert (
            original_file is not None
        ), f"Could not find original file for {saved_file.name}"
        assert saved_file.read_bytes() == original_file.read_bytes()
