from pathlib import Path
from typing import List, Optional, Dict
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from .base_crawler import BaseCrawler
from ...logger.logging_config import get_logger

logger = get_logger("crawlers.web")


class WebCrawler(BaseCrawler):
    def __init__(
        self, allowed_domains: List[str] = None, max_pages: Optional[int] = None
    ):
        """
        Initialize the WebCrawler.

        Args:
            allowed_domains: List of domains that are allowed to be crawled.
                           If None, only the domain of the initial URL will be allowed.
            max_pages: Maximum number of pages to crawl. None for unlimited.
        """
        super().__init__(allowed_domains)
        self.max_pages = max_pages
        self.page_count = 0
        self.page_content: Dict[str, str] = {}

    def _is_allowed_domain(self, url: str) -> bool:
        """Check if the URL's domain is in the allowed domains list."""
        domain = urlparse(url).netloc
        return self._is_allowed(domain)

    def _get_links(self, url: str, soup: BeautifulSoup) -> List[str]:
        """Extract all links from the page that are within allowed domains."""
        links = []
        base_domain = urlparse(url).netloc

        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]

            # Skip empty links and fragments
            if not href or href.startswith("#"):
                continue

            # Handle relative URLs
            if href.startswith("/"):
                full_url = f"{urlparse(url).scheme}://{base_domain}{href}"
            else:
                full_url = urljoin(url, href)

            # Validate URL
            try:
                parsed = urlparse(full_url)
                if not parsed.scheme or not parsed.netloc:
                    continue

                if self._is_allowed_domain(full_url):
                    links.append(full_url)
            except Exception as e:
                logger.warning(f"Invalid URL {href}: {str(e)}")
                continue

        return links

    def _save_html(self, url: str, content: str, output_dir: Path) -> Path:
        """Save HTML content to a file in the html subdirectory and return the path."""
        # Create a filename from the URL
        parsed_url = urlparse(url)
        path = parsed_url.path

        # Handle root path
        if not path or path == "/":
            path = "/index"

        # Create filename
        filename = f"{parsed_url.netloc}{path}".replace("/", "_").replace(":", "_")
        if not filename.endswith(".html"):
            filename += ".html"

        # Save the file in the html subdirectory
        output_path = self._organize_by_type(Path(filename), output_dir, "html")
        output_path.write_text(content, encoding="utf-8")
        logger.debug(f"Saved HTML content to {output_path}")
        return output_path

    def extract(self, input_path: str, output_dir: Path) -> List[Path]:
        """
        Recursively crawl the input URL and save HTML files to the output directory.

        Args:
            input_path: Path object containing the URL to crawl
            output_dir: Directory where HTML files should be saved

        Returns:
            List of Path objects pointing to the saved HTML files
        """
        url = input_path
        if not url.startswith(("http://", "https://")):
            error_msg = "Input path must be a valid HTTP(S) URL"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Initialize allowed domains if not set
        if not self.allowed_patterns:
            self.allowed_patterns = [urlparse(url).netloc]
            logger.info(f"Set allowed domain to: {self.allowed_patterns[0]}")

        # Reset state
        self.processed_items.clear()
        self.page_count = 0
        self.page_content.clear()

        # Clean output directory
        self._clean_output_dir(output_dir)

        saved_files = []
        urls_to_visit = [url]
        logger.info(f"Starting web crawl from {url}")

        while urls_to_visit and (
            self.max_pages is None or self.page_count < self.max_pages
        ):
            current_url = urls_to_visit.pop(0)

            if current_url in self.processed_items:
                logger.debug(f"Skipping already processed URL: {current_url}")
                continue

            logger.info(f"Crawling: {current_url}")

            try:
                response = requests.get(current_url, timeout=10)
                response.raise_for_status()

                # Store content in memory
                self.page_content[current_url] = response.text

                # Save the HTML content
                output_path = self._save_html(current_url, response.text, output_dir)
                saved_files.append(output_path)

                # Parse the page and get new links
                soup = BeautifulSoup(response.text, "html.parser")
                new_links = self._get_links(current_url, soup)
                logger.debug(f"Found {len(new_links)} new links on {current_url}")

                # Add new links to the queue
                urls_to_visit.extend(
                    link for link in new_links if link not in self.processed_items
                )

                self.processed_items.add(current_url)
                self.page_count += 1

                if self.max_pages and self.page_count >= self.max_pages:
                    logger.info(f"Reached maximum page limit of {self.max_pages}")
                    break

            except (requests.RequestException, IOError) as e:
                logger.error(f"Error processing {current_url}: {str(e)}")
                continue

        logger.info(
            f"Crawling complete. Visited {self.page_count} pages, saved {len(saved_files)} files."
        )
        return saved_files
