import pytest
from backend_refactor.models.content_chunk import ContentChunk


def test_content_chunk_initialization(valid_content_chunk):
    """Test basic initialization."""
    assert valid_content_chunk.chunk_id == "test123"
    assert valid_content_chunk.file_name == "test_file"
    assert valid_content_chunk.file_ext == ".txt"
    assert valid_content_chunk.page_number == 1
    assert valid_content_chunk.text_content == "This is a test content"
    assert valid_content_chunk.document_title == "Test Document"


def test_content_chunk_without_title():
    """Test initialization without optional title."""
    chunk = ContentChunk(
        chunk_id="test123",
        file_name="test_file",
        file_ext=".txt",
        page_number=1,
        text_content="This is a test content",
    )
    assert chunk.document_title is None


def test_content_chunk_validation(invalid_content_chunk_data):
    """Test validation errors."""
    with pytest.raises(ValueError):
        ContentChunk(**invalid_content_chunk_data)
