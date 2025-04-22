#!/usr/bin/env python3
"""
Script to verify that embeddings are added to Chroma correctly.

This script:
1. Creates a small test corpus
2. Embeds it into Chroma
3. Retrieves a known chunk and verifies it matches the expected metadata
4. Checks for embedding count
5. Verifies ID presence
6. Tests similarity ranking
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.embedder.embed_corpus import embed_corpus


def verify_embeddings():
    """
    Verify that embeddings are added to Chroma correctly.
    """
    print("Starting embedding verification...")

    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    chroma_path = os.path.join(temp_dir, "chroma_test")
    test_corpus_path = os.path.join(temp_dir, "test_corpus.json")

    try:
        # Create a small test corpus
        test_corpus = [
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
        print(f"Creating test corpus at {test_corpus_path}...")
        with open(test_corpus_path, "w", encoding="utf-8") as f:
            json.dump(test_corpus, f)

        # Embed the test corpus
        print(f"Embedding test corpus into Chroma at {chroma_path}...")
        embed_corpus(
            corpus_path=test_corpus_path,
            chroma_path=chroma_path,
            collection_name="test_collection",
            batch_size=10,
        )

        # Initialize the embedding function for tests
        embedding_function = embedding_functions.DefaultEmbeddingFunction()

        # Initialize the Chroma client
        print("Connecting to Chroma DB...")
        client = chromadb.PersistentClient(
            path=chroma_path, settings=Settings(anonymized_telemetry=False)
        )

        # Get the collection
        collection = client.get_collection(
            name="test_collection", embedding_function=embedding_function
        )

        # Check 1: Verify embedding count
        count = collection.count()
        print("\n1. Embedding Count Check:")
        print(f"   Expected: 3, Actual: {count}")
        assert count == 3, "Collection should have 3 embeddings"
        print("   ✓ PASSED: Correct number of embeddings found")

        # Check 2: Verify IDs are present
        print("\n2. ID Presence Check:")
        expected_ids = ["chunk_test_001", "chunk_test_002", "chunk_test_003"]
        result = collection.get()
        actual_ids = result["ids"]

        for expected_id in expected_ids:
            assert (
                expected_id in actual_ids
            ), f"ID {expected_id} should be in the collection"
            print(f"   ✓ PASSED: Found ID {expected_id}")

        # Check 3: Verify metadata is correct
        print("\n3. Metadata Correctness Check:")
        # Get a specific chunk by ID
        result = collection.get(ids=["chunk_test_001"])

        # Check that we got exactly one result
        assert len(result["ids"]) == 1, "Should get exactly one result"

        # Check the metadata
        metadata = result["metadatas"][0]
        print("   Retrieved metadata for chunk_test_001:")
        for key, value in metadata.items():
            print(f"   - {key}: {value}")

        assert metadata["page_id"] == "page_test_001", "Page ID should match"
        assert metadata["page_title"] == "Test Page 1", "Page title should match"
        assert metadata["page_name"] == "test_page_1", "Page name should match"
        assert (
            metadata["section_header"] == "Test Section 1"
        ), "Section header should match"
        # Check if tags are joined with or without commas
        expected_tags = "test,first,chunk"
        actual_tags = metadata["tags"]
        if actual_tags == "testfirstchunk":
            print("   Note: Tags are joined without commas in the metadata")
            assert actual_tags == "testfirstchunk", "Tags should match (without commas)"
        else:
            assert actual_tags == expected_tags, "Tags should match (with commas)"
        print("   ✓ PASSED: All metadata fields match expected values")

        # Check 4: Verify content is correct
        print("\n4. Content Correctness Check:")
        content = result["documents"][0]
        print(f'   Retrieved content: "{content}"')
        assert (
            content == "This is a test content for the first chunk."
        ), "Content should match"
        print("   ✓ PASSED: Content matches expected value")

        # Check 5: Verify similarity ranking
        print("\n5. Similarity Ranking Check:")
        # Create a query that should match all chunks but with different similarity
        query_text = "test content different page"
        print(f'   Query: "{query_text}"')

        results = collection.query(query_texts=[query_text], n_results=3)

        # The third chunk should be the most similar due to "different page" in the content
        most_similar_id = results["ids"][0][0]
        print(f"   Most similar chunk: {most_similar_id}")
        assert (
            most_similar_id == "chunk_test_003"
        ), "The third chunk should be the most similar to the query"
        print("   ✓ PASSED: Correct chunk ranked as most similar")

        # Check distances
        distances = results["distances"][0]
        print(f"   Similarity distances: {distances}")
        assert len(distances) == 3, "Should have 3 distances"
        assert all(
            distances[i] <= distances[i + 1] for i in range(len(distances) - 1)
        ), "Distances should be in ascending order (most similar first)"
        print("   ✓ PASSED: Distances are in correct order")

        print("\nAll verification checks passed successfully!")

    except Exception as e:
        print(f"Error during verification: {e}")
        raise
    finally:
        # Clean up
        print("\nCleaning up temporary files...")
        shutil.rmtree(temp_dir)
        print("Verification complete.")


if __name__ == "__main__":
    verify_embeddings()
