import json
import chromadb
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple
from ..models.content_chunk import ContentChunk
from ..configer.logging_config import get_logger

logger = get_logger("embedder.utils")


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
    logger.info(
        f"Starting embedding process for {len(json_paths)} files into collection: {collection_name}"
    )

    stats = {
        "total_files": len(json_paths),
        "processed_files": 0,
        "failed_files": 0,
        "total_chunks": 0,
        "invalid_chunks": 0,
        "failed_chunks": 0,
    }

    try:
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_or_create_collection(name=collection_name)
        logger.info(f"Using collection: {collection_name}")

        for json_path in json_paths:
            file_start_time = time.time()
            logger.info(f"Processing file: {json_path}")

            try:
                chunks, invalid_chunks = _load_json_file(json_path)
                stats["invalid_chunks"] += invalid_chunks

                if not chunks:
                    logger.warning(f"No valid chunks found in {json_path}")
                    stats["failed_files"] += 1
                    continue

                ids, documents, metadatas = _prepare_chunk_data(chunks)
                collection.add(ids=ids, documents=documents, metadatas=metadatas)

                stats["processed_files"] += 1
                stats["total_chunks"] += len(chunks)

                file_duration = time.time() - file_start_time
                logger.info(
                    f"Successfully embedded {len(chunks)} chunks from {json_path} in {file_duration:.2f}s"
                )

            except Exception as e:
                stats["failed_files"] += 1
                logger.error(f"Error processing {json_path}: {str(e)}")

        total_duration = time.time() - start_time
        logger.info("Embedding process completed with the following statistics:")
        logger.info(f"Total duration: {total_duration:.2f}s")
        logger.info(
            f"Files processed: {stats['processed_files']}/{stats['total_files']}"
        )
        logger.info(f"Failed files: {stats['failed_files']}")
        logger.info(f"Total chunks processed: {stats['total_chunks']}")
        logger.info(f"Invalid chunks: {stats['invalid_chunks']}")
        logger.info(f"Failed chunks: {stats['failed_chunks']}")

    except Exception as e:
        error_msg = f"Failed to embed chunks: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
