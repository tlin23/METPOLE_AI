# app/crawler/utils.py

import re
import hashlib
from ftfy import fix_text
from keybert import KeyBERT


def clean_text(text: str) -> str:
    """Clean and normalize text by fixing encoding, stripping special characters, and collapsing whitespace."""
    text = fix_text(text)
    text = re.sub(r"[\u200b\u200e\u200f\u202a-\u202e]", "", text)  # invisible chars
    text = (
        text.replace("“", '"')
        .replace("”", '"')
        .replace("‘", "'")
        .replace("’", "'")
        .replace("–", "-")
        .replace("—", "-")
        .replace("…", "...")
    )
    text = re.sub(r"\s*\n\s*", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\W+", " ", text)
    return " ".join(text.split())


def hash_id(text: str) -> str:
    normalized = normalize(text)
    return "chunk_" + hashlib.md5(normalized.encode("utf-8")).hexdigest()


def extract_tags_with_keybert(text: str, model: KeyBERT, num_tags: int = 5) -> list:
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
