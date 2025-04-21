# Metropole Corpus Embedder

This module provides functionality to embed the Metropole corpus using the all-MiniLM-L6-v2 model and store the embeddings in a Chroma vector database.

## Overview

The `embed_corpus.py` script:

1. Loads the `metropole_corpus.json` file
2. Embeds each chunk using the all-MiniLM-L6-v2 model (via ChromaDB's DefaultEmbeddingFunction)
3. Stores the text and metadata in Chroma
4. Includes detailed logging to show how many embeddings were created

## Usage

### Basic Usage

Run the script with default parameters:

```bash
python app/embedder/embed_corpus.py
```

This will:
- Load the corpus from `./data/processed/metropole_corpus.json`
- Use the default Chroma DB path from the CHROMA_DB_PATH environment variable or `./data/index`
- Store embeddings in a collection named "metropole_documents"
- Process chunks in batches of 100

### Advanced Usage

The script supports several command-line arguments:

```bash
python app/embedder/embed_corpus.py --corpus-path PATH --chroma-path PATH --collection-name NAME --batch-size SIZE
```

Parameters:
- `--corpus-path`: Path to the corpus file (default: `./data/processed/metropole_corpus.json`)
- `--chroma-path`: Path to the Chroma DB (default: value of CHROMA_DB_PATH env var or `./data/index`)
- `--collection-name`: Name of the collection to store embeddings in (default: `metropole_documents`)
- `--batch-size`: Number of documents to embed in each batch (default: 100)

Example:
```bash
python app/embedder/embed_corpus.py --corpus-path ./data/custom/corpus.json --collection-name custom_collection --batch-size 50
```

## Metadata

The script stores the following metadata for each chunk:

- `page_id`: Identifier for the page the chunk belongs to
- `page_title`: Title of the page
- `page_name`: Name of the page
- `section_header`: Section header for the chunk
- `tags`: Comma-separated list of tags extracted for the chunk

This metadata can be used for filtering and retrieval operations in the vector database.

## Performance

The embedding process is optimized for performance:
- Chunks are processed in batches to reduce memory usage
- Progress is logged to show embedding status
- The script reports the total time taken and number of embeddings created

On a typical system, embedding the entire corpus takes approximately 1-2 minutes.
