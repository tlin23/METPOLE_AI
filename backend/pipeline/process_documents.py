import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any
from langchain_text_splitters import RecursiveCharacterTextSplitter
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from backend.configer.logging_config import get_logger
from backend.pipeline.processors import PDFProcessor, MSGProcessor, DOCXProcessor

# Constants
DEFAULT_DOCS_ROOT = "backend/data/offline_docs"
PROCESSED_DIR = "backend/data/processed"
RAW_TEXT_DIR = "backend/data/raw_docs"
CHUNK_SIZE = 1000  # Increased chunk size
CHUNK_OVERLAP = 100  # Increased overlap
SUPPORTED_EXTENSIONS = {".pdf", ".docx", ".dotx", ".doc", ".msg"}

# Initialize logger
logger = get_logger("pipeline.process_documents")


def get_processor(file_path: Path):
    """Get the appropriate processor for a file type."""
    extension = file_path.suffix.lower()
    processors = {
        ".pdf": PDFProcessor(),
        ".msg": MSGProcessor(),
        ".docx": DOCXProcessor(),
        ".doc": DOCXProcessor(),  # Use DOCX processor for DOC files
        ".dotx": DOCXProcessor(),  # Use DOCX processor for DOTX files
    }
    return processors.get(extension)


def process_single_document(file_path: Path, output_dir: Path) -> Dict[str, Any]:
    """Process a single document and return its structured content."""
    # Get appropriate processor
    processor = get_processor(file_path)
    if not processor:
        raise ValueError(f"No processor available for {file_path.suffix}")

    # Process document
    structured_blocks = processor.process(file_path)

    # Create document structure
    doc_structure = {
        "metadata": {
            "filename": file_path.name,
            "file_type": file_path.suffix.lower(),
            "sections": list(set(block["section"] for block in structured_blocks)),
        },
        "content": structured_blocks,
    }

    # Save to JSON
    output_file = output_dir / f"{file_path.stem}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(doc_structure, f, indent=2, ensure_ascii=False)

    return doc_structure


def extract_chunks(
    structured_docs: List[Dict[str, Any]], output_path: str
) -> List[Dict[str, Any]]:
    """Extract chunks from structured documents."""
    logger.info("Extracting chunks...")

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=[
            "\n\n",
            "\n",
            ". ",
            "! ",
            "? ",
            "; ",
            ": ",
            " ",
            "",
        ],  # Added space after punctuation
        length_function=len,
        is_separator_regex=False,
    )

    all_chunks = []
    for doc in structured_docs:
        for block in doc["content"]:
            # Get the content text from the block
            content = block.get("content", "")

            # Handle property blocks differently
            if block.get("type") == "properties":
                # Convert properties to a readable string format
                props = content if isinstance(content, dict) else {}
                content = "Document Properties:\n"
                if props.get("title"):
                    content += f"Title: {props['title']}\n"
                if props.get("author"):
                    content += f"Author: {props['author']}\n"
                if props.get("created"):
                    content += f"Created: {props['created']}\n"
                if props.get("modified"):
                    content += f"Modified: {props['modified']}\n"
                if props.get("statistics"):
                    stats = props["statistics"]
                    content += f"Statistics: {stats.get('paragraphs', 0)} paragraphs, {stats.get('tables', 0)} tables"
                logger.debug(f"Converted properties block to text: {content}")

            if not isinstance(content, str):
                logger.warning(
                    f"Skipping block with non-string content:\n"
                    f"Type: {type(content)}\n"
                    f"Content: {content}\n"
                    f"Block structure:\n{json.dumps(block, indent=2, ensure_ascii=False)}"
                )
                continue

            # Split block content into chunks
            chunks = text_splitter.split_text(content)

            # Create chunk data
            for chunk in chunks:
                chunk = " ".join(chunk.split()).strip()  # Clean text

                # Skip chunks that are too short or start with punctuation
                if len(chunk) < 20 or chunk[0] in ".!?;:":
                    continue

                chunk_data = {
                    "source_file": doc["metadata"]["filename"],
                    "section": block["section"],
                    "content": chunk,
                    "source_type": "document",
                }
                all_chunks.append(chunk_data)

    # Save chunks
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Extracted {len(all_chunks)} chunks from {len(structured_docs)} documents"
    )
    return all_chunks


def add_tags(chunks: List[Dict[str, Any]], output_path: str) -> List[Dict[str, Any]]:
    """Add tags to chunks using KeyBERT."""
    logger.info("Adding tags to chunks...")

    # Initialize KeyBERT
    model = KeyBERT(model=SentenceTransformer("all-MiniLM-L6-v2"))

    # Add tags to each chunk
    for chunk in chunks:
        keywords = model.extract_keywords(
            chunk["content"],
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=5,
        )
        chunk["tags"] = [keyword[0] for keyword in keywords]

    # Save tagged chunks
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    return chunks


def process_documents(input_dir: str = DEFAULT_DOCS_ROOT) -> List[Dict[str, Any]]:
    """Process all supported documents in the specified directory."""
    start_time = time.time()
    logger.info("Starting document processing...")

    # Setup directories
    docs_root = Path(input_dir)
    raw_text_dir = Path(RAW_TEXT_DIR)
    raw_text_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing files
    for file in raw_text_dir.glob("*"):
        file.unlink()

    # Process each supported file
    structured_docs = []
    for file_path in docs_root.rglob("*"):
        if file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            try:
                doc = process_single_document(file_path, raw_text_dir)
                structured_docs.append(doc)
            except Exception as e:
                logger.error(f"Error processing {file_path}: {str(e)}")

    # Extract chunks
    chunks_path = os.path.join(PROCESSED_DIR, "doc_chunks.json")
    chunks = extract_chunks(structured_docs, chunks_path)

    # Add tags
    corpus_path = os.path.join(PROCESSED_DIR, "doc_corpus.json")
    tagged_chunks = add_tags(chunks, corpus_path)

    logger.info(f"Processing complete in {time.time() - start_time:.2f}s")
    return tagged_chunks


if __name__ == "__main__":
    process_documents()
