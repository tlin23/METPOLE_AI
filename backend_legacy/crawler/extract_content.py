import os
import json
from unstructured.partition.html import partition_html
from langchain.text_splitter import RecursiveCharacterTextSplitter
from keybert import KeyBERT
from backend_legacy.crawler.utils import (
    clean_text,
    hash_id,
    extract_tags_with_keybert,
)
from backend_legacy.configer.logging_config import get_logger


logger = get_logger("crawler.extract_content")


def extract_chunks_without_tags(
    input_dir,
    output_path,
):
    """
    Extract chunks from HTML files in the input directory and save them to a JSON file.
    Each chunk is a dictionary containing the chunk ID, page ID, page name, page title,
    section header, and content.
    """
    print("Extracting chunks from HTML files...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.isfile(output_path):
        os.remove(output_path)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    all_chunks = []
    seen_hashes = set()

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

            elements = partition_html(text=html)
            full_text = "\n".join([el.text for el in elements if hasattr(el, "text")])
            chunks = text_splitter.split_text(full_text)

            page_name = file.replace(".html", "")
            document_id = hash_id(page_name)
            document_title = (
                f"metropoleballard.com - {page_name.split('_')[-1].capitalize()}"
            )
            document_name = page_name

            for chunk_text in chunks:
                chunk_text = clean_text(chunk_text)
                chunk_id = hash_id(chunk_text)
                if chunk_id in seen_hashes or len(chunk_text) < 20:
                    continue

                all_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "document_id": document_id,
                        "document_title": document_title,
                        "document_name": document_name,
                        "section": "Auto",
                        "content": chunk_text,
                    }
                )
                seen_hashes.add(chunk_id)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"[extract_content.py] Extracted {len(all_chunks)} chunks to {output_path}")
    return all_chunks


def add_tags_to_chunks(
    input_path,
    output_path,
):
    """
    Add tags to chunks using KeyBERT and save the updated chunks to a new JSON file.
    Each chunk is a dictionary containing the chunk ID, page ID, page name, page title,
    section header, content, and tags.
    """
    print("Adding tags to chunks...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.isfile(output_path):
        os.remove(output_path)

    print("Loading KeyBERT model for tag extraction...")
    model = KeyBERT(model="all-MiniLM-L6-v2")

    with open(input_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    for chunk in chunks:
        chunk["tags"] = extract_tags_with_keybert(chunk["content"], model)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)

    print(f"[extract_content.py] Added tags to chunks and saved to {output_path}")
    return chunks
