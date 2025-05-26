import pytest
from backend_refactor.parsers.docx_parser import DOCXParser, clean_text, hash_id


def test_docx_parser_initialization():
    """Test that DOCXParser can be instantiated."""
    parser = DOCXParser()
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


def test_docx_parser_basic(test_docx_file):
    """Test basic DOCX parsing functionality."""
    parser = DOCXParser()
    chunks = parser.parse(test_docx_file)

    # Verify results
    assert len(chunks) == 2  # One chunk for heading + paragraph, one for table
    assert chunks[0].document_title == "Test Document"
    assert "Main Heading" in chunks[0].text_content
    assert "This is a test paragraph" in chunks[0].text_content
    assert "Table 1:" in chunks[1].text_content
    assert "Cell 1" in chunks[1].text_content


def test_docx_parser_invalid_file(temp_dir):
    """Test parser behavior with invalid files."""
    parser = DOCXParser()

    # Test non-existent file
    with pytest.raises(IOError):
        parser.parse(temp_dir / "nonexistent.docx")

    # Test non-DOCX file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Not DOCX content")
    with pytest.raises(ValueError):
        parser.parse(test_file)


def test_docx_parser_complex(complex_docx_file):
    """Test parser with more complex DOCX structure."""
    parser = DOCXParser()
    chunks = parser.parse(complex_docx_file)

    # Verify results
    assert (
        len(chunks) == 5
    )  # One chunk for h1 + first paragraph, two more paragraphs, one chunk for h2 + paragraph, one table
    assert chunks[0].document_title == "Complex Test Document"

    # First chunk should contain h1 and first paragraph
    assert "Document Title" in chunks[0].text_content
    assert "First paragraph of the document" in chunks[0].text_content

    # Second and third chunks should be standalone paragraphs
    assert "Second paragraph with more content" in chunks[1].text_content
    assert "Third paragraph with additional information" in chunks[2].text_content

    # Fourth chunk should contain h2 and its paragraph
    assert "Another Section" in chunks[3].text_content
    assert "Content in another section" in chunks[3].text_content

    # Fifth chunk should be the table
    assert "Table 1:" in chunks[4].text_content
    assert "Table Cell 1" in chunks[4].text_content


def test_docx_parser_duplicate_chunks(duplicate_docx_file):
    """Test that duplicate chunks are not created."""
    parser = DOCXParser()
    chunks = parser.parse(duplicate_docx_file)

    # Verify results
    assert len(chunks) == 3  # Should only have 3 unique chunks
    chunk_texts = [chunk.text_content for chunk in chunks]
    assert "This is a duplicate paragraph." in chunk_texts
    assert "This is a different paragraph." in chunk_texts
    assert "This is a unique paragraph." in chunk_texts

    # Verify chunk IDs are unique
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))  # All IDs should be unique
