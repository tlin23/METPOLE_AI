import json
import chromadb
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..models.content_chunk import ContentChunk
from ..configer.logging_config import get_logger

# Get the logger for this module
logger = get_logger("embedder")


def _load_json_file(json_path: Path) -> Tuple[List[ContentChunk], int]:
    """Load and validate chunks from a JSON file."""
    invalid_chunks = 0
    chunks = []

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            chunks_data = json.load(f)

        for chunk_data in chunks_data:
            try:
                if isinstance(chunk_data, str):
                    chunk_data = json.loads(chunk_data)
                chunks.append(ContentChunk(**chunk_data))
            except (json.JSONDecodeError, ValueError) as e:
                invalid_chunks += 1
                logger.warning(f"Invalid chunk in {json_path}: {str(e)}")

        return chunks, invalid_chunks

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON file {json_path}: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error reading file {json_path}: {str(e)}")
        raise


def _prepare_chunk_data(
    chunks: List[ContentChunk],
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    """Prepare chunk data for ChromaDB insertion."""
    return (
        [chunk.chunk_id for chunk in chunks],
        [chunk.text_content for chunk in chunks],
        [
            {
                "file_name": chunk.file_name,
                "file_ext": chunk.file_ext,
                "page_number": chunk.page_number,
                "document_title": chunk.document_title,
            }
            for chunk in chunks
        ],
    )


def embed_chunks(json_paths: List[Path], collection_name: str, db_path: str) -> None:
    """Convert chunks from JSON files to text embeddings and store them in ChromaDB."""
    if not json_paths:
        error_msg = "No JSON files provided for embedding"
        logger.error(error_msg)
        raise ValueError(error_msg)

    start_time = time.time()
    total_files = len(json_paths)
    failed_items = []
    total_chunks = 0
    error_count = 0

    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(name=collection_name)
        logger.info(f"Using collection: {collection_name}")

        for file_idx, json_path in enumerate(json_paths, 1):
            file_start_time = time.time()
            file_name = json_path.name
            logger.info(f"Processing file {file_idx} of {total_files}: {file_name}")

            try:
                chunks, invalid_chunks = _load_json_file(json_path)
                total_chunks += len(chunks)
                error_count += invalid_chunks

                if not chunks:
                    error_msg = f"No valid chunks found in {file_name}"
                    logger.warning(error_msg)
                    failed_items.append((file_name, None, error_msg))
                    continue

                # Process all chunks from the file at once
                try:
                    ids, documents, metadatas = _prepare_chunk_data(chunks)
                    collection.add(ids=ids, documents=documents, metadatas=metadatas)

                    # Log individual chunk processing for tracking
                    for chunk_idx, chunk in enumerate(chunks, 1):
                        logger.info(
                            f"Processed chunk {chunk_idx} of {len(chunks)} (chunk_id={chunk.chunk_id}) in file {file_name}"
                        )
                except Exception as e:
                    error_msg = str(e)
                    error_count += len(chunks)
                    for chunk in chunks:
                        failed_items.append((file_name, chunk.chunk_id, error_msg))
                    logger.error(
                        f"Error processing chunks in file {file_name}: {error_msg}"
                    )

                file_duration = time.time() - file_start_time
                logger.info(
                    f"Finished processing file {file_idx} of {total_files}: {file_name} in {file_duration:.2f}s"
                )

            except Exception as e:
                error_msg = str(e)
                error_count += 1
                failed_items.append((file_name, None, error_msg))
                logger.error(
                    f"Error processing file {file_idx} of {total_files}: {file_name}: {error_msg} after {time.time() - file_start_time:.2f}s"
                )

        total_duration = time.time() - start_time

        # Log final summary
        summary = f"""
###
All files processed: {total_files} total, {total_chunks} chunks, {error_count} errors, total time: {total_duration:.2f}s
Failed items:
"""
        for file_name, chunk_id, error_reason in failed_items:
            if chunk_id:
                summary += f"  - {file_name}/(chunk_id={chunk_id}): {error_reason}\n"
            else:
                summary += f"  - {file_name}: {error_reason}\n"
        summary += "###"

        logger.info(summary)

    except Exception as e:
        error_msg = f"Failed to embed chunks: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
