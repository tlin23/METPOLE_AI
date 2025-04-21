"""
Pytest configuration file with common fixtures for all tests.
"""

import os
import sys
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to the Python path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_html():
    """Return a sample HTML content for testing."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Test Page</title>
        <meta property="og:title" content="Test Page Meta Title">
    </head>
    <body>
        <header>
            <nav>
                <a href="/">Home</a>
                <a href="/about">About</a>
            </nav>
        </header>
        <main>
            <h1>Main Heading</h1>
            <section>
                <h2>Section 1</h2>
                <p>This is the first paragraph of section 1.</p>
                <p>This is the second paragraph of section 1.</p>
            </section>
            <section>
                <h2>Section 2</h2>
                <p>This is the first paragraph of section 2.</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </section>
        </main>
        <footer>
            <p>Footer content</p>
        </footer>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_file(temp_dir, sample_html):
    """Create a sample HTML file for testing."""
    file_path = os.path.join(temp_dir, "test_page.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sample_html)
    return file_path


@pytest.fixture
def sample_html_with_missing_tags():
    """Return a sample HTML content with missing tags for testing edge cases."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <!-- Missing title tag -->
    </head>
    <body>
        <!-- Missing main content -->
        <p>Some content without proper structure</p>
        <div>Another div without headers</div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_with_empty_content():
    """Return a sample HTML content with empty sections for testing edge cases."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Empty Page</title>
    </head>
    <body>
        <main>
            <h1>Empty Heading</h1>
            <section>
                <h2>Empty Section</h2>
                <!-- No content here -->
            </section>
        </main>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_file_with_missing_tags(temp_dir, sample_html_with_missing_tags):
    """Create a sample HTML file with missing tags for testing edge cases."""
    file_path = os.path.join(temp_dir, "test_page_missing_tags.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sample_html_with_missing_tags)
    return file_path


@pytest.fixture
def sample_html_file_with_empty_content(temp_dir, sample_html_with_empty_content):
    """Create a sample HTML file with empty content for testing edge cases."""
    file_path = os.path.join(temp_dir, "test_page_empty_content.html")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(sample_html_with_empty_content)
    return file_path


@pytest.fixture
def sample_content_objects():
    """Return sample content objects for testing."""
    return [
        {
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 1",
            "content": "This is the content of section 1.",
            "content_html": "<p>This is the content of section 1.</p>"
        },
        {
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 2",
            "content": "This is the content of section 2.",
            "content_html": "<p>This is the content of section 2.</p>"
        },
        {
            "page_title": "Test Page 2",
            "page_name": "test_page_2",
            "section_header": "Section 1",
            "content": "This is the content of section 1 on page 2.",
            "content_html": "<p>This is the content of section 1 on page 2.</p>"
        }
    ]


@pytest.fixture
def sample_content_objects_with_edge_cases():
    """Return sample content objects with edge cases for testing."""
    return [
        # Normal content
        {
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 1",
            "content": "This is the content of section 1.",
            "content_html": "<p>This is the content of section 1.</p>"
        },
        # Empty content
        {
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Empty Section",
            "content": "",
            "content_html": "<p></p>"
        },
        # Very short content (less than 20 chars)
        {
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Short Section",
            "content": "Short text.",
            "content_html": "<p>Short text.</p>"
        },
        # Very long content
        {
            "page_title": "Test Page 2",
            "page_name": "test_page_2",
            "section_header": "Long Section",
            "content": "This is a very long content that exceeds the typical length of a chunk. " * 20,
            "content_html": f"<p>{'This is a very long content that exceeds the typical length of a chunk. ' * 20}</p>"
        }
    ]


@pytest.fixture
def sample_corpus_with_metadata():
    """Return a sample corpus with metadata and tags for testing."""
    return [
        {
            "chunk_id": "chunk_test_001",
            "page_id": "page_test_001",
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 1",
            "content": "This is the content of section 1.",
            "content_html": "<p>This is the content of section 1.</p>",
            "tags": ["test", "content", "section1"]
        },
        {
            "chunk_id": "chunk_test_002",
            "page_id": "page_test_001",
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 2",
            "content": "This is the content of section 2.",
            "content_html": "<p>This is the content of section 2.</p>",
            "tags": ["test", "content", "section2"]
        },
        {
            "chunk_id": "chunk_test_003",
            "page_id": "page_test_002",
            "page_title": "Test Page 2",
            "page_name": "test_page_2",
            "section_header": "Section 1",
            "content": "This is the content of section 1 on page 2.",
            "content_html": "<p>This is the content of section 1 on page 2.</p>",
            "tags": ["test", "content", "page2", "section1"]
        }
    ]


@pytest.fixture
def sample_corpus_with_edge_cases():
    """Return a sample corpus with edge cases for testing."""
    return [
        # Normal chunk
        {
            "chunk_id": "chunk_test_001",
            "page_id": "page_test_001",
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section 1",
            "content": "This is the content of section 1.",
            "content_html": "<p>This is the content of section 1.</p>",
            "tags": ["test", "content", "section1"]
        },
        # Empty content
        {
            "chunk_id": "chunk_test_002",
            "page_id": "page_test_001",
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Empty Section",
            "content": "",
            "content_html": "<p></p>",
            "tags": []
        },
        # Missing tags
        {
            "chunk_id": "chunk_test_003",
            "page_id": "page_test_001",
            "page_title": "Test Page 1",
            "page_name": "test_page_1",
            "section_header": "Section with Missing Tags",
            "content": "This content has no tags.",
            "content_html": "<p>This content has no tags.</p>",
            "tags": []
        },
        # Very long content
        {
            "chunk_id": "chunk_test_004",
            "page_id": "page_test_002",
            "page_title": "Test Page 2",
            "page_name": "test_page_2",
            "section_header": "Long Section",
            "content": "This is a very long content that exceeds the typical length of a chunk. " * 20,
            "content_html": f"<p>{'This is a very long content that exceeds the typical length of a chunk. ' * 20}</p>",
            "tags": ["test", "long", "content"]
        }
    ]


@pytest.fixture
def sample_corpus_json_file(temp_dir, sample_corpus_with_metadata):
    """Create a sample corpus JSON file for testing."""
    file_path = os.path.join(temp_dir, "test_corpus.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_corpus_with_metadata, f, indent=2)
    return file_path


@pytest.fixture
def sample_corpus_with_edge_cases_json_file(temp_dir, sample_corpus_with_edge_cases):
    """Create a sample corpus JSON file with edge cases for testing."""
    file_path = os.path.join(temp_dir, "test_corpus_edge_cases.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(sample_corpus_with_edge_cases, f, indent=2)
    return file_path


@pytest.fixture
def mock_chroma_client():
    """Create a mock ChromaDB client for testing."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client.get_collection.return_value = mock_collection
    
    # Set up the collection's query method to return sample results
    mock_collection.query.return_value = {
        "ids": [["chunk_test_001", "chunk_test_002", "chunk_test_003"]],
        "documents": [["This is the content of section 1.", "This is the content of section 2.", "This is the content of section 1 on page 2."]],
        "metadatas": [[
            {"page_id": "page_test_001", "page_title": "Test Page 1", "section_header": "Section 1", "tags": "test,content,section1"},
            {"page_id": "page_test_001", "page_title": "Test Page 1", "section_header": "Section 2", "tags": "test,content,section2"},
            {"page_id": "page_test_002", "page_title": "Test Page 2", "section_header": "Section 1", "tags": "test,content,page2,section1"}
        ]],
        "distances": [[0.1, 0.2, 0.3]]
    }
    
    # Set up the collection's get method to return sample results
    mock_collection.get.return_value = {
        "ids": ["chunk_test_001"],
        "documents": ["This is the content of section 1."],
        "metadatas": [{"page_id": "page_test_001", "page_title": "Test Page 1", "section_header": "Section 1", "tags": "test,content,section1"}]
    }
    
    return mock_client


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client for testing."""
    mock_client = MagicMock()
    mock_completion = MagicMock()
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    # Set up the message content
    mock_message.content = "This is a sample response from the LLM."
    
    # Set up the choice with the message
    mock_choice.message = mock_message
    
    # Set up the completion with the choice
    mock_completion.choices = [mock_choice]
    
    # Set up the client's chat.completions.create method to return the mock completion
    mock_client.chat.completions.create.return_value = mock_completion
    
    return mock_client


@pytest.fixture
def mock_keybert():
    """Create a mock KeyBERT model for testing."""
    mock_model = MagicMock()
    mock_model.extract_keywords.return_value = [
        ("test", 0.9),
        ("content", 0.8),
        ("section", 0.7)
    ]
    return mock_model
