"""Crawler module for fetching and processing web content."""

import shutil
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from typing import Dict, List, Optional


def fetch_url(url: str) -> Optional[str]:
    """Fetch content from a URL.

    Args:
        url: The URL to fetch.

    Returns:
        The HTML content of the page if successful, None otherwise.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None


def parse_html(html: Optional[str]) -> Optional[BeautifulSoup]:
    """Parse HTML content using BeautifulSoup.

    Args:
        html: HTML content to parse.

    Returns:
        Parsed HTML as BeautifulSoup object if successful, None otherwise.
    """
    if html:
        return BeautifulSoup(html, "html.parser")
    return None


def extract_text(soup: Optional[BeautifulSoup]) -> Optional[str]:
    """Extract text content from parsed HTML.

    Args:
        soup: Parsed HTML as BeautifulSoup object.

    Returns:
        Extracted text content if successful, None otherwise.
    """
    if soup:
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()

        # Get text
        text = soup.get_text()

        # Break into lines and remove leading and trailing space on each
        lines = (line.strip() for line in text.splitlines())

        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))

        # Drop blank lines
        text = "\n".join(chunk for chunk in chunks if chunk)

        return text
    return None


def extract_links(soup: Optional[BeautifulSoup], base_url: str) -> List[str]:
    """Extract all internal links from a parsed HTML page.

    Args:
        soup: Parsed HTML as BeautifulSoup object.
        base_url: The base URL of the website.

    Returns:
        List of internal links found in the HTML.
    """
    if not soup:
        return []

    links = []
    base_domain = urllib.parse.urlparse(base_url).netloc
    parsed_base = urllib.parse.urlparse(base_url)

    for a_tag in soup.find_all("a"):
        if not hasattr(a_tag, "get") or not a_tag.get("href"):
            continue
        href = str(a_tag.get("href", ""))

        # Handle relative URLs
        if href.startswith("/"):
            # Convert relative URL to absolute
            parsed_base = urllib.parse.urlparse(base_url)
            absolute_url = f"{parsed_base.scheme}://{parsed_base.netloc}{href}"
            links.append(absolute_url)
        else:
            # Check if it's an internal link (same domain)
            parsed_href = urllib.parse.urlparse(href)
            if parsed_href.netloc == base_domain or not parsed_href.netloc:
                # If it's a fragment or query within the same page, skip
                if href.startswith("#") or href == "":
                    continue

                # If it's a relative path without leading slash
                if not parsed_href.netloc and not href.startswith("http"):
                    # Get the directory of the current URL
                    current_path = os.path.dirname(urllib.parse.urlparse(base_url).path)
                    if not current_path.endswith("/"):
                        current_path += "/"

                    # Join with the relative path
                    if current_path == "/":
                        absolute_url = (
                            f"{parsed_base.scheme}://{parsed_base.netloc}/{href}"
                        )
                    else:
                        absolute_url = f"{parsed_base.scheme}://{parsed_base.netloc}{current_path}{href}"
                    links.append(absolute_url)
                elif parsed_href.netloc == base_domain:
                    links.append(href)

    return links


def recursive_crawl(
    html_dir: str,
    start_url: str,
    max_pages: Optional[int] = None,
) -> Dict[str, str]:
    """Recursively crawl a website starting from a given URL.

    Args:
        start_url: The URL to start crawling from.
        max_pages: Maximum number of pages to crawl. None for unlimited.
        save_to_files: Whether to save HTML content to files.

    Returns:
        Dictionary mapping URLs to their HTML content.
    """
    if os.path.exists(html_dir):
        shutil.rmtree(html_dir)
    os.makedirs(html_dir, exist_ok=False)

    visited = set()
    to_visit = [start_url]
    page_content = {}
    base_domain = urllib.parse.urlparse(start_url).netloc

    page_count = 0

    while to_visit and (max_pages is None or page_count < max_pages):
        current_url = to_visit.pop(0)

        # Skip if already visited
        if current_url in visited:
            continue

        print(f"Crawling: {current_url}")

        # Fetch and parse the page
        html_content = fetch_url(current_url)
        if not html_content:
            visited.add(current_url)
            continue

        # Store the content
        page_content[current_url] = html_content
        page_count += 1

        # Create a filename from the URL
        parsed_url = urllib.parse.urlparse(current_url)
        path = parsed_url.path
        if not path or path == "/":
            path = "/index"

        # Replace special characters
        filename = f"{parsed_url.netloc}{path}".replace("/", "_").replace(":", "_")
        if not filename.endswith(".html"):
            filename += ".html"

        with open(f"{html_dir}/{filename}", "w", encoding="utf-8") as f:
            f.write(html_content)

        # Parse the HTML
        soup = parse_html(html_content)

        # Extract links
        links = extract_links(soup, current_url)

        # Mark as visited
        visited.add(current_url)

        # Add new links to visit
        for link in links:
            if link not in visited and link not in to_visit:
                # Ensure it's from the same domain
                link_domain = urllib.parse.urlparse(link).netloc
                if link_domain == base_domain:
                    to_visit.append(link)

    print(f"Crawling complete. Visited {len(visited)} pages.")
    return page_content
