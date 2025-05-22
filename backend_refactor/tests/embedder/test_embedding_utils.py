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


def test_embed_chunks_success(sample_chunks, mock_client, tmp_path):
    """Test successful embedding of chunks."""
    with patch("chromadb.PersistentClient", return_value=mock_client):
        db_path = str(tmp_path / "test_db")
        embed_chunks(sample_chunks, "test_collection", db_path)

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
    """Test embedding with empty chunks list."""
    with pytest.raises(ValueError, match="No chunks provided for embedding"):
        embed_chunks([], "test_collection", str(tmp_path / "test_db"))


def test_embed_chunks_db_error(sample_chunks, tmp_path):
    """Test handling of database errors."""
    with patch("chromadb.PersistentClient", side_effect=Exception("DB Error")):
        with pytest.raises(RuntimeError, match="Failed to embed chunks"):
            embed_chunks(sample_chunks, "test_collection", str(tmp_path / "test_db"))
