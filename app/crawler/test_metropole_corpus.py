"""
Test suite to validate the metropole_corpus.json file.

This test suite checks:
1. Required fields exist in each chunk
2. Chunk IDs are unique
3. Tags are generated for chunks with sufficient content
"""

import os
import sys
import json
import unittest
from typing import List, Dict, Any
from jsonschema import validate, ValidationError

# Add the project root to the Python path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


class TestMetropoleCorpus(unittest.TestCase):
    """Test suite for validating the metropole_corpus.json file."""

    @classmethod
    def setUpClass(cls):
        """Load the corpus once for all tests."""
        corpus_path = os.path.join("data", "processed", "metropole_corpus.json")
        try:
            with open(corpus_path, "r", encoding="utf-8") as f:
                cls.corpus = json.load(f)
            print(
                f"Successfully loaded {len(cls.corpus)} content objects from {corpus_path}"
            )
        except FileNotFoundError:
            print(
                f"Error: Could not find {corpus_path}. Make sure to run add_metadata_and_tags.py first."
            )
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Error: Could not parse {corpus_path}. The file may be corrupted.")
            sys.exit(1)

    def test_corpus_is_not_empty(self):
        """Test that the corpus is not empty."""
        self.assertGreater(len(self.corpus), 0, "Corpus should not be empty")

    def test_required_fields_exist(self):
        """Test that all required fields exist in each chunk."""
        required_fields = [
            "chunk_id",
            "page_id",
            "page_title",
            "page_name",
            "section_header",
            "content",
            "content_html",
            "tags",
        ]

        for i, chunk in enumerate(self.corpus):
            for field in required_fields:
                self.assertIn(
                    field,
                    chunk,
                    f"Chunk at index {i} is missing required field '{field}'",
                )

    def test_chunk_ids_are_unique(self):
        """Test that all chunk IDs are unique."""
        chunk_ids = [chunk["chunk_id"] for chunk in self.corpus]
        unique_chunk_ids = set(chunk_ids)

        self.assertEqual(
            len(chunk_ids),
            len(unique_chunk_ids),
            f"Chunk IDs should be unique. Found {len(chunk_ids) - len(unique_chunk_ids)} duplicate IDs.",
        )

    def test_tags_are_generated(self):
        """Test that tags are generated for chunks with sufficient content."""
        for i, chunk in enumerate(self.corpus):
            # Only check chunks with sufficient content (more than 20 characters)
            if len(chunk["content"]) > 20:
                self.assertGreater(
                    len(chunk["tags"]),
                    0,
                    f"Chunk at index {i} with sufficient content should have tags",
                )

    def test_json_schema_validation(self):
        """Test that the corpus conforms to the expected JSON schema."""
        # Define the JSON schema for a corpus chunk
        chunk_schema = {
            "type": "object",
            "required": [
                "chunk_id",
                "page_id",
                "page_title",
                "page_name",
                "section_header",
                "content",
                "content_html",
                "tags",
            ],
            "properties": {
                "chunk_id": {"type": "string"},
                "page_id": {"type": "string"},
                "page_title": {"type": "string"},
                "page_name": {"type": "string"},
                "section_header": {"type": "string"},
                "content": {"type": "string"},
                "content_html": {"type": "string"},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
        }

        # Validate each chunk against the schema
        for i, chunk in enumerate(self.corpus):
            try:
                validate(instance=chunk, schema=chunk_schema)
            except ValidationError as e:
                self.fail(f"Chunk at index {i} failed schema validation: {e}")

    def test_page_ids_are_consistent(self):
        """Test that all chunks from the same page have the same page_id."""
        page_name_to_id = {}

        for chunk in self.corpus:
            page_name = chunk["page_name"]
            page_id = chunk["page_id"]

            if page_name in page_name_to_id:
                self.assertEqual(
                    page_name_to_id[page_name],
                    page_id,
                    f"Inconsistent page_id for page '{page_name}'",
                )
            else:
                page_name_to_id[page_name] = page_id

    def test_chunk_id_format(self):
        """Test that chunk IDs follow the expected format."""
        for i, chunk in enumerate(self.corpus):
            chunk_id = chunk["chunk_id"]
            self.assertTrue(
                chunk_id.startswith("chunk_"),
                f"Chunk ID at index {i} should start with 'chunk_'",
            )
            # Check that the rest of the chunk_id is a valid UUID (or part of one)
            uuid_part = chunk_id[6:]  # Remove 'chunk_' prefix
            self.assertRegex(
                uuid_part,
                r"^[0-9a-f-]+$",
                f"Chunk ID at index {i} has invalid format after 'chunk_' prefix",
            )

    def test_page_id_format(self):
        """Test that page IDs follow the expected format."""
        for i, chunk in enumerate(self.corpus):
            page_id = chunk["page_id"]
            self.assertTrue(
                page_id.startswith("page_"),
                f"Page ID at index {i} should start with 'page_'",
            )
            # Check that the rest of the page_id is a valid UUID (or part of one)
            uuid_part = page_id[5:]  # Remove 'page_' prefix
            self.assertRegex(
                uuid_part,
                r"^[0-9a-f-]+$",
                f"Page ID at index {i} has invalid format after 'page_' prefix",
            )


class TestCorpusStreamProcessing(unittest.TestCase):
    """Test suite for validating the metropole_corpus.json file using stream processing.

    This is useful for large corpus files that can't be loaded entirely into memory.
    """

    def test_stream_processing_validation(self):
        """Test corpus validation using stream processing."""
        corpus_path = os.path.join("data", "processed", "metropole_corpus.json")

        # Set to store chunk IDs for uniqueness check
        chunk_ids = set()

        # Counter for validation statistics
        stats = {"total_chunks": 0, "chunks_with_tags": 0, "chunks_missing_fields": 0}

        # Required fields to check
        required_fields = [
            "chunk_id",
            "page_id",
            "page_title",
            "page_name",
            "section_header",
            "content",
            "content_html",
            "tags",
        ]

        # Process the file in streaming mode
        with open(corpus_path, "rb") as f:
            # Check that the file starts with an array
            first_char = f.read(1).decode("utf-8")
            self.assertEqual(first_char, "[", "Corpus file should start with '['")

            # Reset file pointer
            f.seek(0)

            # Use a streaming JSON parser
            import ijson

            # Process each item in the array
            for chunk in ijson.items(f, "item"):
                stats["total_chunks"] += 1

                # Check required fields
                missing_fields = [
                    field for field in required_fields if field not in chunk
                ]
                if missing_fields:
                    stats["chunks_missing_fields"] += 1
                    print(
                        f"Warning: Chunk {stats['total_chunks']} is missing fields: {missing_fields}"
                    )

                # Check chunk_id uniqueness
                if "chunk_id" in chunk:
                    chunk_id = chunk["chunk_id"]
                    self.assertNotIn(
                        chunk_id, chunk_ids, f"Duplicate chunk_id found: {chunk_id}"
                    )
                    chunk_ids.add(chunk_id)

                # Check tags are generated for chunks with sufficient content
                if "content" in chunk and "tags" in chunk:
                    if len(chunk["content"]) > 20 and len(chunk["tags"]) > 0:
                        stats["chunks_with_tags"] += 1

        # Print statistics
        print(f"\nStream processing statistics:")
        print(f"- Total chunks processed: {stats['total_chunks']}")
        print(f"- Chunks with tags: {stats['chunks_with_tags']}")
        print(f"- Chunks missing fields: {stats['chunks_missing_fields']}")

        # Ensure we processed at least one chunk
        self.assertGreater(stats["total_chunks"], 0, "No chunks were processed")


if __name__ == "__main__":
    unittest.main()
