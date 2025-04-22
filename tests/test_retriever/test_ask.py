"""
Tests for the ask module.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

from app.retriever.ask import Retriever


@pytest.mark.unit
@pytest.mark.retrieval
class TestRetrieverClass:
    """Test the Retriever class."""

    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_retriever_init(self, mock_persistent_client):
        """Test initializing the Retriever."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the retriever
        retriever = Retriever()

        # Check that the client was initialized
        mock_persistent_client.assert_called_once()

        # Check that the collection was created
        mock_client.get_or_create_collection.assert_called_once_with("documents")

        # Check the retriever attributes
        assert retriever.collection == mock_collection

    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_query(self, mock_persistent_client):
        """Test querying the vector store."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the collection's query method to return sample results
        mock_collection.query.return_value = {
            "ids": [["chunk_test_001", "chunk_test_002", "chunk_test_003"]],
            "documents": [
                [
                    "This is the content of section 1.",
                    "This is the content of section 2.",
                    "This is the content of section 1 on page 2.",
                ]
            ],
            "metadatas": [
                [
                    {
                        "page_id": "page_test_001",
                        "page_title": "Test Page 1",
                        "section_header": "Section 1",
                        "tags": "test,content,section1",
                    },
                    {
                        "page_id": "page_test_001",
                        "page_title": "Test Page 1",
                        "section_header": "Section 2",
                        "tags": "test,content,section2",
                    },
                    {
                        "page_id": "page_test_002",
                        "page_title": "Test Page 2",
                        "section_header": "Section 1",
                        "tags": "test,content,page2,section1",
                    },
                ]
            ],
            "distances": [[0.1, 0.2, 0.3]],
        }

        # Initialize the retriever
        retriever = Retriever()

        # Query the vector store
        result = retriever.query("test query", n_results=3)

        # Check that the collection's query method was called
        mock_collection.query.assert_called_once_with(
            query_texts=["test query"],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        # Check the result
        assert result == mock_collection.query.return_value

    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_get_document(self, mock_persistent_client):
        """Test retrieving a specific document by ID."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the collection's get method to return sample results
        mock_collection.get.return_value = {
            "ids": ["chunk_test_001"],
            "documents": ["This is the content of section 1."],
            "metadatas": [
                {
                    "page_id": "page_test_001",
                    "page_title": "Test Page 1",
                    "section_header": "Section 1",
                    "tags": "test,content,section1",
                }
            ],
        }

        # Initialize the retriever
        retriever = Retriever()

        # Get a document
        result = retriever.get_document("chunk_test_001")

        # Check that the collection's get method was called
        mock_collection.get.assert_called_once_with(ids=["chunk_test_001"])

        # Check the result
        assert result == mock_collection.get.return_value


