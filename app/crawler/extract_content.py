"""
Module for extracting structured content from HTML files.
"""

import os
from bs4 import BeautifulSoup
import re
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


def extract_sections(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Extract sections with headers and content from the HTML.

    Args:
        soup (BeautifulSoup): Parsed HTML.

    Returns:
        List[Dict[str, Any]]: List of sections with headers and content.
    """
    sections = []
    current_section = None

    # First, try to find the main content area
    main_content = find_main_content_area(soup)

    if main_content:
        # Find all headers (h1, h2, h3) and content elements (p, li) within the main content
        content_elements = main_content.find_all(["h1", "h2", "h3", "p", "li", "div"])
    else:
        # Fallback to searching the entire document
        content_elements = soup.find_all(["h1", "h2", "h3", "p", "li"])

    for element in content_elements:
        # Skip elements that are likely not part of the main content
        if should_skip_element(element):
            continue

        # If it's a div, check if it contains paragraph text
        if element.name == "div" and element.get_text(strip=True):
            # Only process divs with specific classes that likely contain content
            if not (
                element.has_attr("class")
                and any(
                    cls in ["tyJCtd", "mGzaTb", "Depvyb", "baZpAe", "zfr3Q"]
                    for cls in element.get("class", [])
                )
            ):
                continue

            # Skip if it's just a container with no direct text
            if not any(child.name in ["p", "span"] for child in element.children):
                continue

        # If we find a header, start a new section
        if element.name in ["h1", "h2", "h3"]:
            # If we have a current section with content, add it to the list
            if current_section and current_section["chunks"]:
                sections.append(current_section)

            # Start a new section
            current_section = {
                "header": element.get_text(strip=True),
                "header_html": str(element),
                "header_level": int(element.name[1]),
                "chunks": [],
            }
        # If we have content and a current section, add it to the current section
        elif current_section is not None:
            # Skip empty content
            if not element.get_text(strip=True):
                continue

            # Create a chunk with the content
            chunk = {
                "content": element.get_text(strip=True),
                "content_html": str(element),
                "section_header": current_section["header"],
            }
            current_section["chunks"].append(chunk)
        # If we have content but no current section, create a default section
        elif element.get_text(strip=True):
            current_section = {
                "header": "Introduction",
                "header_html": "<h2>Introduction</h2>",
                "header_level": 2,
                "chunks": [
                    {
                        "content": element.get_text(strip=True),
                        "content_html": str(element),
                        "section_header": "Introduction",
                    }
                ],
            }

    # Add the last section if it exists
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
    results = {}

    for filename in os.listdir(directory):
        if filename.endswith(".html"):
            file_path = os.path.join(directory, filename)
            try:
                results[file_path] = extract_structured_content(file_path)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

    return results


if __name__ == "__main__":
    # Example usage
    html_directory = "data/html"
    results = process_all_html_files(html_directory)

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
