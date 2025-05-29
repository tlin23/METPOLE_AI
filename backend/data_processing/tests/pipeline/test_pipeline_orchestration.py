import json
import pytest
from pathlib import Path
from unittest.mock import patch, Mock
from backend.data_processing.pipeline.pipeline_orchestration import (
    crawl_content,
    parse_files,
    embed_chunks_from_dir,
    run_pipeline,
    _save_chunks_to_json,
    _save_error_to_json,
    _process_single_file,
    _is_valid_url,
    sort_files,
)
from backend.data_processing.pipeline.directory_utils import get_step_dir
from backend.data_processing.models.content_chunk import ContentChunk


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test output."""
    return tmp_path


@pytest.fixture
def sample_chunks():
    """Create sample content chunks for testing."""
    return [
        ContentChunk(
            chunk_id="chunk_1",
            file_name="test1",
            file_ext=".html",
            page_number=1,
            text_content="Test content 1",
        ),
        ContentChunk(
            chunk_id="chunk_2",
            file_name="test2",
            file_ext=".html",
            page_number=1,
            text_content="Test content 2",
        ),
    ]


@pytest.fixture
def mock_parser_class():
    """Create a mock parser class for testing."""

    class MockParserClass:
        def __init__(self):
            pass

        def parse(self, file_path):
            return [
                ContentChunk(
                    chunk_id="chunk_1",
                    file_name="test",
                    file_ext=".html",
                    page_number=1,
                    text_content="Test content",
                )
            ]

    return MockParserClass


@pytest.fixture
def parser_map_patch(mock_parser_class):
    """Create a patch for PARSER_MAP with mock parser."""
    return patch(
        "backend.data_processing.pipeline.pipeline_orchestration.PARSER_MAP",
        {".html": mock_parser_class},
    )


@pytest.fixture
def test_html_file(temp_dir):
    """Create a test HTML file."""
    file_path = temp_dir / "test.html"
    file_path.write_text("<html>Test</html>")
    return file_path


def test_get_output_subdir():
    """Test output subdirectory generation."""
    base_dir = Path("/test/output")

    # Test dev mode
    dev_dir = get_step_dir(base_dir, "crawl", False)
    assert dev_dir == Path("/test/output/dev/local_input_source")

    # Test prod mode
    prod_dir = get_step_dir(base_dir, "parse", True)
    assert prod_dir == Path("/test/output/prod/json_chunks")


def test_save_chunks_to_json(temp_dir, sample_chunks):
    """Test saving chunks to JSON file."""
    output_path = temp_dir / "test.json"
    _save_chunks_to_json(sample_chunks, output_path)

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["chunk_id"] == "chunk_1"
        assert data[1]["chunk_id"] == "chunk_2"


def test_save_error_to_json(temp_dir):
    """Test saving error message to JSON file."""
    output_path = temp_dir / "error.json"
    error_msg = "Test error message"
    _save_error_to_json(error_msg, output_path)

    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
        assert data["error"] == error_msg


def test_process_single_file(temp_dir, test_html_file, parser_map_patch):
    """Test processing a single file."""
    with parser_map_patch:
        output_path = _process_single_file(test_html_file, temp_dir)
        assert output_path is not None
        assert output_path.exists()
        assert output_path.suffix == ".json"


def test_is_valid_url():
    """Test URL validation."""
    # Valid URLs
    assert _is_valid_url("https://example.com")
    assert _is_valid_url("http://localhost:8000")
    assert _is_valid_url("http://example.com/path?query=value")

    # Invalid URLs
    assert not _is_valid_url("not-a-url")
    assert not _is_valid_url("ftp://example.com")  # Only http/https supported
    assert not _is_valid_url("file:///path/to/file")
    assert not _is_valid_url("")
    assert not _is_valid_url("http://")  # Missing domain


@patch("backend.data_processing.pipeline.pipeline_orchestration.WebCrawler")
def test_crawl_content_web(mock_web_crawler, temp_dir):
    """Test web content crawling."""
    mock_crawler = Mock()
    mock_crawler.extract.return_value = [temp_dir / "test.html"]
    mock_web_crawler.return_value = mock_crawler

    files, errors = crawl_content(
        input_source="https://example.com",
        output_dir=temp_dir,
        allowed_domains=["example.com"],
    )

    assert len(files) == 1
    assert len(errors) == 0
    mock_web_crawler.assert_called_once_with(allowed_domains=["example.com"])


@patch("backend.data_processing.pipeline.pipeline_orchestration.LocalCrawler")
def test_sort_files_local(mock_local_crawler, temp_dir):
    """Test local file sorting."""
    mock_crawler = Mock()
    mock_crawler.extract.return_value = [temp_dir / "test.html"]
    mock_local_crawler.return_value = mock_crawler

    # Create test file
    test_file = temp_dir / "test.html"
    test_file.write_text("<html>Test</html>")

    files, errors = sort_files(
        input_dir=temp_dir,
        output_dir=temp_dir,
    )

    assert len(files) == 1
    assert len(errors) == 0
    mock_local_crawler.assert_called_once_with(
        allowed_extensions=[".pdf", ".docx", ".html"]
    )


def test_parse_files(temp_dir, parser_map_patch):
    """Test file parsing."""
    with parser_map_patch:
        # Create test files
        input_dir = temp_dir / "input"
        input_dir.mkdir()
        (input_dir / "test1.html").write_text("<html>Test 1</html>")
        (input_dir / "test2.html").write_text("<html>Test 2</html>")

        output_paths, errors = parse_files(
            input_dir=input_dir,
            output_dir=temp_dir,
            n_limit=1,
        )

        assert len(output_paths) == 1
        assert len(errors) == 0
        assert output_paths[0].suffix == ".json"


@patch("backend.data_processing.pipeline.pipeline_orchestration.clean_pipeline")
@patch("backend.data_processing.pipeline.pipeline_orchestration.embed_chunks")
def test_embed_chunks_from_dir(mock_embed_chunks, mock_clean_pipeline, temp_dir):
    """Test chunk embedding."""
    # Create test JSON files
    input_dir = temp_dir / "input"
    input_dir.mkdir()
    (input_dir / "test1.json").write_text(
        '{"chunk_id": "chunk_1", "content": "Test 1"}'
    )
    (input_dir / "test2.json").write_text(
        '{"chunk_id": "chunk_2", "content": "Test 2"}'
    )

    # Create output directory
    output_dir = temp_dir / "dev" / "chroma_db"
    output_dir.mkdir(parents=True, exist_ok=True)

    n_embedded, errors = embed_chunks_from_dir(
        input_dir=input_dir,
        output_dir=temp_dir,
        collection_name="test_collection",
        n_limit=1,
    )

    assert n_embedded == 1
    assert len(errors) == 0

    # Verify that embed_chunks was called with correct arguments
    mock_embed_chunks.assert_called_once_with(
        [input_dir / "test1.json"],  # Only first file due to n_limit=1
        "test_collection",
        output_dir,
    )

    # Verify that clean_pipeline was called with correct arguments
    mock_clean_pipeline.assert_called_once_with(temp_dir, "embed", False)


@patch("backend.data_processing.pipeline.pipeline_orchestration.clean_pipeline")
@patch("backend.data_processing.pipeline.pipeline_orchestration.crawl_content")
@patch("backend.data_processing.pipeline.pipeline_orchestration.sort_files")
@patch("backend.data_processing.pipeline.pipeline_orchestration.parse_files")
@patch("backend.data_processing.pipeline.pipeline_orchestration.embed_chunks_from_dir")
def test_run_pipeline(
    mock_embed_chunks, mock_parse, mock_sort, mock_crawl, mock_clean, temp_dir
):
    """Test full pipeline execution."""
    # Create necessary directories
    crawl_dir = temp_dir / "dev" / "local_input_source"
    sort_dir = temp_dir / "dev" / "sorted_documents"
    parse_dir = temp_dir / "dev" / "json_chunks"
    embed_dir = temp_dir / "dev" / "chroma_db"

    for dir_path in [crawl_dir, sort_dir, parse_dir, embed_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Mock crawl output
    mock_crawl.return_value = ([temp_dir / "test.html"], [])

    # Mock sort output
    mock_sort.return_value = ([temp_dir / "test.html"], [])

    # Mock parse output
    mock_parse.return_value = ([temp_dir / "test.json"], [])

    # Mock embed output
    mock_embed_chunks.return_value = (1, [])

    result = run_pipeline(
        input_source="https://example.com",
        output_dir=temp_dir,
        collection_name="test_collection",
        allowed_domains=["example.com"],
    )

    assert "output_dir" in result
    assert "crawled_files" in result
    assert "sorted_files" in result
    assert "parsed_files" in result
    assert "embedded_files" in result

    # Verify that all steps were called in the correct order
    mock_clean.assert_called_once_with(temp_dir, "crawl", False)
    mock_crawl.assert_called_once()
    mock_sort.assert_called_once()
    mock_parse.assert_called_once()
    mock_embed_chunks.assert_called_once()


def test_crawl_content_invalid_input(temp_dir):
    """Test crawling with invalid input."""
    files, errors = crawl_content(
        input_source="not-a-url",
        output_dir=temp_dir,
    )

    assert len(files) == 0
    assert len(errors) == 1
    assert "Crawl failed" in errors[0]


def test_parse_files_invalid_input(temp_dir):
    """Test parsing with invalid input."""
    output_paths, errors = parse_files(
        input_dir=temp_dir / "nonexistent",
        output_dir=temp_dir,
    )

    assert len(output_paths) == 0
    assert len(errors) == 0  # No errors because no files found


@patch("backend.data_processing.pipeline.pipeline_orchestration.embed_chunks")
def test_embed_chunks_from_dir_invalid_input(mock_embed_chunks, temp_dir):
    """Test embedding with invalid input."""
    mock_embed_chunks.side_effect = Exception("Embedding failed")

    n_embedded, errors = embed_chunks_from_dir(
        input_dir=temp_dir / "nonexistent",
        output_dir=temp_dir,
        collection_name="test_collection",
    )

    assert n_embedded == 0
    assert len(errors) == 1
    assert "Embedding failed" in errors[0]


def test_error_handling_with_messages(temp_dir, test_error_messages):
    """Test error handling with standardized error messages."""
    # Test file not found error
    nonexistent_file = temp_dir / "nonexistent.txt"
    error_path = temp_dir / "error.json"
    _save_error_to_json(
        test_error_messages["file_not_found"].format(path=nonexistent_file),
        error_path,
    )
    assert error_path.exists()
    with open(error_path) as f:
        data = json.load(f)
        assert "File not found" in data["error"]

    # Test invalid file format error
    invalid_file = temp_dir / "invalid.txt"
    invalid_file.write_text("invalid content")
    error_path = temp_dir / "format_error.json"
    _save_error_to_json(
        test_error_messages["invalid_file"].format(file=invalid_file),
        error_path,
    )
    assert error_path.exists()
    with open(error_path) as f:
        data = json.load(f)
        assert "Invalid file format" in data["error"]

    # Test network error
    error_path = temp_dir / "network_error.json"
    _save_error_to_json(
        test_error_messages["network_error"].format(error="Connection refused"),
        error_path,
    )
    assert error_path.exists()
    with open(error_path) as f:
        data = json.load(f)
        assert "Network error" in data["error"]
        assert "Connection refused" in data["error"]
