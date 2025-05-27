import json
import pytest
import logging
from unittest.mock import Mock, patch
from pathlib import Path
from backend_refactor.models.content_chunk import ContentChunk
from backend_refactor.embedder.embedding_utils import embed_chunks
from backend_refactor.configer.logging_config import configure_logging


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
        ContentChunk(
            chunk_id="chunk1",
            file_name="test1",
            file_ext="txt",
            page_number=1,
            text_content="This is test content 1",
            document_title="Test Document 1",
        ),
        ContentChunk(
            chunk_id="chunk2",
            file_name="test2",
            file_ext="pdf",
            page_number=2,
            text_content="This is test content 2",
            document_title="Test Document 2",
        ),
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
    json_path = create_json_file(
        tmp_path / "test_chunks.json", [chunk.model_dump() for chunk in sample_chunks]
    )

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path], "test_collection", db_path)

        # Verify collection was created and documents were added
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )
        call_args = mock_client.get_or_create_collection.return_value.add.call_args[1]
        assert call_args["ids"] == ["chunk1", "chunk2"]
        assert call_args["documents"] == [
            "This is test content 1",
            "This is test content 2",
        ]
        assert len(call_args["metadatas"]) == 2
        assert call_args["metadatas"][0]["file_name"] == "test1"
        assert call_args["metadatas"][1]["file_name"] == "test2"

        # Verify logging
        log_messages = [record.message for record in caplog.records]
        assert any(
            "Starting embedding process for 1 files" in msg for msg in log_messages
        )
        assert any("Successfully embedded 2 chunks" in msg for msg in log_messages)
        assert any("Files processed: 1/1" in msg for msg in log_messages)
        assert any("Total chunks processed: 2" in msg for msg in log_messages)


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
    json_path = create_json_file(
        tmp_path / "test_chunks.json", [chunk.model_dump() for chunk in sample_chunks]
    )

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
    json_path1 = create_json_file(
        tmp_path / "chunks1.json", [sample_chunks[0].model_dump()]
    )
    json_path2 = create_json_file(
        tmp_path / "chunks2.json", [sample_chunks[1].model_dump()]
    )

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
            "Starting embedding process for 2 files" in msg for msg in log_messages
        )
        assert any("Files processed: 2/2" in msg for msg in log_messages)
        assert any("Total chunks processed: 2" in msg for msg in log_messages)


def test_embed_chunks_invalid_chunk(sample_chunks, mock_client, tmp_path, caplog):
    """Test handling of invalid chunk data within a valid JSON file."""
    caplog.set_level(logging.INFO)
    chunks_data = [sample_chunks[0].model_dump(), {"invalid": "data"}]
    json_path = create_json_file(tmp_path / "mixed_chunks.json", chunks_data)

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path], "test_collection", db_path)

        # Verify warning logging for invalid chunk
        assert any("Invalid chunk in" in record.message for record in caplog.records)

        # Verify successful processing of valid chunk
        log_messages = [record.message for record in caplog.records]
        success_messages = [
            msg for msg in log_messages if "Successfully embedded" in msg
        ]
        assert len(success_messages) > 0, "No success message found in logs"
        assert (
            "1 chunks" in success_messages[0]
        ), "Success message does not indicate 1 chunk was embedded"
        assert any("Invalid chunks: 1" in msg for msg in log_messages)
