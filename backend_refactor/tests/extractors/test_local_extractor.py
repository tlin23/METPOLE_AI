import pytest
from pathlib import Path
from backend_refactor.extractors.local_extractor import LocalExtractor


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test output."""
    return tmp_path


@pytest.fixture
def sample_files(tmp_path):
    """Create a sample directory structure with test files."""
    # Create input directory structure
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    # Create subdirectory before writing into it
    subdir = input_dir / "subdir"
    subdir.mkdir()

    # Create test files
    (input_dir / "test1.txt").write_text("Content 1")
    (input_dir / "test2.pdf").write_text("Content 2")
    (input_dir / "test3.txt").write_text("Content 3")
    (subdir / "test4.pdf").write_text("Content 4")

    return input_dir


def test_local_extractor_initialization():
    """Test LocalExtractor initialization with and without allowed extensions."""
    # Test without allowed extensions
    extractor = LocalExtractor()
    assert extractor.allowed_extensions is None
    assert extractor.processed_files == set()

    # Test with allowed extensions
    extensions = [".txt", ".pdf"]
    extractor = LocalExtractor(allowed_extensions=extensions)
    assert extractor.allowed_extensions == extensions


def test_is_allowed_extension():
    """Test file extension filtering functionality."""
    extractor = LocalExtractor(allowed_extensions=[".txt", ".pdf"])

    assert extractor._is_allowed_extension(Path("test.txt"))
    assert extractor._is_allowed_extension(Path("test.PDF"))  # Case insensitive
    assert not extractor._is_allowed_extension(Path("test.doc"))

    # Test with no allowed extensions
    extractor = LocalExtractor()
    assert extractor._is_allowed_extension(Path("test.any"))


def test_organize_by_extension(temp_dir):
    """Test file organization by extension."""
    extractor = LocalExtractor()
    input_file = temp_dir / "test.txt"
    input_file.write_text("Test content")

    output_path = extractor._organize_by_extension(input_file, temp_dir / "output")

    assert output_path.exists()
    assert output_path.parent.name == "txt"
    assert output_path.read_text() == "Test content"


def test_extract_with_valid_directory(sample_files, temp_dir):
    """Test extraction from a valid directory."""
    extractor = LocalExtractor()
    output_dir = temp_dir / "output"

    saved_files = extractor.extract(sample_files, output_dir)

    assert len(saved_files) == 4
    assert len(extractor.processed_files) == 4

    # Check that files are organized by extension
    assert (output_dir / "txt").exists()
    assert (output_dir / "pdf").exists()
    assert len(list((output_dir / "txt").glob("*.txt"))) == 2
    assert len(list((output_dir / "pdf").glob("*.pdf"))) == 2


def test_extract_with_extension_filter(sample_files, temp_dir):
    """Test extraction with extension filtering."""
    extractor = LocalExtractor(allowed_extensions=[".txt"])
    output_dir = temp_dir / "output"

    saved_files = extractor.extract(sample_files, output_dir)

    assert len(saved_files) == 2
    assert all(f.suffix == ".txt" for f in saved_files)
    assert not (output_dir / "pdf").exists()


def test_extract_with_nonexistent_directory(temp_dir):
    """Test extraction with a nonexistent directory."""
    extractor = LocalExtractor()
    input_dir = temp_dir / "nonexistent"

    with pytest.raises(ValueError):
        extractor.extract(input_dir, temp_dir / "output")


def test_extract_with_file_instead_of_directory(temp_dir):
    """Test extraction with a file instead of a directory."""
    extractor = LocalExtractor()
    input_file = temp_dir / "test.txt"
    input_file.write_text("Test content")

    with pytest.raises(ValueError):
        extractor.extract(input_file, temp_dir / "output")