@pytest.mark.integration
@pytest.mark.retrieval
class TestRetrieverIntegration:
    """Test the Retriever integration."""

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_generate_answer(self, mock_openai, mock_persistent_client):
        """Test generating an answer using OpenAI."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Set up the chat completions mock
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a sample response from the LLM."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        # Initialize the retriever
        retriever = Retriever()

        # Generate an answer
        chunks = [
            MagicMock(
                text="Chunk 1 text",
                metadata={
                    "chunk_id": "chunk1",
                    "page_title": "Page 1",
                    "section_header": "Section 1",
                },
            ),
            MagicMock(
                text="Chunk 2 text",
                metadata={
                    "chunk_id": "chunk2",
                    "page_title": "Page 1",
                    "section_header": "Section 2",
                },
            ),
        ]

        result = retriever.generate_answer("What is the answer?", chunks)

        # Check that the OpenAI API was called
        mock_openai_client.chat.completions.create.assert_called_once()

        # Check the result
        assert "answer" in result
        assert result["answer"] == "This is a sample response from the LLM."
        assert "is_general_knowledge" in result
        assert "contains_diy_advice" in result
        assert "source_info" in result

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_generate_answer_with_general_knowledge(
        self, mock_openai, mock_persistent_client
    ):
        """Test generating an answer with general knowledge flag."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Set up the chat completions mock with general knowledge response
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "Based on general knowledge, the answer is..."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        # Initialize the retriever
        retriever = Retriever()

        # Generate an answer
        chunks = [
            MagicMock(
                text="Chunk 1 text",
                metadata={
                    "chunk_id": "chunk1",
                    "page_title": "Page 1",
                    "section_header": "Section 1",
                },
            )
        ]

        result = retriever.generate_answer("What is the answer?", chunks)

        # Check the result
        assert result["is_general_knowledge"] is True
        assert "general knowledge" in result["answer"]

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_generate_answer_with_diy_advice(self, mock_openai, mock_persistent_client):
        """Test generating an answer with DIY advice flag."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Set up the chat completions mock with DIY advice response
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "You can try these steps to fix the issue..."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        # Initialize the retriever
        retriever = Retriever()

        # Generate an answer
        chunks = [
            MagicMock(
                text="Chunk 1 text",
                metadata={
                    "chunk_id": "chunk1",
                    "page_title": "Page 1",
                    "section_header": "Section 1",
                },
            )
        ]

        result = retriever.generate_answer("How do I fix this?", chunks)

        # Check the result
        assert result["contains_diy_advice"] is True
        assert "Disclaimer" in result["answer"]


@pytest.mark.unit
@pytest.mark.retrieval
@pytest.mark.edge_case
class TestRetrieverEdgeCases:
    """Test edge cases for the Retriever."""

    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_query_empty_results(self, mock_persistent_client):
        """Test querying with empty results."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the collection's query method to return empty results
        mock_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        # Initialize the retriever
        retriever = Retriever()

        # Query the vector store
        result = retriever.query("test query")

        # Check the result
        assert result["ids"][0] == []
        assert result["documents"][0] == []
        assert result["metadatas"][0] == []
        assert result["distances"][0] == []

    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_get_document_not_found(self, mock_persistent_client):
        """Test retrieving a document that doesn't exist."""
        # Set up the mock
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the collection's get method to return empty results
        mock_collection.get.return_value = {"ids": [], "documents": [], "metadatas": []}

        # Initialize the retriever
        retriever = Retriever()

        # Get a document
        result = retriever.get_document("nonexistent_id")

        # Check the result
        assert result["ids"] == []
        assert result["documents"] == []
        assert result["metadatas"] == []

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_generate_answer_empty_chunks(self, mock_openai, mock_persistent_client):
        """Test generating an answer with empty chunks."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Set up the chat completions mock
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "I don't have specific information about that."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion

        # Initialize the retriever
        retriever = Retriever()

        # Generate an answer with empty chunks
        result = retriever.generate_answer("What is the answer?", [])

        # Check the result
        assert "answer" in result
        assert result["is_general_knowledge"] is True
        assert "source_info" in result
        assert result["source_info"] == ""

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_generate_answer_openai_error(self, mock_openai, mock_persistent_client):
        """Test handling OpenAI API errors."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock to raise an exception
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "OpenAI API error"
        )

        # Initialize the retriever
        retriever = Retriever()

        # Generate an answer - should raise the exception
        with pytest.raises(Exception) as excinfo:
            retriever.generate_answer(
                "What is the answer?",
                [
                    MagicMock(
                        text="Chunk 1 text",
                        metadata={
                            "chunk_id": "chunk1",
                            "page_title": "Page 1",
                            "section_header": "Section 1",
                        },
                    )
                ],
            )

        # Check the exception
        assert "OpenAI API error" in str(excinfo.value)

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": ""})
    def test_missing_api_key(self, mock_openai, mock_persistent_client):
        """Test handling missing OpenAI API key."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Initialize the retriever - should raise ValueError
        with pytest.raises(ValueError) as excinfo:
            retriever = Retriever()

        # Check the exception
        assert "OPENAI_API_KEY" in str(excinfo.value)

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_prepare_source_info_empty(self, mock_openai, mock_persistent_client):
        """Test preparing source info with empty chunks."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Initialize the retriever
        retriever = Retriever()

        # Call the private method
        result = retriever._prepare_source_info([])

        # Check the result
        assert result == ""

    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_prepare_source_info_missing_metadata(
        self, mock_openai, mock_persistent_client
    ):
        """Test preparing source info with chunks missing metadata."""
        # Set up the mocks
        mock_client = MagicMock()
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        mock_persistent_client.return_value = mock_client

        # Set up the OpenAI mock
        mock_openai_client = MagicMock()
        mock_openai.return_value = mock_openai_client

        # Initialize the retriever
        retriever = Retriever()

        # Create chunks without metadata
        chunks = [
            MagicMock(text="Chunk 1 text", metadata=None),
            MagicMock(text="Chunk 2 text"),  # No metadata attribute
        ]

        # Call the private method
        result = retriever._prepare_source_info(chunks)

        # Check the result - should handle missing metadata gracefully
        assert "unknown-0" in result
        assert "unknown-1" in result
