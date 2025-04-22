"""
Tests for the embed_corpus module.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock, mock_open

from app.embedder.embed_corpus import load_corpus, embed_corpus


@pytest.mark.unit
@pytest.mark.embedding
class TestLoadCorpus:
    """Test the load_corpus function."""

    def test_load_corpus_success(self, sample_corpus_json_file):
        """Test successfully loading a corpus from a JSON file."""
        result = load_corpus(sample_corpus_json_file)

        # Check that the corpus was loaded
        assert len(result) == 3
        assert result[0]["chunk_id"] == "chunk_test_001"
        assert result[1]["chunk_id"] == "chunk_test_002"
        assert result[2]["chunk_id"] == "chunk_test_003"

    def test_load_corpus_file_not_found(self):
        """Test handling a file not found error."""
        with pytest.raises(Exception) as excinfo:
            load_corpus("nonexistent_file.json")

        # Check the exception
        assert "Error loading corpus" in str(excinfo.value)

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_corpus_json_error(self, mock_json_load, mock_file_open):
        """Test handling a JSON parsing error."""
        # Set up the mock to raise an exception
        mock_json_load.side_effect = json.JSONDecodeError("JSON error", "", 0)

        with pytest.raises(Exception) as excinfo:
            load_corpus("test_corpus.json")

        # Check the exception
        assert "Error loading corpus" in str(excinfo.value)


@pytest.mark.integration
@pytest.mark.embedding
class TestEmbedCorpus:
    """Test the embed_corpus function."""

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus(
        self, mock_embedding_function, mock_persistent_client, sample_corpus_json_file
    ):
        """Test embedding a corpus."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Call the function
        embed_corpus(
            corpus_path=sample_corpus_json_file,
            chroma_path="test_chroma_path",
            collection_name="test_collection",
            batch_size=2,
        )

        # Check that the client was initialized
        mock_persistent_client.assert_called_once_with(
            path="test_chroma_path",
            settings=pytest.approx({}),  # Approximate match for Settings object
        )

        # Check that the collection was created
        mock_client.get_or_create_collection.assert_called_once_with(
            name="test_collection",
            embedding_function=mock_embedding_function.return_value,
            metadata={"description": "Metropole corpus embeddings"},
        )

        # Check that the collection's add method was called twice (batch_size=2, 3 documents)
        assert mock_collection.add.call_count == 2

        # Check the first batch
        first_batch_args, first_batch_kwargs = mock_collection.add.call_args_list[0]
        assert len(first_batch_kwargs["ids"]) == 2
        assert first_batch_kwargs["ids"][0] == "chunk_test_001"
        assert first_batch_kwargs["ids"][1] == "chunk_test_002"
        assert len(first_batch_kwargs["documents"]) == 2
        assert first_batch_kwargs["documents"][0] == "This is the content of section 1."
        assert first_batch_kwargs["documents"][1] == "This is the content of section 2."

        # Check the second batch
        second_batch_args, second_batch_kwargs = mock_collection.add.call_args_list[1]
        assert len(second_batch_kwargs["ids"]) == 1
        assert second_batch_kwargs["ids"][0] == "chunk_test_003"
        assert len(second_batch_kwargs["documents"]) == 1
        assert (
            second_batch_kwargs["documents"][0]
            == "This is the content of section 1 on page 2."
        )

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus_with_env_path(
        self, mock_embedding_function, mock_persistent_client, sample_corpus_json_file
    ):
        """Test embedding a corpus with environment variable path."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set the CHROMA_DB_PATH environment variable
        with patch.dict(os.environ, {"CHROMA_DB_PATH": "env_chroma_path"}):
            # Call the function without specifying chroma_path
            embed_corpus(
                corpus_path=sample_corpus_json_file,
                chroma_path=None,
                collection_name="test_collection",
                batch_size=10,
            )

        # Check that the client was initialized with the environment variable path
        mock_persistent_client.assert_called_once_with(
            path="env_chroma_path",
            settings=pytest.approx({}),  # Approximate match for Settings object
        )


@pytest.mark.integration
@pytest.mark.embedding
@pytest.mark.edge_case
class TestEmbedCorpusEdgeCases:
    """Test edge cases for the embed_corpus function."""

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus_empty(
        self, mock_embedding_function, mock_persistent_client, temp_dir
    ):
        """Test embedding an empty corpus."""
        # Create an empty corpus file
        empty_corpus_path = os.path.join(temp_dir, "empty_corpus.json")
        with open(empty_corpus_path, "w", encoding="utf-8") as f:
            json.dump([], f)

        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Call the function
        embed_corpus(
            corpus_path=empty_corpus_path,
            chroma_path="test_chroma_path",
            collection_name="test_collection",
            batch_size=10,
        )

        # Check that the collection's add method was not called
        mock_collection.add.assert_not_called()

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus_batch_size_one(
        self, mock_embedding_function, mock_persistent_client, sample_corpus_json_file
    ):
        """Test embedding a corpus with batch size of 1."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Call the function with batch_size=1
        embed_corpus(
            corpus_path=sample_corpus_json_file,
            chroma_path="test_chroma_path",
            collection_name="test_collection",
            batch_size=1,
        )

        # Check that the collection's add method was called three times (once for each document)
        assert mock_collection.add.call_count == 3

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus_chroma_exception(
        self, mock_embedding_function, mock_persistent_client, sample_corpus_json_file
    ):
        """Test handling ChromaDB exceptions when embedding a corpus."""
        # Set up the mock to raise an exception
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_collection.add.side_effect = Exception("ChromaDB error")
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Call the function - should log the error but not raise it
        with patch("app.embedder.embed_corpus.logger") as mock_logger:
            embed_corpus(
                corpus_path=sample_corpus_json_file,
                chroma_path="test_chroma_path",
                collection_name="test_collection",
                batch_size=10,
            )

            # Check that the error was logged
            mock_logger.error.assert_called()

    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    def test_embed_corpus_with_edge_cases(
        self,
        mock_embedding_function,
        mock_persistent_client,
        sample_corpus_with_edge_cases_json_file,
    ):
        """Test embedding a corpus with edge cases."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Call the function
        embed_corpus(
            corpus_path=sample_corpus_with_edge_cases_json_file,
            chroma_path="test_chroma_path",
            collection_name="test_collection",
            batch_size=10,
        )

        # Check that the collection's add method was called once
        mock_collection.add.assert_called_once()

        # Check the arguments
        args, kwargs = mock_collection.add.call_args
        assert len(kwargs["ids"]) == 4
        assert kwargs["ids"][0] == "chunk_test_001"
        assert kwargs["ids"][1] == "chunk_test_002"  # Empty content
        assert kwargs["ids"][2] == "chunk_test_003"  # Missing tags
        assert kwargs["ids"][3] == "chunk_test_004"  # Very long content

        # Check the documents
        assert kwargs["documents"][0] == "This is the content of section 1."
        assert kwargs["documents"][1] == ""  # Empty content
        assert kwargs["documents"][2] == "This content has no tags."
        assert "This is a very long content" in kwargs["documents"][3]

        # Check the metadata
        assert kwargs["metadatas"][0]["tags"] == "test,content,section1"
        assert kwargs["metadatas"][1]["tags"] == ""  # Empty tags
        assert kwargs["metadatas"][2]["tags"] == ""  # Empty tags
        assert kwargs["metadatas"][3]["tags"] == "test,long,content"

    @patch("app.embedder.embed_corpus.load_corpus")
    def test_embed_corpus_load_failure(self, mock_load_corpus, temp_dir):
        """Test handling corpus loading failures."""
        # Set up the mock to raise an exception
        mock_load_corpus.side_effect = Exception("Failed to load corpus")

        # Call the function - should raise the exception
        with pytest.raises(Exception) as excinfo:
            embed_corpus(
                corpus_path="test_corpus.json",
                chroma_path=temp_dir,
                collection_name="test_collection",
                batch_size=10,
            )

        # Check the exception
        assert "Failed to load corpus" in str(excinfo.value)
