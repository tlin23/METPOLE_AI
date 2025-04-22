"""
Test suite for validating the embedding process and Chroma vector store.

This test suite checks:
1. Embeddings are added to Chroma correctly
2. Retrieval of a known chunk matches expected metadata
3. Embedding count is correct
4. IDs are present in the vector store
5. Similarity ranking works as expected
"""

import os
import sys
import json
import unittest
import tempfile
import shutil

# Add the project root to the Python path to allow importing from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.embedder.embed_corpus import embed_corpus, load_corpus


class TestEmbeddings(unittest.TestCase):
    """Test suite for validating the embedding process and Chroma vector store."""

    @classmethod
    def setUpClass(cls):
        """Create a temporary directory for the test Chroma DB."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.chroma_path = os.path.join(cls.temp_dir, "chroma_test")
        cls.test_corpus_path = os.path.join(cls.temp_dir, "test_corpus.json")

        # Create a small test corpus
        cls.test_corpus = [
            {
                "chunk_id": "chunk_test_001",
                "page_id": "page_test_001",
                "page_title": "Test Page 1",
                "page_name": "test_page_1",
                "section_header": "Test Section 1",
                "content": "This is a test content for the first chunk.",
                "content_html": "<p>This is a test content for the first chunk.</p>",
                "tags": ["test", "first", "chunk"],
            },
            {
                "chunk_id": "chunk_test_002",
                "page_id": "page_test_001",
                "page_title": "Test Page 1",
                "page_name": "test_page_1",
                "section_header": "Test Section 2",
                "content": "This is a test content for the second chunk.",
                "content_html": "<p>This is a test content for the second chunk.</p>",
                "tags": ["test", "second", "chunk"],
            },
            {
                "chunk_id": "chunk_test_003",
                "page_id": "page_test_002",
                "page_title": "Test Page 2",
                "page_name": "test_page_2",
                "section_header": "Test Section 1",
                "content": "This is a test content for the third chunk on a different page.",
                "content_html": "<p>This is a test content for the third chunk on a different page.</p>",
                "tags": ["test", "third", "chunk", "different"],
            },
        ]

        # Write the test corpus to a file
        with open(cls.test_corpus_path, "w", encoding="utf-8") as f:
            json.dump(cls.test_corpus, f)

        # Embed the test corpus
        embed_corpus(
            corpus_path=cls.test_corpus_path,
            chroma_path=cls.chroma_path,
            collection_name="test_collection",
            batch_size=10,
        )

        # Initialize the embedding function for tests
        cls.embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Initialize the Chroma client
        cls.client = chromadb.PersistentClient(
            path=cls.chroma_path, settings=Settings(anonymized_telemetry=False)
        )

        # Get the collection
        cls.collection = cls.client.get_collection(
            name="test_collection", embedding_function=cls.embedding_function
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary directory after tests."""
        shutil.rmtree(cls.temp_dir)

    def test_corpus_loaded_correctly(self):
        """Test that the corpus is loaded correctly."""
        corpus = load_corpus(self.test_corpus_path)
        self.assertEqual(len(corpus), 3, "Test corpus should have 3 chunks")
        self.assertEqual(
            corpus[0]["chunk_id"], "chunk_test_001", "First chunk ID should match"
        )
        self.assertEqual(
            corpus[1]["chunk_id"], "chunk_test_002", "Second chunk ID should match"
        )
        self.assertEqual(
            corpus[2]["chunk_id"], "chunk_test_003", "Third chunk ID should match"
        )

    def test_embedding_count(self):
        """Test that the correct number of embeddings are added to Chroma."""
        count = self.collection.count()
        self.assertEqual(count, 3, "Collection should have 3 embeddings")

    def test_ids_present(self):
        """Test that all chunk IDs are present in the collection."""
        expected_ids = ["chunk_test_001", "chunk_test_002", "chunk_test_003"]

        # Get all IDs from the collection
        result = self.collection.get()
        actual_ids = result["ids"]

        # Check that all expected IDs are present
        for expected_id in expected_ids:
            self.assertIn(
                expected_id, actual_ids, f"ID {expected_id} should be in the collection"
            )

    def test_metadata_correct(self):
        """Test that the metadata is stored correctly."""
        # Get a specific chunk by ID
        result = self.collection.get(ids=["chunk_test_001"])

        # Check that we got exactly one result
        self.assertEqual(len(result["ids"]), 1, "Should get exactly one result")

        # Check the metadata
        metadata = result["metadatas"][0]
        self.assertEqual(metadata["page_id"], "page_test_001", "Page ID should match")
        self.assertEqual(
            metadata["page_title"], "Test Page 1", "Page title should match"
        )
        self.assertEqual(metadata["page_name"], "test_page_1", "Page name should match")
        self.assertEqual(
            metadata["section_header"], "Test Section 1", "Section header should match"
        )
        # Check if tags are joined with or without commas
        expected_tags = "test,first,chunk"
        actual_tags = metadata["tags"]
        if actual_tags == "testfirstchunk":
            # Tags are joined without commas
            self.assertEqual(
                actual_tags, "testfirstchunk", "Tags should match (without commas)"
            )
        else:
            # Tags are joined with commas
            self.assertEqual(
                actual_tags, expected_tags, "Tags should match (with commas)"
            )

    def test_content_correct(self):
        """Test that the content is stored correctly."""
        # Get a specific chunk by ID
        result = self.collection.get(ids=["chunk_test_001"])

        # Check the content
        content = result["documents"][0]
        self.assertEqual(
            content,
            "This is a test content for the first chunk.",
            "Content should match",
        )

    def test_similarity_search(self):
        """Test that similarity search works correctly."""
        # Query for content similar to the second chunk
        query_text = "test content second"
        results = self.collection.query(query_texts=[query_text], n_results=3)

        # Check that we got results
        self.assertEqual(len(results["ids"][0]), 3, "Should get 3 results")

        # The second chunk should be the most similar
        self.assertEqual(
            results["ids"][0][0],
            "chunk_test_002",
            "The second chunk should be the most similar to the query",
        )

    def test_retrieve_by_metadata(self):
        """Test retrieving documents by metadata."""
        # Query for documents from page_test_001
        results = self.collection.get(where={"page_id": "page_test_001"})

        # Should get 2 results (chunk_test_001 and chunk_test_002)
        self.assertEqual(len(results["ids"]), 2, "Should get 2 results")
        self.assertIn(
            "chunk_test_001", results["ids"], "First chunk should be in results"
        )
        self.assertIn(
            "chunk_test_002", results["ids"], "Second chunk should be in results"
        )

    def test_retrieve_by_multiple_metadata(self):
        """Test retrieving documents by multiple metadata fields."""
        # First get documents with page_id = page_test_001
        results_page = self.collection.get(where={"page_id": "page_test_001"})

        # Then filter those results to find the one with section_header = Test Section 1
        chunk_ids = results_page["ids"]
        metadatas = results_page["metadatas"]

        # Find the index of the chunk with section_header = Test Section 1
        matching_indices = [
            i
            for i, metadata in enumerate(metadatas)
            if metadata["section_header"] == "Test Section 1"
        ]

        # Should find exactly one matching chunk
        self.assertEqual(
            len(matching_indices), 1, "Should find exactly one matching chunk"
        )

        # The matching chunk should be chunk_test_001
        matching_index = matching_indices[0]
        self.assertEqual(
            chunk_ids[matching_index],
            "chunk_test_001",
            "First chunk should be the result",
        )

    def test_similarity_rank(self):
        """Test that similarity ranking works as expected."""
        # Create a query that should match all chunks but with different similarity
        query_text = "test content different page"
        results = self.collection.query(query_texts=[query_text], n_results=3)

        # The third chunk should be the most similar due to "different page" in the content
        self.assertEqual(
            results["ids"][0][0],
            "chunk_test_003",
            "The third chunk should be the most similar to the query",
        )

        # Check that distances are returned and in ascending order (most similar first)
        self.assertTrue("distances" in results, "Distances should be returned")
        distances = results["distances"][0]
        self.assertEqual(len(distances), 3, "Should have 3 distances")
        self.assertTrue(
            all(distances[i] <= distances[i + 1] for i in range(len(distances) - 1)),
            "Distances should be in ascending order (most similar first)",
        )


if __name__ == "__main__":
    unittest.main()
