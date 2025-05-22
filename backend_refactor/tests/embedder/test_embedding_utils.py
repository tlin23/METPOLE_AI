import json
import pytest
from unittest.mock import Mock, patch
from backend_refactor.models.content_chunk import ContentChunk
from backend_refactor.embedder.embedding_utils import embed_chunks


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
def sample_json_file(sample_chunks, tmp_path):
    """Create a temporary JSON file with sample chunks."""
    json_path = tmp_path / "test_chunks.json"
    chunks_data = [chunk.model_dump() for chunk in sample_chunks]
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(chunks_data, f)
    return json_path


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


def test_embed_chunks_success(sample_json_file, mock_client, tmp_path):
    """Test successful embedding of chunks from JSON file."""
    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([sample_json_file], "test_collection", db_path)

        # Verify collection was created
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )

        # Verify documents were added
        mock_client.get_or_create_collection.return_value.add.assert_called_once()
        call_args = mock_client.get_or_create_collection.return_value.add.call_args[1]

        assert call_args["ids"] == ["chunk1", "chunk2"]
        assert call_args["documents"] == [
            "This is test content 1",
            "This is test content 2",
        ]
        assert len(call_args["metadatas"]) == 2
        assert call_args["metadatas"][0]["file_name"] == "test1"
        assert call_args["metadatas"][1]["file_name"] == "test2"


def test_embed_chunks_empty_list(tmp_path):
    """Test embedding with empty file list."""
    with pytest.raises(ValueError, match="No JSON files provided for embedding"):
        embed_chunks([], "test_collection", str(tmp_path / "test_db"))


def test_embed_chunks_db_error(sample_json_file, tmp_path):
    """Test handling of database errors."""
    with patch("chromadb.PersistentClient", side_effect=Exception("DB Error")):
        with pytest.raises(RuntimeError, match="Failed to embed chunks"):
            embed_chunks(
                [sample_json_file], "test_collection", str(tmp_path / "test_db")
            )


def test_embed_chunks_invalid_json(tmp_path):
    """Test handling of invalid JSON file."""
    invalid_json_path = tmp_path / "invalid.json"
    with open(invalid_json_path, "w", encoding="utf-8") as f:
        f.write("invalid json content")

    with pytest.raises(RuntimeError, match="Failed to embed chunks"):
        embed_chunks([invalid_json_path], "test_collection", str(tmp_path / "test_db"))


def test_embed_chunks_multiple_files(sample_chunks, mock_client, tmp_path):
    """Test embedding chunks from multiple JSON files."""
    # Create two JSON files with different chunks
    json_path1 = tmp_path / "chunks1.json"
    json_path2 = tmp_path / "chunks2.json"

    with open(json_path1, "w", encoding="utf-8") as f:
        json.dump([sample_chunks[0].model_dump()], f)
    with open(json_path2, "w", encoding="utf-8") as f:
        json.dump([sample_chunks[1].model_dump()], f)

    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks([json_path1, json_path2], "test_collection", db_path)

        # Verify collection was created
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )

        # Verify documents were added twice (once for each file)
        assert mock_client.get_or_create_collection.return_value.add.call_count == 2
