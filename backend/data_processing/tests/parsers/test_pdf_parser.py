import pytest
from backend.data_processing.parsers.pdf_parser import (
    PDFParser,
    clean_text,
    hash_id,
)


def test_pdf_parser_initialization():
    """Test that PDFParser can be instantiated."""
    parser = PDFParser()
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


def test_pdf_parser_basic(test_pdf_file):
    """Test basic PDF parsing functionality."""
    parser = PDFParser()
    chunks = parser.parse(test_pdf_file)

    # Verify results
    assert len(chunks) == 2  # Two paragraphs from the test PDF
    assert chunks[0].document_title == "Test PDF"
    assert "First paragraph of the test document" in chunks[0].text_content
    assert "Second paragraph with more content" in chunks[1].text_content
    assert chunks[0].page_number == 1
    assert chunks[1].page_number == 1


def test_pdf_parser_invalid_file(temp_dir):
    """Test parser behavior with invalid files."""
    parser = PDFParser()

    # Test non-existent file
    with pytest.raises(IOError):
        parser.parse(temp_dir / "nonexistent.pdf")

    # Test non-PDF file
    test_file = temp_dir / "test.txt"
    test_file.write_text("Not PDF content")
    with pytest.raises(ValueError):
        parser.parse(test_file)


def test_pdf_parser_complex(complex_pdf_file):
    """Test parser with more complex PDF structure."""
    parser = PDFParser()
    chunks = parser.parse(complex_pdf_file)

    # Verify results
    assert len(chunks) == 5  # Five paragraphs across multiple pages
    assert chunks[0].document_title == "Complex Test PDF"
    assert "First paragraph of the document" in chunks[0].text_content
    assert "Second paragraph with more content" in chunks[1].text_content
    assert "Third paragraph with additional information" in chunks[2].text_content
    assert "Content on the second page" in chunks[3].text_content
    assert "Final paragraph of the document" in chunks[4].text_content

    # Verify page numbers
    assert chunks[0].page_number == 1
    assert chunks[3].page_number == 2


def test_pdf_parser_duplicate_chunks(duplicate_pdf_file):
    """Test that duplicate chunks are not created."""
    parser = PDFParser()
    chunks = parser.parse(duplicate_pdf_file)

    # Verify results
    assert len(chunks) == 3  # Should only have 3 unique chunks
    chunk_texts = [chunk.text_content for chunk in chunks]
    assert "This is a duplicate paragraph." in chunk_texts
    assert "This is a different paragraph." in chunk_texts
    assert "This is a unique paragraph." in chunk_texts

    # Verify chunk IDs are unique
    chunk_ids = [chunk.chunk_id for chunk in chunks]
    assert len(chunk_ids) == len(set(chunk_ids))  # All IDs should be unique
