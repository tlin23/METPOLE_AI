"""
Example script demonstrating how to use the extracted content.
"""

import os
import sys

# Add the project root to the Python path to allow importing from data/processed
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

try:
    from data.processed.content_objects import content_objects
    print(f"Successfully loaded {len(content_objects)} content objects")
except ImportError:
    print("Error: Could not import content_objects. Make sure to run process_html_content.py first.")
    sys.exit(1)


def print_content_summary():
    """Print a summary of the content objects."""
    # Count unique pages and sections
    pages = set(chunk['page_name'] for chunk in content_objects)
    sections = set(chunk['section_header'] for chunk in content_objects)
    
    print(f"\nContent Summary:")
    print(f"- Total chunks: {len(content_objects)}")
    print(f"- Unique pages: {len(pages)}")
    print(f"- Unique sections: {len(sections)}")
    
    # Print the first few pages and sections
    print("\nPages:")
    for page in sorted(list(pages))[:5]:
        print(f"  - {page}")
    if len(pages) > 5:
        print(f"  - ... and {len(pages) - 5} more")
    
    print("\nSections:")
    for section in sorted(list(sections))[:5]:
        print(f"  - {section}")
    if len(sections) > 5:
        print(f"  - ... and {len(sections) - 5} more")


def search_content(query):
    """
    Search for content containing the query string.
    
    Args:
        query (str): The search query.
        
    Returns:
        list: List of matching content chunks.
    """
    query = query.lower()
    results = []
    
    for chunk in content_objects:
        if query in chunk['content'].lower():
            results.append(chunk)
    
    return results


def get_content_by_section(section_header):
    """
    Get all content from a specific section.
    
    Args:
        section_header (str): The section header to filter by.
        
    Returns:
        list: List of content chunks from the specified section.
    """
    return [chunk for chunk in content_objects if chunk['section_header'] == section_header]


def get_content_by_page(page_name):
    """
    Get all content from a specific page.
    
    Args:
        page_name (str): The page name to filter by.
        
    Returns:
        list: List of content chunks from the specified page.
    """
    return [chunk for chunk in content_objects if chunk['page_name'] == page_name]


def main():
    """Main function demonstrating usage of the content objects."""
    print_content_summary()
    
    # Example 1: Search for content containing "security"
    print("\nExample 1: Search for 'security'")
    security_results = search_content("security")
    print(f"Found {len(security_results)} chunks containing 'security'")
    if security_results:
        print("First result:")
        print(f"  Page: {security_results[0]['page_title']}")
        print(f"  Section: {security_results[0]['section_header']}")
        print(f"  Content: {security_results[0]['content'][:100]}...")
    
    # Example 2: Get content from a specific section
    print("\nExample 2: Get content from 'Security' section")
    security_section = get_content_by_section("Security")
    print(f"Found {len(security_section)} chunks in 'Security' section")
    
    # Example 3: Get content from a specific page
    print("\nExample 3: Get content from 'manual' page")
    manual_page = get_content_by_page("www.metropoleballard.com_manual")
    print(f"Found {len(manual_page)} chunks in 'manual' page")
    
    # Example 4: Combine filters
    print("\nExample 4: Get content about 'water' from 'manual' page")
    water_in_manual = [chunk for chunk in manual_page if "water" in chunk['content'].lower()]
    print(f"Found {len(water_in_manual)} chunks about 'water' in 'manual' page")
    if water_in_manual:
        print("First result:")
        print(f"  Section: {water_in_manual[0]['section_header']}")
        print(f"  Content: {water_in_manual[0]['content'][:100]}...")


if __name__ == "__main__":
    main()
