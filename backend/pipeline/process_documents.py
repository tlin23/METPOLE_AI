import os
import json
from pathlib import Path
from backend.configer.config import (
    OFFLINE_DOCS_DIR,
    DOC_TEXT_DIR as RAW_DOCS_DIR,
    OFFLINE_CHUNKS_JSON_PATH,
    OFFLINE_CORPUS_PATH,
    SUPPORTED_EXTENSIONS,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer
from backend.configer.logging_config import get_logger
from backend.pipeline.processors import PDFProcessor, DOCXProcessor
import hashlib

logger = get_logger("pipeline.process_documents")
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 100


def get_processor(file_path: Path):
    extension = file_path.suffix.lower()
    processors = {
        ".pdf": PDFProcessor(),
        ".docx": DOCXProcessor(),
    }
    return processors.get(extension)


def extract_structured_docs_from_files(
    input_dir=OFFLINE_DOCS_DIR,
    output_dir=RAW_DOCS_DIR,
):
    """
    Process all supported files in input_dir and save structured docs to output_dir as JSON.
    """
    logger.info(f"Extracting structured docs from files in {input_dir}...")
    os.makedirs(output_dir, exist_ok=True)
    docs_root = Path(input_dir)
    # Find all files to process first
    files_to_process = [
        f for f in docs_root.rglob("*") if f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    total_files = len(files_to_process)
    logger.info(f"Found {total_files} files to process.")
    count = 0
    for idx, file_path in enumerate(files_to_process, 1):
        processor = get_processor(file_path)
        if not processor:
            logger.warning(f"No processor for {file_path.suffix}, skipping {file_path}")
            continue
        try:
            structured_blocks = processor.process(file_path)
            doc_structure = {
                "metadata": {
                    "filename": file_path.name,
                    "file_type": file_path.suffix.lower(),
                    "sections": list(
                        set(block["section"] for block in structured_blocks)
                    ),
                },
                "content": structured_blocks,
            }
            output_file = Path(output_dir) / f"{file_path.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(doc_structure, f, indent=2, ensure_ascii=False)
            count += 1
            logger.info(f"[{idx}/{total_files}] Processed and saved: {output_file}")
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
    logger.info(f"Extracted structured docs from {count} files.")


def hash_id(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def extract_chunks_from_raw_docs(
    input_dir=RAW_DOCS_DIR,
    output_path=OFFLINE_CHUNKS_JSON_PATH,
):
    """
    Extract chunks from all structured JSON docs in input_dir and save to output_path.
    """
    logger.info(f"Extracting chunks from JSON files in {input_dir}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.isfile(output_path):
        os.remove(output_path)

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
        ],
        length_function=len,
        is_separator_regex=False,
    )

    all_chunks = []
    seen_hashes = set()
    raw_docs_dir = Path(input_dir)
    json_files = list(raw_docs_dir.glob("*.json"))
    logger.info(f"Found {len(json_files)} JSON files in {input_dir}")

    for file_path in json_files:
        with open(file_path, "r", encoding="utf-8") as f:
            doc = json.load(f)
        metadata = doc.get("metadata", {})
        blocks = doc.get("content", [])
        logger.info(f"Processing {file_path.name}: {len(blocks)} blocks")
        for block_idx, block in enumerate(blocks):
            content = block.get("content", "")
            if block.get("type") == "properties":
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
                    f"Skipping block {block_idx+1}: non-string content (type: {type(content)})"
                )
                continue

            chunks = text_splitter.split_text(content)
            logger.info(f"Block {block_idx+1}: split into {len(chunks)} chunks")

            for chunk in chunks:
                chunk = " ".join(chunk.split()).strip()
                if len(chunk) < 20 or chunk[0] in ".!?;:":
                    logger.debug(
                        f"Skipping short or punctuated chunk: '{chunk[:30]}...'"
                    )
                    continue

                chunk_id = hash_id(chunk)
                if chunk_id in seen_hashes:
                    continue
                seen_hashes.add(chunk_id)
                document_id = hash_id(metadata.get("filename", file_path.name))
                document_title = metadata.get("filename", file_path.name)
                document_name = Path(metadata.get("filename", file_path.name)).stem
                chunk_data = {
                    "chunk_id": chunk_id,
                    "document_id": document_id,
                    "document_title": document_title,
                    "document_name": document_name,
                    "section": block.get("section", "unknown"),
                    "source_file": metadata.get("filename", file_path.name),
                    "content": chunk,
                    "source_type": "document",
                }
                all_chunks.append(chunk_data)
        logger.info(f"{file_path.name}: total chunks so far: {len(all_chunks)}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    logger.info(
        f"Extracted {len(all_chunks)} chunks from {len(json_files)} documents to {output_path}"
    )
    return all_chunks


def add_tags_to_chunks(
    input_path=OFFLINE_CHUNKS_JSON_PATH,
    output_path=OFFLINE_CORPUS_PATH,
):
    """
    Add tags to chunks using KeyBERT and save to output_path.
    """
    logger.info(f"Adding tags to chunks in {input_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.isfile(output_path):
        os.remove(output_path)

    model = KeyBERT(model=SentenceTransformer("all-MiniLM-L6-v2"))

    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for idx, chunk in enumerate(chunks):
        logger.debug(
            f"Processing chunk {idx+1}/{len(chunks)}: {chunk.get('content', '')[:50]}..."
        )
        keywords = model.extract_keywords(
            chunk["content"],
            keyphrase_ngram_range=(1, 2),
            stop_words="english",
            top_n=5,
        )
        chunk["tags"] = [keyword[0] for keyword in keywords]
        logger.info(f"Chunk {idx+1}: tags={chunk['tags']}")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    logger.info(f"Tagging complete. Tagged chunks saved to {output_path}")
    return chunks
