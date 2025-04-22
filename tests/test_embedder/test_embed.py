"""
Tests for the embed module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.embedder.embed import Embedder


@pytest.mark.unit
@pytest.mark.embedding
class TestEmbedderClass:
    """Test the Embedder class."""

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embedder_init(self, mock_persistent_client):
        """Test initializing the Embedder."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Check that the client was initialized
        mock_persistent_client.assert_called_once()

        # Check that the collection was created
        mock_client.get_or_create_collection.assert_called_once_with("documents")

        # Check the embedder attributes
        assert embedder.model_name == "default"
        assert embedder.collection == mock_collection

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_text(self, mock_persistent_client):
        """Test embedding text."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed text
        embedder.embed_text("This is a test document.")

        # Check that the collection's add method was called
        mock_collection.add.assert_called_once()

        # Check the arguments
        args, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == ["This is a test document."]
        assert len(kwargs["ids"]) == 1
        assert len(kwargs["metadatas"]) == 1
        assert kwargs["metadatas"][0]["source"] == "direct_input"
        assert "timestamp" in kwargs["metadatas"][0]

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_text_with_metadata(self, mock_persistent_client):
        """Test embedding text with custom metadata."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed text with custom metadata
        metadata = {"source": "test", "category": "example"}
        embedder.embed_text(
            "This is a test document.", doc_id="test_id", metadata=metadata
        )

        # Check that the collection's add method was called
        mock_collection.add.assert_called_once()

        # Check the arguments
        args, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == ["This is a test document."]
        assert kwargs["ids"] == ["test_id"]
        assert kwargs["metadatas"] == [metadata]

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_documents(self, mock_persistent_client):
        """Test embedding multiple documents."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Prepare documents
        documents = [
            ("doc1", "This is document 1."),
            ("doc2", "This is document 2.", {"source": "test"}),
            ("doc3", "This is document 3."),
        ]

        # Embed documents
        doc_ids = embedder.embed_documents(documents)

        # Check that the collection's add method was called for each document
        assert mock_collection.add.call_count == 3

        # Check the returned document IDs
        assert doc_ids == ["doc1", "doc2", "doc3"]


@pytest.mark.integration
@pytest.mark.embedding
class TestEmbedderIntegration:
    """Test the Embedder integration."""

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_workflow(self, mock_persistent_client, temp_dir):
        """Test the complete embedding workflow."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set the CHROMA_DB_PATH environment variable
        with patch.dict(os.environ, {"CHROMA_DB_PATH": temp_dir}):
            # Initialize the embedder
            embedder = Embedder()

            # Embed a document
            embedder.embed_text("This is a test document.")

            # Check that the collection's add method was called
            mock_collection.add.assert_called_once()

            # Check the arguments
            args, kwargs = mock_collection.add.call_args
            assert kwargs["documents"] == ["This is a test document."]
            assert len(kwargs["ids"]) == 1


@pytest.mark.unit
@pytest.mark.embedding
@pytest.mark.edge_case
class TestEmbedderEdgeCases:
    """Test edge cases for the Embedder."""

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_empty_text(self, mock_persistent_client):
        """Test embedding empty text."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed empty text
        embedder.embed_text("")

        # Check that the collection's add method was called
        mock_collection.add.assert_called_once()

        # Check the arguments
        args, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == [""]

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_documents_empty_list(self, mock_persistent_client):
        """Test embedding an empty list of documents."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed empty list
        doc_ids = embedder.embed_documents([])

        # Check that the collection's add method was not called
        mock_collection.add.assert_not_called()

        # Check the returned document IDs
        assert doc_ids == []

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_text_with_none_metadata(self, mock_persistent_client):
        """Test embedding text with None metadata."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed text with None metadata
        embedder.embed_text("This is a test document.", metadata=None)

        # Check that the collection's add method was called
        mock_collection.add.assert_called_once()

        # Check the arguments
        args, kwargs = mock_collection.add.call_args
        assert kwargs["documents"] == ["This is a test document."]
        assert len(kwargs["metadatas"]) == 1
        assert kwargs["metadatas"][0]["source"] == "direct_input"
        assert "timestamp" in kwargs["metadatas"][0]

    @patch("app.embedder.embed.chromadb.PersistentClient")
    @patch("app.embedder.embed.uuid.uuid4")
    def test_embed_text_uuid_generation(self, mock_uuid4, mock_persistent_client):
        """Test UUID generation when embedding text."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client
        mock_uuid4.return_value = "test-uuid"

        # Initialize the embedder
        embedder = Embedder()

        # Embed text without specifying doc_id
        doc_id = embedder.embed_text("This is a test document.")

        # Check that uuid4 was called
        mock_uuid4.assert_called_once()

        # Check that the generated UUID was used
        assert doc_id == "test-uuid"

    @patch("app.embedder.embed.chromadb.PersistentClient")
    def test_embed_text_chroma_exception(self, mock_persistent_client):
        """Test handling ChromaDB exceptions when embedding text."""
        # Set up the mock to raise an exception
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.add.side_effect = Exception("ChromaDB error")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the embedder
        embedder = Embedder()

        # Embed text - should raise the exception
        with pytest.raises(Exception) as excinfo:
            embedder.embed_text("This is a test document.")

        # Check the exception
        assert "ChromaDB error" in str(excinfo.value)
