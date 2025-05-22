import pytest
from pathlib import Path
from backend_refactor.crawlers.local_crawler import LocalCrawler


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test output."""
    return tmp_path


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files for testing."""
    input_dir = temp_dir / "input"
    input_dir.mkdir()

    # Create files with different extensions
    (input_dir / "test1.txt").write_text("Content 1")
    (input_dir / "test2.txt").write_text("Content 2")
    (input_dir / "test3.pdf").write_text("Content 3")
    (input_dir / "test4.doc").write_text("Content 4")

    return input_dir


def test_local_crawler_initialization():
    """Test LocalCrawler initialization with and without allowed extensions."""
    # Test without allowed extensions
    crawler = LocalCrawler()
    assert crawler.allowed_extensions is None
    assert crawler.processed_files == set()

    # Test with allowed extensions
    extensions = [".txt", ".pdf"]
    crawler = LocalCrawler(allowed_extensions=extensions)
    assert crawler.allowed_extensions == extensions


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
