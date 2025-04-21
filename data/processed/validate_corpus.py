#!/usr/bin/env python3
"""
Script to validate the metropole_corpus.json file.

This script provides a simple way to validate the corpus without running the full test suite.
It can be used for quick validation or for integration into other scripts.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Tuple, Set


def validate_corpus(corpus_path: str, verbose: bool = False) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate the corpus file.
    
    Args:
        corpus_path (str): Path to the corpus file.
        verbose (bool): Whether to print verbose output.
        
    Returns:
        Tuple[bool, Dict[str, Any]]: A tuple containing a boolean indicating whether the validation
                                    passed and a dictionary with validation statistics.
    """
    # Check if the file exists
    if not os.path.exists(corpus_path):
        print(f"Error: Corpus file not found at {corpus_path}")
        return False, {}
    
    # Statistics
    stats = {
        'total_chunks': 0,
        'chunks_with_missing_fields': 0,
        'chunks_with_tags': 0,
        'duplicate_chunk_ids': 0,
        'invalid_chunk_id_format': 0,
        'invalid_page_id_format': 0,
        'inconsistent_page_ids': 0,
    }
    
    # Required fields
    required_fields = [
        'chunk_id', 'page_id', 'page_title', 'page_name', 
        'section_header', 'content', 'content_html', 'tags'
    ]
    
    # Sets to track uniqueness
    chunk_ids = set()
    page_name_to_id = {}
    
    # Load the corpus
    try:
        with open(corpus_path, 'rb') as f:
            corpus = json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Could not parse {corpus_path}. The file may be corrupted.")
        return False, {}
    
    if not isinstance(corpus, list):
        print(f"Error: Corpus should be a list of objects, but got {type(corpus)}")
        return False, {}
    
    # Validate each chunk
    for i, chunk in enumerate(corpus):
        stats['total_chunks'] += 1
        
        # Check required fields
        missing_fields = [field for field in required_fields if field not in chunk]
        if missing_fields:
            stats['chunks_with_missing_fields'] += 1
            if verbose:
                print(f"Warning: Chunk at index {i} is missing fields: {missing_fields}")
            continue  # Skip further validation for this chunk
        
        # Check chunk_id uniqueness
        chunk_id = chunk['chunk_id']
        if chunk_id in chunk_ids:
            stats['duplicate_chunk_ids'] += 1
            if verbose:
                print(f"Warning: Duplicate chunk_id found: {chunk_id}")
        chunk_ids.add(chunk_id)
        
        # Check chunk_id format
        if not chunk_id.startswith('chunk_'):
            stats['invalid_chunk_id_format'] += 1
            if verbose:
                print(f"Warning: Chunk ID at index {i} should start with 'chunk_': {chunk_id}")
        
        # Check page_id format
        page_id = chunk['page_id']
        if not page_id.startswith('page_'):
            stats['invalid_page_id_format'] += 1
            if verbose:
                print(f"Warning: Page ID at index {i} should start with 'page_': {page_id}")
        
        # Check page_id consistency
        page_name = chunk['page_name']
        if page_name in page_name_to_id:
            if page_name_to_id[page_name] != page_id:
                stats['inconsistent_page_ids'] += 1
                if verbose:
                    print(f"Warning: Inconsistent page_id for page '{page_name}': "
                          f"'{page_name_to_id[page_name]}' vs '{page_id}'")
        else:
            page_name_to_id[page_name] = page_id
        
        # Check tags are generated for chunks with sufficient content
        if len(chunk['content']) > 20 and len(chunk['tags']) > 0:
            stats['chunks_with_tags'] += 1
    
    # Determine if validation passed
    validation_passed = (
        stats['chunks_with_missing_fields'] == 0 and
        stats['duplicate_chunk_ids'] == 0 and
        stats['invalid_chunk_id_format'] == 0 and
        stats['invalid_page_id_format'] == 0 and
        stats['inconsistent_page_ids'] == 0
    )
    
    return validation_passed, stats


def print_validation_results(validation_passed: bool, stats: Dict[str, Any]) -> None:
    """
    Print the validation results.
    
    Args:
        validation_passed (bool): Whether the validation passed.
        stats (Dict[str, Any]): Validation statistics.
    """
    print("\nValidation Results:")
    print(f"- Total chunks: {stats['total_chunks']}")
    print(f"- Chunks with tags: {stats['chunks_with_tags']}")
    print(f"- Chunks with missing fields: {stats['chunks_with_missing_fields']}")
    print(f"- Duplicate chunk IDs: {stats['duplicate_chunk_ids']}")
    print(f"- Invalid chunk ID format: {stats['invalid_chunk_id_format']}")
    print(f"- Invalid page ID format: {stats['invalid_page_id_format']}")
    print(f"- Inconsistent page IDs: {stats['inconsistent_page_ids']}")
    
    if validation_passed:
        print("\n✅ Validation Passed: The corpus is valid.")
    else:
        print("\n❌ Validation Failed: The corpus has issues that need to be fixed.")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Validate the metropole_corpus.json file.')
    parser.add_argument('--corpus-path', type=str, 
                        default='metropole_corpus.json',
                        help='Path to the corpus file')
    parser.add_argument('--verbose', action='store_true',
                        help='Print verbose output')
    
    args = parser.parse_args()
    
    print(f"Validating corpus file: {args.corpus_path}")
    validation_passed, stats = validate_corpus(args.corpus_path, args.verbose)
    print_validation_results(validation_passed, stats)
    
    # Exit with appropriate status code
    sys.exit(0 if validation_passed else 1)


if __name__ == '__main__':
    main()
