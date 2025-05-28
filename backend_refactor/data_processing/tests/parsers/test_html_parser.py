import pytest
from backend_refactor.data_processing.parsers.html_parser import (
    HTMLParser,
    clean_text,
    hash_id,
)


def test_html_parser_initialization():
    """Test that HTMLParser can be instantiated."""
    parser = HTMLParser()
    assert parser is not None


def test_clean_text():
    """Test text cleaning functionality."""
    # Test invisible characters removal
    text = "Hello\u200bWorld"
    assert clean_text(text) == "Hello World"

    # Test smart quote normalization
    text = "\"Hello\" and 'World'"
    assert clean_text(text) == "\"Hello\" and 'World'"

    # Test whitespace normalization
    text = "Hello\n  World  \n  Test"
    assert clean_text(text) == "Hello World Test"


def test_hash_id():
    """Test chunk ID generation."""
    text = "Hello World"
    chunk_id = hash_id(text)
    assert chunk_id.startswith("chunk_")
    assert len(chunk_id) == 38  # "chunk_" (6) + MD5 hash (32)


def test_html_parser_basic(test_html_file):
    """Test basic HTML parsing functionality."""
    parser = HTMLParser()
    chunks = parser.parse(test_html_file)

    # Verify results
    assert len(chunks) == 1  # One chunk containing all content
    assert chunks[0].document_title == "Test Page"
    assert "Main Heading" in chunks[0].text_content
    assert "This is a test paragraph" in chunks[0].text_content
    # Don't check exact text content as RecursiveCharacterTextSplitter may format differently


def test_html_parser_invalid_file(temp_dir):
    """Test parser behavior with invalid files."""
    parser = HTMLParser()

    # Test non-existent file
    with pytest.raises(IOError):
        parser.parse(temp_dir / "nonexistent.html")

    # Test non-HTML file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Not HTML content")
    with pytest.raises(ValueError):
        parser.parse(test_file)


def test_html_parser_complex(complex_html_file):
    """Test parser with more complex HTML structure."""
    parser = HTMLParser()
    chunks = parser.parse(complex_html_file)

    # Verify results
    assert len(chunks) == 1  # All content combined into one chunk
    assert chunks[0].document_title == "Complex Test Page"
    # Check that all important content is present
    content = chunks[0].text_content
    assert "Article Title" in content
    assert "First paragraph of the article" in content
    assert "Second paragraph with more content" in content
    assert "Third paragraph with additional information" in content
    assert "Content in another section" in content


def test_html_parser_duplicate_chunks(duplicate_html_file):
    """Test that duplicate chunks are not created."""
    parser = HTMLParser()
    chunks = parser.parse(duplicate_html_file)

    # Verify results
    assert len(chunks) == 1  # All content combined into one chunk
    content = chunks[0].text_content

    # Check that all unique content is present
    assert "This is a duplicate paragraph" in content
    assert "This is a different paragraph" in content
    assert "This is a unique paragraph" in content

    # Verify chunk ID is unique
    assert chunks[0].chunk_id.startswith("chunk_")
    assert len(chunks[0].chunk_id) == 38  # "chunk_" (6) + MD5 hash (32)
