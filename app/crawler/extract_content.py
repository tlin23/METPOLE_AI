"""
Module for extracting structured content from HTML files.
"""

import os
from bs4.element import Tag
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional


def extract_structured_content(html_file_path: str) -> Dict[str, Any]:
    """
    Extract structured content from an HTML file.

    Args:
        html_file_path (str): Path to the HTML file.

    Returns:
        Dict[str, Any]: Dictionary containing page title and content chunks.
    """
    with open(html_file_path, "r", encoding="utf-8") as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, "html.parser")

    # Extract page title
    title = extract_page_title(soup)

    # Extract sections and content
    sections = extract_sections(soup)

    return {"title": title, "sections": sections}


def extract_page_title(soup: BeautifulSoup) -> str:
    """
    Extract the page title from the HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        str: Page title.
    """
    # Try to get title from meta tags first
    meta_title = soup.find("meta", property="og:title")
    if meta_title and meta_title.get("content"):
        return meta_title.get("content")

    # Try to get from title tag
    title_tag = soup.find("title")
    if title_tag and title_tag.text:
        return title_tag.text

    # Try to get from h1 tags
    h1_tag = soup.find("h1")
    if h1_tag and h1_tag.text:
        return h1_tag.text.strip()

    # Default to filename if no title found
    return os.path.basename(soup.title.string) if soup.title else "Untitled Page"


def is_block_level(tag: Tag) -> bool:
    return tag.name in ["p", "li", "h1", "h2", "h3"]


def extract_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    sections = []
    current_section = None

    content_elements = soup.find_all(["h1", "h2", "h3", "p", "li", "div", "span"])

    for element in content_elements:
        # New section if header
        if element.name in ["h1", "h2", "h3"]:
            if current_section and current_section["chunks"]:
                sections.append(current_section)
            current_section = {
                "header": element.get_text(strip=True),
                "header_html": str(element),
                "header_level": int(element.name[1]),
                "chunks": [],
            }
            continue

        # Only extract if not nested inside a block we've already processed
        if current_section is not None:
            # Only add chunks if it's not just nested clutter
            if element.name in ["p", "li"] or (
                element.name in ["div", "span"] and not element.find(is_block_level)
            ):
                raw_text = element.get_text(separator=" ", strip=True)
                if raw_text:
                    current_section["chunks"].append(
                        {
                            "content": raw_text,
                            "section_header": current_section["header"],
                        }
                    )

    if current_section and current_section["chunks"]:
        sections.append(current_section)

    return sections


def find_main_content_area(soup: BeautifulSoup) -> Optional[BeautifulSoup]:
    """
    Find the main content area of the page.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        Optional[BeautifulSoup]: Main content area, or None if not found.
    """
    # Look for common main content identifiers
    main_content_candidates = [
        # Look for role="main"
        soup.find(attrs={"role": "main"}),
        # Look for main tag
        soup.find("main"),
        # Look for common content div classes
        soup.find("div", class_="UtePc"),
        soup.find("div", class_="RCETm"),
        # Look for article tag
        soup.find("article"),
        # Look for section tags
        soup.find("section"),
    ]

    # Return the first non-None candidate
    for candidate in main_content_candidates:
        if candidate:
            return candidate

    # If no candidate found, return None
    return None


def should_skip_element(element) -> bool:
    """
    Determine if an element should be skipped (not included in content).

    Args:
        element: HTML element.

    Returns:
        bool: True if the element should be skipped, False otherwise.
    """
    return False
    # Skip empty elements
    if not element.get_text(strip=True):
        return True

    # Skip script, style, and other non-content elements
    if element.name in ["script", "style", "meta", "link", "noscript"]:
        return True

    # Skip elements that are likely navigation, footer, etc.
    skip_classes = [
        "navigation",
        "footer",
        "header",
        "nav",
        "menu",
        "sidebar",
        "BbxBP",
        "JzO0Vc",
        "VLoccc",
        "zDUgLc",
        "TxnWlb",
        "dZA9kd",
        "LqzjUe",
        "hBW7Hb",
        "YkaBSd",
    ]

    if element.has_attr("class"):
        element_classes = " ".join(element.get("class", []))
        for cls in skip_classes:
            if cls in element_classes:
                return True

    # Skip elements with specific IDs
    skip_ids = ["header", "footer", "navigation", "menu", "sidebar"]
    if element.has_attr("id") and element["id"] in skip_ids:
        return True

    # Skip elements that are likely not part of the main content
    parent = element.parent
    while parent:
        if parent.name in ["nav", "footer", "header"]:
            return True
        if parent.has_attr("class"):
            parent_classes = " ".join(parent.get("class", []))
            for cls in skip_classes:
                if cls in parent_classes:
                    return True
        parent = parent.parent

    return False


def process_all_html_files(directory: str) -> Dict[str, Dict[str, Any]]:
    """
    Process all HTML files in a directory and extract structured content.

    Args:
        directory (str): Directory containing HTML files.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary mapping file paths to structured content.
    """
    raw_results = {}

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            try:
                raw_results[file_path] = extract_structured_content(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        # Deduplicate chunks across all pages/sections
    deduped_results = {}
    seen_chunks = set()

    for file_path, page in raw_results.items():
        deduped_sections = []
        for section in page["sections"]:
            deduped_chunks = []
            for chunk in section["chunks"]:
                key = f"{file_path}:{section['header']}:{chunk['content'].strip()}"
                if key not in seen_chunks:
                    seen_chunks.add(key)
                    deduped_chunks.append(chunk)
            if deduped_chunks:
                deduped_sections.append({**section, "chunks": deduped_chunks})
        deduped_results[file_path] = {**page, "sections": deduped_sections}

    return deduped_results


if __name__ == "__main__":
    # Example usage
    html_directory = "data/html"

    output_directory = "data/processed"

    results = process_all_html_files(html_directory)

    # Save results to JSON file
    json_output_path = os.path.join(output_directory, "extracted_content.json")
    with open(json_output_path, "w", encoding="utf-8") as f:
        import json

        json.dump(results, f, indent=2, ensure_ascii=False)

    # Print summary
    print(f"Processed {len(results)} HTML files")
    for file_path, content in results.items():
        print(f"\nFile: {file_path}")
        print(f"Title: {content['title']}")
        print(f"Sections: {len(content['sections'])}")

        # Print first section as an example
        if content["sections"]:
            first_section = content["sections"][0]
            print(f"First section header: {first_section['header']}")
            print(f"Number of chunks: {len(first_section['chunks'])}")
            if first_section["chunks"]:
                print(
                    f"First chunk content: {first_section['chunks'][0]['content'][:100]}..."
                )
