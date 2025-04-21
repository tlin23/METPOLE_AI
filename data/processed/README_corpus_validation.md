# Metropole Corpus Validation

This document explains how to validate the `metropole_corpus.json` file using the provided test suite.

## Overview

The validation test suite checks the following:

1. **Required Fields**: Ensures all required fields exist in each chunk
   - `chunk_id`: Unique identifier for each chunk
   - `page_id`: Identifier for the page the chunk belongs to
   - `page_title`: Title of the page
   - `page_name`: Name of the page
   - `section_header`: Section header for the chunk
   - `content`: Text content of the chunk
   - `content_html`: HTML content of the chunk
   - `tags`: List of tags extracted for the chunk

2. **Chunk ID Uniqueness**: Verifies that all chunk IDs are unique

3. **Tag Generation**: Ensures tags are generated for chunks with sufficient content

4. **JSON Schema Validation**: Validates the corpus against a defined JSON schema

5. **Page ID Consistency**: Checks that all chunks from the same page have the same page ID

6. **ID Format Validation**: Verifies that chunk IDs and page IDs follow the expected format

## Running the Validation

### Option 1: Using the Validation Script (Recommended)

The easiest way to run the validation is to use the provided shell script:

```bash
./validate_corpus.sh
```

This script will:
1. Check if Python and pip are installed
2. Verify that the corpus file exists
3. Install the required dependencies
4. Run the validation tests

### Option 2: Using the Python Validation Script

For a quick validation or for integration into other scripts, you can use the Python validation script:

```bash
./validate_corpus.py
```

This script provides a simple way to validate the corpus without running the full test suite. It checks for the most important validation criteria and provides a summary of the results.

Options:
- `--corpus-path PATH`: Specify a custom path to the corpus file
- `--verbose`: Print detailed warnings for each validation issue

Example:
```bash
./validate_corpus.py --verbose
```

### Option 3: Manual Validation

If you prefer to run the full test suite manually, follow these steps:

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the test suite:
   ```bash
   python -m app.crawler.test_metropole_corpus
   ```

## Handling Large Corpus Files

The test suite includes two approaches for validation:

1. **Standard Validation**: Loads the entire corpus into memory for validation
   - Suitable for smaller corpus files
   - Provides more detailed validation

2. **Stream Processing Validation**: Processes the corpus file in a streaming fashion
   - Suitable for very large corpus files that can't be loaded entirely into memory
   - Performs basic validation checks without loading the entire file

The test suite automatically runs both approaches, but if you're working with a very large corpus file and encounter memory issues, you can modify the test suite to only use the stream processing approach.

## Extending the Validation

If you need to add additional validation checks, you can extend the `TestMetropoleCorpus` class in `app/crawler/test_metropole_corpus.py`. Simply add new test methods following the pattern of the existing ones.

For example, to add a test that checks if all chunks have a minimum content length:

```python
def test_minimum_content_length(self):
    """Test that all chunks have a minimum content length."""
    min_length = 10  # Minimum content length in characters
    
    for i, chunk in enumerate(self.corpus):
        self.assertGreater(
            len(chunk['content']), min_length,
            f"Chunk at index {i} has content shorter than {min_length} characters"
        )
```

## Troubleshooting

If the validation fails, the test output will indicate which tests failed and why. Common issues include:

- **Missing Fields**: Some chunks may be missing required fields
- **Duplicate Chunk IDs**: Some chunks may have the same chunk ID
- **Missing Tags**: Chunks with sufficient content may not have tags generated
- **Inconsistent Page IDs**: Chunks from the same page may have different page IDs

To fix these issues, you may need to re-run the metadata and tag generation process by running the `add_metadata_and_tags.py` script.
