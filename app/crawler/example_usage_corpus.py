"""
Example script demonstrating how to use the processed corpus with metadata and tags.
"""

import os
import sys
import json
from typing import List, Dict, Any

# Path to the processed corpus
CORPUS_PATH = os.path.join('data', 'processed', 'metropole_corpus.json')


def load_corpus() -> List[Dict[str, Any]]:
    """
    Load the processed corpus from JSON.
    
    Returns:
        List[Dict[str, Any]]: List of processed content objects.
    """
    try:
        with open(CORPUS_PATH, 'r', encoding='utf-8') as f:
            corpus = json.load(f)
        print(f"Successfully loaded {len(corpus)} content objects from {CORPUS_PATH}")
        return corpus
    except FileNotFoundError:
        print(f"Error: Could not find {CORPUS_PATH}. Make sure to run add_metadata_and_tags.py first.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Could not parse {CORPUS_PATH}. The file may be corrupted.")
        sys.exit(1)


def print_corpus_summary(corpus: List[Dict[str, Any]]) -> None:
    """
    Print a summary of the corpus.
    
    Args:
        corpus (List[Dict[str, Any]]): List of processed content objects.
    """
    # Count unique pages, sections, and tags
    pages = set(chunk['page_id'] for chunk in corpus)
    sections = set(chunk['section_header'] for chunk in corpus)
    all_tags = [tag for chunk in corpus for tag in chunk['tags']]
    unique_tags = set(all_tags)
    
    print(f"\nCorpus Summary:")
    print(f"- Total chunks: {len(corpus)}")
    print(f"- Unique pages: {len(pages)}")
    print(f"- Unique sections: {len(sections)}")
    print(f"- Total tags: {len(all_tags)}")
    print(f"- Unique tags: {len(unique_tags)}")
    print(f"- Average tags per chunk: {len(all_tags) / len(corpus):.1f}")
    
    # Print the most common tags
    tag_counts = {}
    for tag in all_tags:
        tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    print("\nMost common tags:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  - {tag}: {count} occurrences")


def search_by_tag(corpus: List[Dict[str, Any]], tag: str) -> List[Dict[str, Any]]:
    """
    Search for content chunks with a specific tag.
    
    Args:
        corpus (List[Dict[str, Any]]): List of processed content objects.
        tag (str): Tag to search for.
        
    Returns:
        List[Dict[str, Any]]: List of matching content chunks.
    """
    return [chunk for chunk in corpus if tag in chunk['tags']]


def search_by_content(corpus: List[Dict[str, Any]], query: str) -> List[Dict[str, Any]]:
    """
    Search for content chunks containing a specific query string.
    
    Args:
        corpus (List[Dict[str, Any]]): List of processed content objects.
        query (str): Query string to search for.
        
    Returns:
        List[Dict[str, Any]]: List of matching content chunks.
    """
    query = query.lower()
    return [chunk for chunk in corpus if query in chunk['content'].lower()]


def get_chunks_by_page(corpus: List[Dict[str, Any]], page_id: str) -> List[Dict[str, Any]]:
    """
    Get all content chunks from a specific page.
    
    Args:
        corpus (List[Dict[str, Any]]): List of processed content objects.
        page_id (str): Page ID to filter by.
        
    Returns:
        List[Dict[str, Any]]: List of content chunks from the specified page.
    """
    return [chunk for chunk in corpus if chunk['page_id'] == page_id]


def get_chunks_by_section(corpus: List[Dict[str, Any]], section_header: str) -> List[Dict[str, Any]]:
    """
    Get all content chunks from a specific section.
    
    Args:
        corpus (List[Dict[str, Any]]): List of processed content objects.
        section_header (str): Section header to filter by.
        
    Returns:
        List[Dict[str, Any]]: List of content chunks from the specified section.
    """
    return [chunk for chunk in corpus if chunk['section_header'] == section_header]


def print_chunk_details(chunk: Dict[str, Any]) -> None:
    """
    Print details of a content chunk.
    
    Args:
        chunk (Dict[str, Any]): Content chunk.
    """
    print(f"Chunk ID: {chunk['chunk_id']}")
    print(f"Page: {chunk['page_title']} (ID: {chunk['page_id']})")
    print(f"Section: {chunk['section_header']}")
    print(f"Tags: {', '.join(chunk['tags'])}")
    print(f"Content: {chunk['content'][:100]}..." if len(chunk['content']) > 100 else f"Content: {chunk['content']}")
    print()


def main():
    """Main function demonstrating usage of the processed corpus."""
    # Load the corpus
    corpus = load_corpus()
    
    # Print corpus summary
    print_corpus_summary(corpus)
    
    # Example 1: Search for content by tag
    print("\nExample 1: Search for content with tag 'security'")
    security_results = search_by_tag(corpus, "security")
    print(f"Found {len(security_results)} chunks with tag 'security'")
    if security_results:
        print("First result:")
        print_chunk_details(security_results[0])
    
    # Example 2: Search for content by text
    print("\nExample 2: Search for content containing 'water'")
    water_results = search_by_content(corpus, "water")
    print(f"Found {len(water_results)} chunks containing 'water'")
    if water_results:
        print("First result:")
        print_chunk_details(water_results[0])
    
    # Example 3: Get content from a specific page
    if corpus:
        # Get the first page ID as an example
        example_page_id = corpus[0]['page_id']
        print(f"\nExample 3: Get content from page with ID '{example_page_id}'")
        page_results = get_chunks_by_page(corpus, example_page_id)
        print(f"Found {len(page_results)} chunks in page with ID '{example_page_id}'")
        
        # Example 4: Get content from a specific section
        if page_results:
            # Get the first section header as an example
            example_section = page_results[0]['section_header']
            print(f"\nExample 4: Get content from section '{example_section}'")
            section_results = get_chunks_by_section(corpus, example_section)
            print(f"Found {len(section_results)} chunks in section '{example_section}'")
    
    # Example 5: Find chunks with multiple specific tags
    print("\nExample 5: Find chunks with both 'building' and 'maintenance' tags")
    building_maintenance = [
        chunk for chunk in corpus 
        if "building" in chunk['tags'] and "maintenance" in chunk['tags']
    ]
    print(f"Found {len(building_maintenance)} chunks with both 'building' and 'maintenance' tags")
    if building_maintenance:
        print("First result:")
        print_chunk_details(building_maintenance[0])


if __name__ == "__main__":
    main()
