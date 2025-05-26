import pytest
from backend_refactor.parsers.html_parser import HTMLParser, clean_text, hash_id


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
    assert len(chunks) == 1  # One chunk containing heading and paragraph
    assert chunks[0].document_title == "Test Page"
    assert "Main Heading" in chunks[0].text_content
    assert "This is a test paragraph" in chunks[0].text_content
    assert chunks[0].text_content == "Main Heading\nThis is a test paragraph."


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
    assert len(chunks) == 5  # One h1, three paragraphs, one h3
    assert chunks[0].document_title == "Complex Test Page"
    assert "First paragraph of the article" in chunks[1].text_content
    assert "Second paragraph with more content" in chunks[2].text_content
    assert "Third paragraph with additional information" in chunks[3].text_content
    assert "Content in another section" in chunks[4].text_content


def test_html_parser_duplicate_chunks(duplicate_html_file):
    """Test that duplicate chunks are not created."""
    parser = HTMLParser()
    chunks = parser.parse(duplicate_html_file)

    # Verify results
    assert len(chunks) == 3  # Should only have 3 unique chunks
    chunk_texts = [chunk.text_content for chunk in chunks]
    assert "This is a duplicate paragraph." in chunk_texts
    assert "This is a different paragraph." in chunk_texts
    assert "This is a unique paragraph." in chunk_texts

    # Verify chunk IDs are unique
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))  # All IDs should be unique
