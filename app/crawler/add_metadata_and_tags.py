"""
Script to add metadata and tags to content chunks.

This script:
1. Loads content objects from data/processed/content_objects.py
2. Assigns a page_id, section header, and unique chunk_id to each chunk
3. Uses KeyBERT + MiniLM to extract 3-5 tags per chunk
4. Stores everything in a structured JSON file named metropole_corpus.json
"""

import os
import sys
import json
import uuid
from typing import List, Dict, Any
from keybert import KeyBERT

# Add the project root to the Python path to allow importing from data/processed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from data.processed.content_objects import content_objects

    print(f"Successfully loaded {len(content_objects)} content objects")
except ImportError:
    print(
        "Error: Could not import content_objects. Make sure to run process_html_content.py first."
    )
    sys.exit(1)


def generate_page_ids(content_objects: List[Dict[str, Any]]) -> Dict[str, str]:
    """
    Generate unique page IDs for each unique page name.

    Args:
        content_objects (List[Dict[str, Any]]): List of content objects.

    Returns:
        Dict[str, str]: Dictionary mapping page names to page IDs.
    """
    # Get unique page names
    page_names = set(chunk["page_name"] for chunk in content_objects)

    # Generate a unique ID for each page name
    page_ids = {}
    for page_name in page_names:
        # Use a shortened UUID as the page ID
        page_ids[page_name] = f"page_{str(uuid.uuid4())[:8]}"

    return page_ids


def extract_tags_with_keybert(
    text: str, model: KeyBERT, num_tags: int = 5
) -> List[str]:
    """
    Extract tags from text using KeyBERT with MiniLM.

    Args:
        text (str): Text to extract tags from.
        model (KeyBERT): KeyBERT model instance.
        num_tags (int, optional): Number of tags to extract. Defaults to 5.

    Returns:
        List[str]: List of extracted tags.
    """
    # Skip empty or very short text
    if not text or len(text) < 20:
        return []

    # Extract keywords
    keywords = model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 2),  # Extract single words and bigrams
        stop_words="english",
        use_mmr=True,  # Use Maximal Marginal Relevance to diversify results
        diversity=0.7,  # Higher diversity means more diverse results
        top_n=num_tags,
    )

    # Return just the keywords (not the scores)
    return [keyword for keyword, _ in keywords]


def process_content_objects() -> List[Dict[str, Any]]:
    """
    Process content objects to add metadata and tags.

    Returns:
        List[Dict[str, Any]]: List of processed content objects with metadata and tags.
    """
    # Initialize KeyBERT with MiniLM
    print("Initializing KeyBERT with MiniLM model...")
    model = KeyBERT(model="all-MiniLM-L6-v2")

    # Generate page IDs
    page_ids = generate_page_ids(content_objects)

    # Process each content object
    processed_objects = []

    print(f"Processing {len(content_objects)} content objects...")
    for i, chunk in enumerate(content_objects):
        # Generate a unique chunk ID
        chunk_id = f"chunk_{str(uuid.uuid4())}"

        # Get the page ID for this chunk
        page_id = page_ids[chunk["page_name"]]

        # Extract tags using KeyBERT
        tags = extract_tags_with_keybert(chunk["content"], model)

        # Create a processed object with metadata and tags
        processed_object = {
            "chunk_id": chunk_id,
            "page_id": page_id,
            "page_title": chunk["page_title"],
            "page_name": chunk["page_name"],
            "section_header": chunk["section_header"],
            "content": chunk["content"],
            "content_html": chunk["content_html"],
            "tags": tags,
        }

        processed_objects.append(processed_object)

        # Print progress every 10 chunks
        if (i + 1) % 10 == 0:
            print(f"Processed {i + 1}/{len(content_objects)} chunks")

    return processed_objects


def save_to_json(processed_objects: List[Dict[str, Any]], output_path: str) -> None:
    """
    Save processed objects to a JSON file.

    Args:
        processed_objects (List[Dict[str, Any]]): List of processed content objects.
        output_path (str): Path to save the JSON file.
    """
    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(processed_objects, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(processed_objects)} processed objects to {output_path}")


def main():
    """Main function to process content objects and save to JSON."""
    # Process content objects
    processed_objects = process_content_objects()

    # Save to JSON
    output_path = os.path.join("data", "processed", "metropole_corpus.json")
    save_to_json(processed_objects, output_path)

    # Print summary
    page_count = len(set(obj["page_id"] for obj in processed_objects))
    section_count = len(set(obj["section_header"] for obj in processed_objects))
    tag_count = sum(len(obj["tags"]) for obj in processed_objects)

    print("\nSummary:")
    print(f"- Processed {len(processed_objects)} content chunks")
    print(f"- From {page_count} unique pages")
    print(f"- With {section_count} unique sections")
    print(
        f"- Generated {tag_count} tags (avg. {tag_count/len(processed_objects):.1f} per chunk)"
    )


if __name__ == "__main__":
    main()
