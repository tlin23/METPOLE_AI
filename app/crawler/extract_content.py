import os
import json
import hashlib
from bs4 import BeautifulSoup
import re


def normalize(text: str) -> str:
    """Normalize text by lowercasing, removing symbols, and collapsing spaces."""
    text = text.lower()
    text = re.sub(r"\W+", " ", text)  # Remove non-word chars
    return " ".join(text.split())  # Remove extra spaces


def clean_text(text):
    return " ".join(text.split())


def hash_id(text):
    normalized = normalize(text)
    return "chunk_" + hashlib.md5(normalized.encode("utf-8")).hexdigest()


def extract_chunks_from_html(html, page_name, page_title, page_id, max_tokens=500):
    soup = BeautifulSoup(html, "html.parser")
    chunks = []
    current_header = None
    current_text = ""
    seen_hashes = set()

    def flush_chunk():
        nonlocal current_text
        content = current_text.strip()

        if not content or len(content) < 50:
            current_text = ""
            return

        # Hash the normalized version for deduplication
        chunk_hash = hash_id(content)

        if chunk_hash in seen_hashes:
            current_text = ""
            return

        # Optional: reject overly repetitive chunks
        unique_words = set(normalize(content).split())
        if len(unique_words) < 5:
            current_text = ""
            return

        # Add chunk
        chunks.append(
            {
                "chunk_id": chunk_hash,
                "page_id": page_id,
                "page_name": page_name,
                "page_title": page_title,
                "section_header": current_header or "No header",
                "content": content,
                "tags": [],
            }
        )
        seen_hashes.add(chunk_hash)
        current_text = ""

    def token_count(text):
        # Approximate token count (adjust if needed)
        return len(text.split())

    for el in soup.find_all(["h1", "h2", "h3", "p", "li"]):
        text = clean_text(el.get_text())
        if not text or len(text) < 5:
            continue

        if el.name in ["h1", "h2", "h3"]:
            flush_chunk()
            current_header = text
        else:
            if token_count(current_text + text) > max_tokens:
                flush_chunk()
            current_text += text + "\n"

    flush_chunk()
    return chunks


def process_all_html_files(
    input_dir="data/html", output_path="data/processed/metropole_corpus.json"
):
    all_chunks = []
    grouped_by_file = {}

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

            page_name = file.replace(".html", "")
            page_id = "page_" + hashlib.md5(page_name.encode("utf-8")).hexdigest()
            page_title = (
                f"metropoleballard.com - {page_name.split('_')[-1].capitalize()}"
            )

            chunks = extract_chunks_from_html(html, page_name, page_title, page_id)
            grouped_by_file[file_path] = chunks
            all_chunks.extend(chunks)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"[extract_content.py] Extracted {len(all_chunks)} chunks to {output_path}")
    return grouped_by_file


if __name__ == "__main__":
    html_directory = "data/html"
    output_directory = "data/processed"
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "metropole_corpus.json")
    process_all_html_files(html_directory, output_file)
    print(f"[extract_content.py] Processed HTML files and saved to {output_file}")
