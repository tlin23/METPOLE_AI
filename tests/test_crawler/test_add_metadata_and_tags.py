"""
Tests for the add_metadata_and_tags module.
"""

import os
import sys
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.crawler.add_metadata_and_tags import (
    generate_page_ids,
    extract_tags_with_keybert,
    process_content_objects,
    save_to_json,
)


@pytest.mark.unit
@pytest.mark.chunking
class TestAddMetadataFunctions:
    """Test individual functions in the add_metadata_and_tags module."""

    def test_generate_page_ids(self, sample_content_objects):
        """Test generating page IDs."""
        result = generate_page_ids(sample_content_objects)

        # Should have 2 unique page IDs
        assert len(result) == 2
        assert "test_page_1" in result
        assert "test_page_2" in result

        # IDs should follow the expected format
        for page_name, page_id in result.items():
            assert page_id.startswith("page_")
            assert len(page_id) > 5  # Should have some UUID part

    @patch("uuid.uuid4")
    def test_generate_page_ids_deterministic(self, mock_uuid4, sample_content_objects):
        """Test generating deterministic page IDs for testing."""
        # Make UUID deterministic for testing
        mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

        result = generate_page_ids(sample_content_objects)

        # Check the format with the deterministic UUID
        assert result["test_page_1"] == "page_12345678"
        assert result["test_page_2"] == "page_12345678"

    def test_extract_tags_with_keybert(self, mock_keybert):
        """Test extracting tags with KeyBERT."""
        text = "This is a test content for extracting keywords and tags."
        result = extract_tags_with_keybert(text, mock_keybert, num_tags=3)

        # Should have 3 tags
        assert len(result) == 3
        assert "test" in result
        assert "content" in result
        assert "section" in result

    def test_extract_tags_with_keybert_short_text(self, mock_keybert):
        """Test extracting tags with short text."""
        text = "Short text."
        result = extract_tags_with_keybert(text, mock_keybert)

        # Should return empty list for very short text
        assert result == []

    def test_extract_tags_with_keybert_empty_text(self, mock_keybert):
        """Test extracting tags with empty text."""
        text = ""
        result = extract_tags_with_keybert(text, mock_keybert)

        # Should return empty list for empty text
        assert result == []


@pytest.mark.integration
@pytest.mark.chunking
class TestProcessContentObjects:
    """Test the process_content_objects function."""

    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    def test_process_content_objects(self, mock_keybert_class, sample_content_objects):
        """Test processing content objects."""
        # Set up the mock
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = [
            ("test", 0.9),
            ("content", 0.8),
            ("section", 0.7),
        ]
        mock_keybert_class.return_value = mock_keybert_instance

        # Patch UUID to be deterministic
        with patch("uuid.uuid4") as mock_uuid4:
            mock_uuid4.return_value = uuid.UUID("12345678-1234-5678-1234-567812345678")

            # Call the function
            with patch.object(sys, "path", sys.path):  # Preserve sys.path
                with patch(
                    "app.crawler.add_metadata_and_tags.content_objects",
                    sample_content_objects,
                ):
                    result = process_content_objects()

        # Check the result
        assert len(result) == len(sample_content_objects)

        # Check the structure of the processed objects
        for obj in result:
            assert "chunk_id" in obj
            assert "page_id" in obj
            assert "page_title" in obj
            assert "page_name" in obj
            assert "section_header" in obj
            assert "content" in obj
            assert "content_html" in obj
            assert "tags" in obj

            # Check that tags were extracted
            if len(obj["content"]) >= 20:
                assert len(obj["tags"]) == 3
                assert "test" in obj["tags"]
                assert "content" in obj["tags"]
                assert "section" in obj["tags"]

    def test_save_to_json(self, temp_dir, sample_corpus_with_metadata):
        """Test saving processed objects to JSON."""
        output_path = os.path.join(temp_dir, "test_output.json")

        # Call the function
        save_to_json(sample_corpus_with_metadata, output_path)

        # Check that the file was created
        assert os.path.exists(output_path)

        # Check the content
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert len(loaded_data) == len(sample_corpus_with_metadata)
        assert loaded_data[0]["chunk_id"] == sample_corpus_with_metadata[0]["chunk_id"]


@pytest.mark.integration
@pytest.mark.chunking
@pytest.mark.edge_case
class TestAddMetadataEdgeCases:
    """Test edge cases for the add_metadata_and_tags module."""

    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    def test_process_content_objects_with_edge_cases(
        self, mock_keybert_class, sample_content_objects_with_edge_cases
    ):
        """Test processing content objects with edge cases."""
        # Set up the mock
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = [
            ("test", 0.9),
            ("content", 0.8),
            ("section", 0.7),
        ]
        mock_keybert_class.return_value = mock_keybert_instance

        # Call the function
        with patch.object(sys, "path", sys.path):  # Preserve sys.path
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects",
                sample_content_objects_with_edge_cases,
            ):
                result = process_content_objects()

        # Check the result
        assert len(result) == len(sample_content_objects_with_edge_cases)

        # Check empty content
        empty_content_obj = next(
            obj for obj in result if obj["section_header"] == "Empty Section"
        )
        assert empty_content_obj["tags"] == []

        # Check short content
        short_content_obj = next(
            obj for obj in result if obj["section_header"] == "Short Section"
        )
        assert short_content_obj["tags"] == []

        # Check long content
        long_content_obj = next(
            obj for obj in result if obj["section_header"] == "Long Section"
        )
        assert len(long_content_obj["tags"]) == 3

    def test_save_to_json_empty_list(self, temp_dir):
        """Test saving an empty list to JSON."""
        output_path = os.path.join(temp_dir, "empty_output.json")

        # Call the function with an empty list
        save_to_json([], output_path)

        # Check that the file was created
        assert os.path.exists(output_path)

        # Check the content
        with open(output_path, "r", encoding="utf-8") as f:
            loaded_data = json.load(f)

        assert loaded_data == []

    def test_generate_page_ids_empty_list(self):
        """Test generating page IDs with an empty list."""
        result = generate_page_ids([])
        assert result == {}

    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    def test_keybert_exception_handling(
        self, mock_keybert_class, sample_content_objects
    ):
        """Test handling KeyBERT exceptions."""
        # Set up the mock to raise an exception
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.side_effect = Exception("KeyBERT error")
        mock_keybert_class.return_value = mock_keybert_instance

        # Call the function
        with patch.object(sys, "path", sys.path):  # Preserve sys.path
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects",
                sample_content_objects,
            ):
                # Should handle the exception and return empty tags
                result = extract_tags_with_keybert(
                    "Test content", mock_keybert_instance
                )
                assert result == []
