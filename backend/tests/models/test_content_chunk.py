import pytest
from models.content_chunk import ContentChunk


def test_content_chunk_initialization():
    # Test basic initialization
    chunk = ContentChunk(
        chunk_id="test123",
        file_name="test_file",
        file_ext="txt",
        page_number=1,
        text_content="This is a test content",
    )
    assert chunk.chunk_id == "test123"
    assert chunk.file_name == "test_file"
    assert chunk.file_ext == "txt"
    assert chunk.page_number == 1
    assert chunk.text_content == "This is a test content"
    assert chunk.document_title is None


def test_content_chunk_with_title():
    # Test initialization with optional title
    chunk = ContentChunk(
        chunk_id="test123",
        file_name="test_file",
        file_ext="txt",
        page_number=1,
        text_content="This is a test content",
        document_title="Test Document",
    )
    assert chunk.document_title == "Test Document"


def test_content_chunk_validation():
    # Test validation errors
    with pytest.raises(ValueError):
        ContentChunk(
            chunk_id="test123",
            file_name="test_file",
            file_ext="txt",
            page_number="not_an_integer",  # Should be int
            text_content="This is a test content",
        )
