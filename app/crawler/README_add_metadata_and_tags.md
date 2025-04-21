# Add Metadata and Tags

This script adds metadata and tags to content chunks extracted from HTML files.

## Features

- Assigns a unique page_id to each page
- Assigns a unique chunk_id to each content chunk
- Uses KeyBERT with MiniLM to extract 3-5 tags per chunk
- Stores everything in a structured JSON file

## Prerequisites

Make sure you have run the HTML content extraction process first:

1. Run `process_html_content.py` to extract content from HTML files
2. This will create `data/processed/content_objects.py` which is required for this script

## Required Packages

- keybert
- sentence-transformers (automatically installed with keybert)

## Usage

Run the script from the project root directory:

```bash
python -m app.crawler.add_metadata_and_tags
```

## Output

The script will create a file named `metropole_corpus.json` in the `data/processed` directory.

This JSON file contains an array of objects with the following structure:

```json
[
  {
    "chunk_id": "chunk_12345678-90ab-cdef-1234-567890abcdef",
    "page_id": "page_12345678",
    "page_title": "Page Title",
    "page_name": "page_name",
    "section_header": "Section Header",
    "content": "The text content of the chunk",
    "content_html": "<p>The HTML content of the chunk</p>",
    "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"]
  },
  ...
]
```

## Process

1. Loads content objects from `data/processed/content_objects.py`
2. Initializes KeyBERT with the MiniLM model
3. Generates unique page IDs for each unique page
4. For each content chunk:
   - Generates a unique chunk ID
   - Extracts 3-5 tags using KeyBERT + MiniLM
   - Creates a processed object with metadata and tags
5. Saves all processed objects to `data/processed/metropole_corpus.json`
6. Prints a summary of the processing results
