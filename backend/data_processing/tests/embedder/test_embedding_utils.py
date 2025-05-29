import json
import pytest
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from backend.data_processing.models.content_chunk import ContentChunk
from backend.data_processing.embedder.embedding_utils import (
    embed_chunks,
    _load_json_file,
)
from backend.logger.logging_config import configure_logging


@pytest.fixture(autouse=True)
def setup_logging():
    """Configure logging for tests."""
    # Configure root logger for testing
    configure_logging(
        logger_name="metropole_ai_refactor",
        log_level=logging.INFO,
        propagate=True,  # Enable propagation for caplog
    )


@pytest.fixture
def sample_chunks():
    """Create sample ContentChunk objects for testing."""
    return [
        {
            "chunk_id": "test1",
            "text_content": "Test content 1",
            "file_name": "test1.txt",
            "file_ext": ".txt",
            "page_number": 1,
            "document_title": "Test Document 1",
        },
        {
            "chunk_id": "test2",
            "text_content": "Test content 2",
            "file_name": "test2.txt",
            "file_ext": ".txt",
            "page_number": 1,
            "document_title": "Test Document 2",
        },
    ]


@pytest.fixture
def mock_collection():
    """Create a mock ChromaDB collection."""
    collection = Mock()
    collection.add = Mock()
    return collection


@pytest.fixture
def mock_client(mock_collection):
    """Create a mock ChromaDB client."""
    client = Mock()
    client.get_or_create_collection = Mock(return_value=mock_collection)
    return client


def create_json_file(tmp_path: Path, chunks_data: list) -> Path:
    """Helper function to create a JSON file with given chunks data."""
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f)
    return tmp_path


def test_embed_chunks_success(sample_chunks, mock_client, tmp_path, caplog):
    """Test successful embedding of chunks from JSON file."""
    caplog.set_level(logging.INFO)
    json_path = create_json_file(tmp_path / "test_chunks.json", sample_chunks)

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path], "test_collection", db_path)

        # Verify collection was created and documents were added
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )
        call_args = mock_client.get_or_create_collection.return_value.add.call_args[1]
        assert call_args["ids"] == ["test1", "test2"]
        assert call_args["documents"] == [
            "Test content 1",
            "Test content 2",
        ]
        assert len(call_args["metadatas"]) == 2
        assert call_args["metadatas"][0]["file_name"] == "test1.txt"
        assert call_args["metadatas"][1]["file_name"] == "test2.txt"

        # Verify logging
        log_messages = [record.message for record in caplog.records]
        assert any("Using collection: test_collection" in msg for msg in log_messages)
        assert any("Processing file 1 of 1" in msg for msg in log_messages)
        assert any("Processed chunk 1 of 2" in msg for msg in log_messages)
        assert any("Processed chunk 2 of 2" in msg for msg in log_messages)
        assert any("Finished processing file 1 of 1" in msg for msg in log_messages)
        assert any("All files processed: 1 total" in msg for msg in log_messages)


def test_embed_chunks_empty_list(tmp_path, caplog):
    """Test embedding with empty file list."""
    caplog.set_level(logging.ERROR)
    with pytest.raises(ValueError, match="No JSON files provided for embedding"):
        embed_chunks([], "test_collection", str(tmp_path / "test_db"))
    assert any(
        "No JSON files provided for embedding" in record.message
        for record in caplog.records
    )


def test_embed_chunks_db_error(sample_chunks, tmp_path, caplog):
    """Test handling of database errors."""
    caplog.set_level(logging.ERROR)
    json_path = create_json_file(tmp_path / "test_chunks.json", sample_chunks)

    with patch("chromadb.PersistentClient", side_effect=Exception("DB Error")):
        with pytest.raises(RuntimeError, match="Failed to embed chunks"):
            embed_chunks([json_path], "test_collection", str(tmp_path / "test_db"))
    assert any(
        "Failed to embed chunks: DB Error" in record.message
        for record in caplog.records
    )


def test_embed_chunks_invalid_json(tmp_path, caplog):
    """Test handling of invalid JSON file."""
    caplog.set_level(logging.WARNING)
    invalid_json_path = tmp_path / "invalid.json"
    with open(invalid_json_path, "w", encoding="utf-8") as f:
        f.write("invalid json content")

    embed_chunks([invalid_json_path], "test_collection", str(tmp_path))
    assert any(
        "Failed to parse JSON file" in record.message for record in caplog.records
    )
    assert any("Error processing" in record.message for record in caplog.records)


