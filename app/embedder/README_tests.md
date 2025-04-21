# Embedding Tests

This directory contains tests to verify that embeddings are correctly added to the Chroma vector store.

## Test Files

1. `test_embeddings.py` - A comprehensive unittest suite for testing the embedding process
2. `verify_embeddings.py` - A standalone script that verifies embeddings are added correctly

## What the Tests Verify

Both test files verify the following aspects of the embedding process:

1. **Embedding Count**: Ensures that all chunks from the corpus are embedded and stored in Chroma.
2. **ID Presence**: Verifies that all chunk IDs are present in the vector store.
3. **Metadata Correctness**: Checks that metadata (page_id, page_title, page_name, section_header, tags) is stored correctly.
4. **Content Correctness**: Ensures that the content of each chunk is stored correctly.
5. **Similarity Ranking**: Verifies that similarity search works correctly and returns results in the expected order.

## Running the Tests

### Running the unittest suite

```bash
python -m unittest app/embedder/test_embeddings.py
```

This will run all the tests in the unittest suite and report the results.

### Running the verification script

```bash
python app/embedder/verify_embeddings.py
```

or

```bash
./app/embedder/verify_embeddings.py
```

This will run the verification script, which will:
1. Create a small test corpus
2. Embed it into a temporary Chroma database
3. Perform various checks to ensure embeddings are stored correctly
4. Clean up the temporary files

## Implementation Details

### Test Corpus

Both tests create a small test corpus with three chunks:
- Chunk 1: A basic test chunk
- Chunk 2: Another chunk from the same page
- Chunk 3: A chunk from a different page with content that includes the word "different"

This allows testing various aspects of the embedding and retrieval process.

### Temporary Database

The tests create a temporary Chroma database to avoid interfering with any existing databases. The temporary files are cleaned up after the tests complete.

### Similarity Testing

The similarity tests use a query that should match all chunks but with different levels of similarity. This allows verifying that the similarity ranking works correctly.

## Adding More Tests

To add more tests:

1. Add new test methods to the `TestEmbeddings` class in `test_embeddings.py`
2. Add new checks to the `verify_embeddings` function in `verify_embeddings.py`

When adding tests, consider:
- Edge cases (empty content, very long content, etc.)
- Different metadata combinations
- Various query patterns for similarity search
