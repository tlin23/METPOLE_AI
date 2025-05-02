# app/crawler/extract_content.py

import os
import json
import uuid
from unstructured.partition.html import partition_html
from langchain.text_splitter import RecursiveCharacterTextSplitter
from keybert import KeyBERT
from app.crawler.utils import (
    clean_text,
    hash_id,
    extract_tags_with_keybert,
)  # Move helpers to a utils module


def process_all_html_files(
    input_dir="app/data/html", output_path="app/data/processed/metropole_corpus.json"
):
    print("Initializing KeyBERT with MiniLM model...")
    model = KeyBERT(model="all-MiniLM-L6-v2")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)

    all_chunks = []
    seen_hashes = set()
    page_ids = {}

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
            page_id = page_ids.setdefault(page_name, f"page_{str(uuid.uuid4())[:8]}")
            page_title = (
                f"metropoleballard.com - {page_name.split('_')[-1].capitalize()}"
            )

            for chunk_text in chunks:
                chunk_text = clean_text(chunk_text)
                chunk_id = hash_id(chunk_text)
                if chunk_id in seen_hashes or len(chunk_text) < 20:
                    continue

                tags = extract_tags_with_keybert(chunk_text, model)
                all_chunks.append(
                    {
                        "chunk_id": chunk_id,
                        "page_id": page_id,
                        "page_name": page_name,
                        "page_title": page_title,
                        "section_header": "Auto",
                        "content": chunk_text,
                        "tags": tags,
                    }
                )
                seen_hashes.add(chunk_id)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"[extract_content.py] Extracted {len(all_chunks)} chunks to {output_path}")
    return all_chunks


if __name__ == "__main__":
    html_directory = "app/data/html"
    output_directory = "app/data/processed"
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "metropole_corpus.json")
    process_all_html_files(html_directory, output_file)
    print(f"[extract_content.py] Processed HTML files and saved to {output_file}")