def test_embed_chunks_multiple_files(sample_chunks, mock_client, tmp_path, caplog):
    """Test embedding chunks from multiple JSON files."""
    caplog.set_level(logging.INFO)
    json_path1 = create_json_file(tmp_path / "chunks1.json", [sample_chunks[0]])
    json_path2 = create_json_file(tmp_path / "chunks2.json", [sample_chunks[1]])

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path1, json_path2], "test_collection", db_path)

        # Verify collection was created and documents were added twice
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )
        assert mock_client.get_or_create_collection.return_value.add.call_count == 2

        # Verify logging
        log_messages = [record.message for record in caplog.records]
        assert any(
            "Processing file 1 of 2" in msg for msg in log_messages
        ), "First file processing message not found"
        assert any(
            "Processing file 2 of 2" in msg for msg in log_messages
        ), "Second file processing message not found"
        assert any(
            "Finished processing file 1 of 2" in msg for msg in log_messages
        ), "First file completion message not found"
        assert any(
            "Finished processing file 2 of 2" in msg for msg in log_messages
        ), "Second file completion message not found"
        assert any(
            "All files processed: 2 total" in msg for msg in log_messages
        ), "Summary message not found"


def test_embed_chunks_invalid_chunk(sample_chunks, mock_client, tmp_path, caplog):
    """Test handling of invalid chunk data within a valid JSON file."""
    caplog.set_level(logging.INFO)
    chunks_data = [sample_chunks[0], {"invalid": "data"}]
    json_path = create_json_file(tmp_path / "mixed_chunks.json", chunks_data)

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path], "test_collection", db_path)

        # Verify warning logging for invalid chunk
        assert any("Invalid chunk in" in record.message for record in caplog.records)

        # Verify successful processing of valid chunk
        log_messages = [record.message for record in caplog.records]
        assert any(
            "Processed chunk 1 of 1" in msg for msg in log_messages
        ), "No chunk processing message found"
        assert any(
            "Finished processing file 1 of 1" in msg for msg in log_messages
        ), "No file completion message found"
        assert any(
            "All files processed: 1 total" in msg for msg in log_messages
        ), "No summary message found"
        assert any(
            "1 errors" in msg for msg in log_messages
        ), "Error count not found in summary"


@pytest.fixture
def temp_json_file(tmp_path, sample_chunks):
    json_file = tmp_path / "test_chunks.json"
    with open(json_file, "w") as f:
        json.dump(sample_chunks, f)
    return json_file


@pytest.fixture
def temp_log_file(tmp_path):
    log_file = tmp_path / "embedding.log"
    return log_file


def test_load_json_file(temp_json_file):
    chunks, invalid_chunks = _load_json_file(temp_json_file)
    assert len(chunks) == 2
    assert invalid_chunks == 0
    assert isinstance(chunks[0], ContentChunk)
    assert chunks[0].chunk_id == "test1"


def test_load_json_file_invalid(temp_json_file):
    # Corrupt the JSON file
    with open(temp_json_file, "w") as f:
        f.write("invalid json")

    with pytest.raises(json.JSONDecodeError):
        _load_json_file(temp_json_file)


@patch("chromadb.PersistentClient")
def test_embed_chunks_logging(mock_client, temp_json_file, temp_log_file, caplog):
    # Mock the logger at the module level
    with patch(
        "backend.data_processing.embedder.embedding_utils.logger"
    ) as mock_logger:
        # Mock ChromaDB collection
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        # Run embedding process
        embed_chunks([temp_json_file], "test_collection", str(temp_json_file.parent))

        # Verify logging calls
        assert mock_logger.info.call_count > 0
        assert "Processing file 1 of 1" in str(mock_logger.info.call_args_list)
        assert "Finished processing file 1 of 1" in str(mock_logger.info.call_args_list)
        assert "Processed chunk 1 of 2" in str(mock_logger.info.call_args_list)
        assert "Processed chunk 2 of 2" in str(mock_logger.info.call_args_list)
        assert "All files processed" in str(mock_logger.info.call_args_list)


@patch("chromadb.PersistentClient")
def test_embed_chunks_error_logging(mock_client, temp_json_file, temp_log_file, caplog):
    # Mock the logger at the module level
    with patch(
        "backend.data_processing.embedder.embedding_utils.logger"
    ) as mock_logger:
        # Mock ChromaDB collection to raise an error
        mock_collection = MagicMock()
        mock_collection.add.side_effect = Exception("Test error")
        mock_client.return_value.get_or_create_collection.return_value = mock_collection

        # Run embedding process
        embed_chunks([temp_json_file], "test_collection", str(temp_json_file.parent))

        # Verify error logging
        assert mock_logger.error.call_count > 0
        assert "Error processing chunk" in str(mock_logger.error.call_args_list)
        assert "Test error" in str(mock_logger.error.call_args_list)

        # Verify error in summary
        assert "Failed items" in str(mock_logger.info.call_args_list)
        assert "Test error" in str(mock_logger.info.call_args_list)
