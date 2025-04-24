import os
import json
import hashlib
from bs4 import BeautifulSoup
import re
from collections import Counter
from keybert import KeyBERT
import uuid
from ftfy import fix_text


def clean_text(text: str) -> str:
    # Fix garbled Unicode (e.g., \u2019 to ’)
    text = fix_text(text)

    # Remove invisible/control characters (e.g., zero-width space)
    text = re.sub(r"[\u200b\u200e\u200f\u202a-\u202e]", "", text)

    # Normalize smart punctuation
    text = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("…", "...")
    )

    # Remove all newlines and surrounding whitespace
    text = re.sub(r"\s*\n\s*", " ", text)  # flatten all newlines
    text = re.sub(r"\s+", " ", text)  # collapse multiple spaces

    return text.strip()


def is_repetitive(text, threshold=0.3):
    words = text.split()
    if len(words) < 10:
        return False
    common = Counter(words)
    most_common = common.most_common(1)[0]
    return most_common[1] / len(words) > threshold


def normalize(text: str) -> str:
    """Normalize text by lowercasing, removing symbols, and collapsing spaces."""
    text = text.lower()
    text = re.sub(r"\W+", " ", text)  # Remove non-word chars
    return " ".join(text.split())  # Remove extra spaces


def hash_id(text):
    normalized = normalize(text)
    return "chunk_" + hashlib.md5(normalized.encode("utf-8")).hexdigest()


def extract_tags_with_keybert(text, model, num_tags=5):
    text = text.strip()
    if not text or len(text.split()) < 10:
        return []
    keywords = model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),
        stop_words="english",
        use_mmr=True,
        diversity=0.7,
        top_n=num_tags,
    )
    return [kw for kw, _ in keywords]


def extract_chunks_from_html(
    html, page_name, page_title, page_id, seen_hashes, max_tokens=500
):
    soup = BeautifulSoup(html, "html.parser")
    chunks = []
    current_header = None
    current_text = ""

    def flush_chunk():
        nonlocal current_text
        content = current_text.strip()

        if not content or len(content) < 20:
            current_text = ""
            return

        # Deduplicate
        chunk_hash = hash_id(content)
        if chunk_hash in seen_hashes:
            current_text = ""
            return

        # Reject overly repetitive content
        if is_repetitive(content):
            current_text = ""
            return

        # Reject low diversity (already exists)
        unique_words = set(normalize(content).split())
        if len(unique_words) < 5:
            current_text = ""
            return

        chunks.append(
            {
                "chunk_id": chunk_hash,
                "page_id": page_id,
                "page_name": page_name,
                "page_title": page_title,
                "section_header": current_header or "No header",
                "content": clean_text(content),
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
    print("Initializing KeyBERT with MiniLM model...")
    model = KeyBERT(model="all-MiniLM-L6-v2")

    all_chunks = []
    page_ids = {}
    seen_hashes = set()

    for root, _, files in os.walk(input_dir):
        for file in files:
            if not file.endswith(".html"):
                continue

            file_path = os.path.join(root, file)
            with open(file_path, "r", encoding="utf-8") as f:
                html = f.read()

            page_name = file.replace(".html", "")
            page_id = page_ids.setdefault(page_name, f"page_{str(uuid.uuid4())[:8]}")
            page_title = (
                f"metropoleballard.com - {page_name.split('_')[-1].capitalize()}"
            )

            raw_chunks = extract_chunks_from_html(
                html, page_name, page_title, page_id, seen_hashes
            )
            for chunk in raw_chunks:
                # Add unique chunk_id and tags
                chunk["tags"] = extract_tags_with_keybert(chunk["content"], model)
                all_chunks.append(chunk)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print(f"[extract_content.py] Extracted {len(all_chunks)} chunks to {output_path}")
    return all_chunks


if __name__ == "__main__":
    html_directory = "data/html"
    output_directory = "data/processed"
    os.makedirs(output_directory, exist_ok=True)
    output_file = os.path.join(output_directory, "metropole_corpus.json")
    process_all_html_files(html_directory, output_file)
    print(f"[extract_content.py] Processed HTML files and saved to {output_file}")
