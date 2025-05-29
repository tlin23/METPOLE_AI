import pytest
from pathlib import Path
from bs4 import BeautifulSoup
from backend.data_processing.parsers.unified_html_parser import (
    UnifiedHTMLParser,
    HeadingHierarchyStrategy,
    BackupStrategy,
    clean_text,
    hash_id,
)


@pytest.fixture
def test_html_file(tmp_path):
    """Create a test HTML file."""
    html_content = """
    <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <h1>Main Heading</h1>
            <p>This is a test paragraph</p>
            <h2>Sub Heading</h2>
            <p>Another paragraph</p>
        </body>
    </html>
    """
    file_path = tmp_path / "test.html"
    file_path.write_text(html_content)
    return file_path


@pytest.fixture
def complex_html_file(tmp_path):
    """Create a complex test HTML file with multiple sections."""
    html_content = """
    <html>
        <head>
            <title>Complex Test Page</title>
        </head>
        <body>
            <div class="preamble">
                <p>This is the preamble content</p>
            </div>
            <article>
                <h1>Article Title</h1>
                <p>First paragraph of the article</p>
                <h2>First Section</h2>
                <p>Second paragraph with more content</p>
                <h3>Subsection</h3>
                <p>Third paragraph with additional information</p>
            </article>
            <section>
                <h2>Content in another section</h2>
                <p>More content here</p>
            </section>
        </body>
    </html>
    """
    file_path = tmp_path / "complex.html"
    file_path.write_text(html_content)
    return file_path


@pytest.fixture
def duplicate_html_file(tmp_path):
    """Create a test HTML file with duplicate content."""
    html_content = """
    <html>
        <head>
            <title>Duplicate Content Test</title>
        </head>
        <body>
            <p>This is a duplicate paragraph</p>
            <p>This is a duplicate paragraph</p>
            <p>This is a different paragraph</p>
            <p>This is a unique paragraph</p>
        </body>
    </html>
    """
    file_path = tmp_path / "duplicate.html"
    file_path.write_text(html_content)
    return file_path


def test_unified_parser_initialization():
    """Test that UnifiedHTMLParser can be instantiated."""
    parser = UnifiedHTMLParser()
    assert parser is not None
    assert len(parser.strategies) == 2
    assert isinstance(parser.strategies[0], HeadingHierarchyStrategy)
    assert isinstance(parser.strategies[1], BackupStrategy)


def test_unified_parser_basic(test_html_file):
    """Test basic HTML parsing functionality."""
    parser = UnifiedHTMLParser()
    chunks = parser.parse(test_html_file)

    # Verify results
    assert len(chunks) > 0
    assert chunks[0].document_title == "Test Page"
    assert "Main Heading" in chunks[0].text_content
    assert "This is a test paragraph" in chunks[0].text_content


def test_unified_parser_invalid_file(tmp_path):
    """Test parser behavior with invalid files."""
    parser = UnifiedHTMLParser()

    # Test non-existent file
    with pytest.raises(IOError):
        parser.parse(tmp_path / "nonexistent.html")

    # Test non-HTML file
    test_file = tmp_path / "test.txt"
    test_file.write_text("Not HTML content")
    with pytest.raises(ValueError):
        parser.parse(test_file)


def test_unified_parser_complex(complex_html_file):
    """Test parser with more complex HTML structure."""
    parser = UnifiedHTMLParser()
    chunks = parser.parse(complex_html_file)

    # Verify results
    assert len(chunks) > 0
    assert chunks[0].document_title == "Complex Test Page"

    # Check that all important content is present
    content = " ".join(chunk.text_content for chunk in chunks)
    assert "This is the preamble content" in content
    assert "Article Title" in content
    assert "First paragraph of the article" in content
    assert "Second paragraph with more content" in content
    assert "Third paragraph with additional information" in content
    assert "Content in another section" in content


def test_unified_parser_duplicate_chunks(duplicate_html_file):
    """Test that duplicate chunks are not created."""
    parser = UnifiedHTMLParser()
    chunks = parser.parse(duplicate_html_file)

    # Verify results
    assert len(chunks) > 0
    content = " ".join(chunk.text_content for chunk in chunks)

    # Check that all unique content is present
    assert "This is a duplicate paragraph" in content
    assert "This is a different paragraph" in content
    assert "This is a unique paragraph" in content

    # Verify chunk IDs are unique
    chunk_ids = {chunk.chunk_id for chunk in chunks}
    assert len(chunk_ids) == len(chunks)  # No duplicate IDs


def test_strategy_fallback():
    """Test that the parser falls back to backup strategy when primary fails."""
    # Create HTML with no headings to force fallback
    html_content = """
    <html>
        <head>
            <title>No Headings Page</title>
        </head>
        <body>
            <p>This is a paragraph without any headings</p>
            <p>Another paragraph</p>
        </body>
    </html>
    """
    soup = BeautifulSoup(html_content, "html.parser")
    file_path = Path("test.html")

    # Primary strategy should return no chunks
    primary = HeadingHierarchyStrategy()
    primary_chunks = primary.extract_chunks(soup, file_path, "No Headings Page")
    assert len(primary_chunks) == 0

    # Backup strategy should extract chunks
    backup = BackupStrategy()
    backup_chunks = backup.extract_chunks(soup, file_path, "No Headings Page")
    assert len(backup_chunks) > 0
    assert "This is a paragraph without any headings" in backup_chunks[0].text_content


def test_clean_text():
    """Test text cleaning functionality."""
    # Test invisible characters removal
    text = "Hello\u200bWorld\u200e\u200f"
    cleaned = clean_text(text)
    assert cleaned == "Hello World"

    # Test smart quote normalization
    text = "\"Hello\" and 'World'"
    cleaned = clean_text(text)
    assert cleaned == "\"Hello\" and 'World'"

    # Test whitespace normalization
    text = "Hello\n  World  \n  Test"
    cleaned = clean_text(text)
    assert cleaned == "Hello World Test"

    # Test additional special characters
    text = "Smart quotes: \u201c\u201d ''"  # Using Unicode for smart quotes
    cleaned = clean_text(text)
    assert (
        cleaned == "Smart quotes: \"\" ''"
    )  # Smart quotes are converted to regular quotes

    text = "Multiple\n\n\nlines"
    cleaned = clean_text(text)
    assert cleaned == "Multiple lines"


def test_hash_id():
    """Test chunk ID generation."""
    text1 = "Hello World"
    text2 = "hello world"
    text3 = "Different text"

    id1 = hash_id(text1)
    id2 = hash_id(text2)
    id3 = hash_id(text3)

    assert id1 == id2  # Case-insensitive
    assert id1 != id3  # Different content
    assert id1.startswith("chunk_")  # Correct prefix
    assert len(id1) == 38  # "chunk_" (6) + MD5 hash (32)
