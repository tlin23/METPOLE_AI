"""
Tests for the crawler module.
"""

import pytest
from unittest.mock import patch, MagicMock
from bs4 import BeautifulSoup

from app.crawler.crawl import (
    fetch_url,
    parse_html,
    extract_text,
    extract_links,
    recursive_crawl,
    crawl,
)


@pytest.mark.unit
@pytest.mark.crawler
class TestCrawlFunctions:
    """Test individual functions in the crawl module."""

    @patch("app.crawler.crawl.requests.get")
    def test_fetch_url_success(self, mock_get):
        """Test successful URL fetching."""
        # Set up the mock
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_get.return_value = mock_response

        # Call the function
        result = fetch_url("https://example.com")

        # Check the result
        assert result == "<html><body>Test content</body></html>"
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    @patch("app.crawler.crawl.requests.get")
    def test_fetch_url_failure(self, mock_get):
        """Test URL fetching failure."""
        # Set up the mock to raise an exception
        mock_get.side_effect = Exception("Connection error")

        # Call the function
        result = fetch_url("https://example.com")

        # Check the result
        assert result is None
        mock_get.assert_called_once_with("https://example.com", timeout=10)

    def test_parse_html_valid(self):
        """Test parsing valid HTML."""
        html = "<html><body><h1>Test</h1></body></html>"
        result = parse_html(html)

        assert isinstance(result, BeautifulSoup)
        assert result.h1.text == "Test"

    def test_parse_html_none(self):
        """Test parsing None HTML."""
        result = parse_html(None)
        assert result is None

    def test_extract_text_valid(self):
        """Test extracting text from valid HTML."""
        soup = BeautifulSoup(
            "<html><body><h1>Title</h1><p>Paragraph</p><script>var x = 5;</script></body></html>",
            "html.parser",
        )
        result = extract_text(soup)

        assert "Title" in result
        assert "Paragraph" in result
        assert "var x = 5" not in result  # Script content should be removed

    def test_extract_text_none(self):
        """Test extracting text from None."""
        result = extract_text(None)
        assert result is None

    def test_extract_links_valid(self):
        """Test extracting links from valid HTML."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <a href="/">Home</a>
                <a href="/about">About</a>
                <a href="https://example.com/contact">Contact</a>
                <a href="https://external.com">External</a>
                <a href="#">Anchor</a>
            </body>
        </html>
        """,
            "html.parser",
        )

        base_url = "https://example.com/page"
        result = extract_links(soup, base_url)

        # Should extract internal links (same domain)
        assert "https://example.com/" in result
        assert "https://example.com/about" in result
        assert "https://example.com/contact" in result

        # Should not extract external links or anchors
        assert "https://external.com" not in result
        assert "#" not in result

    def test_extract_links_none(self):
        """Test extracting links from None."""
        result = extract_links(None, "https://example.com")
        assert result == []


@pytest.mark.unit
@pytest.mark.crawler
@pytest.mark.edge_case
class TestCrawlEdgeCases:
    """Test edge cases for the crawl module."""

    @patch("app.crawler.crawl.requests.get")
    def test_fetch_url_timeout(self, mock_get):
        """Test URL fetching with timeout."""
        # Set up the mock to raise a timeout exception
        mock_get.side_effect = TimeoutError("Request timed out")

        # Call the function
        result = fetch_url("https://example.com")

        # Check the result
        assert result is None

    def test_extract_links_malformed(self):
        """Test extracting links from malformed HTML."""
        soup = BeautifulSoup(
            """
        <html>
            <body>
                <a>No href</a>
                <a href="">Empty href</a>
                <a href="javascript:void(0)">JavaScript href</a>
                <a href="mailto:test@example.com">Email href</a>
            </body>
        </html>
        """,
            "html.parser",
        )

        base_url = "https://example.com/page"
        result = extract_links(soup, base_url)

        # Should not extract any of these links
        assert len(result) == 0

    def test_extract_text_empty(self):
        """Test extracting text from empty HTML."""
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        result = extract_text(soup)

        assert result == ""


@pytest.mark.integration
@pytest.mark.crawler
class TestRecursiveCrawl:
    """Test the recursive_crawl function."""

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    def test_recursive_crawl_basic(self, mock_extract_links, mock_fetch_url):
        """Test basic recursive crawling."""
        # Set up the mocks
        mock_fetch_url.side_effect = [
            "<html><body>Page 1</body></html>",
            "<html><body>Page 2</body></html>",
            "<html><body>Page 3</body></html>",
        ]
        mock_extract_links.side_effect = [
            ["https://example.com/page2", "https://example.com/page3"],
            [],
            [],
        ]

        # Call the function
        result = recursive_crawl("https://example.com/page1", max_pages=3)

        # Check the result
        assert len(result) == 3
        assert "https://example.com/page1" in result
        assert "https://example.com/page2" in result
        assert "https://example.com/page3" in result

        # Check that fetch_url was called for each URL
        assert mock_fetch_url.call_count == 3

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    def test_recursive_crawl_max_pages(self, mock_extract_links, mock_fetch_url):
        """Test recursive crawling with max_pages limit."""
        # Set up the mocks
        mock_fetch_url.side_effect = [
            "<html><body>Page 1</body></html>",
            "<html><body>Page 2</body></html>",
        ]
        mock_extract_links.side_effect = [
            ["https://example.com/page2", "https://example.com/page3"],
            ["https://example.com/page4"],
        ]

        # Call the function with max_pages=2
        result = recursive_crawl("https://example.com/page1", max_pages=2)

        # Check the result
        assert len(result) == 2
        assert "https://example.com/page1" in result
        assert "https://example.com/page2" in result
        assert "https://example.com/page3" not in result
        assert "https://example.com/page4" not in result

        # Check that fetch_url was called only twice
        assert mock_fetch_url.call_count == 2

    @patch("app.crawler.crawl.fetch_url")
    def test_recursive_crawl_fetch_failure(self, mock_fetch_url):
        """Test recursive crawling with fetch failures."""
        # Set up the mock to return None (fetch failure)
        mock_fetch_url.return_value = None

        # Call the function
        result = recursive_crawl("https://example.com/page1")

        # Check the result
        assert len(result) == 0

        # Check that fetch_url was called
        mock_fetch_url.assert_called_once_with("https://example.com/page1")


@pytest.mark.integration
@pytest.mark.crawler
class TestCrawl:
    """Test the crawl function."""

    @patch("app.crawler.crawl.fetch_url")
    def test_crawl_success(self, mock_fetch_url):
        """Test successful crawling."""
        # Set up the mock
        mock_fetch_url.return_value = "<html><head><title>Test Page</title></head><body><p>Test content</p></body></html>"

        # Call the function
        text, metadata = crawl("https://example.com")

        # Check the result
        assert "Test content" in text
        assert metadata["url"] == "https://example.com"
        assert metadata["title"] == "Test Page"
        assert "crawl_time" in metadata
        assert metadata["source"] == "web_crawl"

    @patch("app.crawler.crawl.fetch_url")
    def test_crawl_failure(self, mock_fetch_url):
        """Test crawling failure."""
        # Set up the mock to return None (fetch failure)
        mock_fetch_url.return_value = None

        # Call the function
        text, metadata = crawl("https://example.com")

        # Check the result
        assert text is None
        assert metadata["url"] == "https://example.com"
        assert metadata["title"] == "No title"
        assert "crawl_time" in metadata
        assert metadata["source"] == "web_crawl"


@pytest.mark.integration
@pytest.mark.crawler
@pytest.mark.edge_case
class TestCrawlIntegrationEdgeCases:
    """Test edge cases for the crawl integration."""

    @patch("app.crawler.crawl.fetch_url")
    def test_crawl_empty_page(self, mock_fetch_url):
        """Test crawling an empty page."""
        # Set up the mock to return an empty page
        mock_fetch_url.return_value = "<html><head></head><body></body></html>"

        # Call the function
        text, metadata = crawl("https://example.com")

        # Check the result
        assert text == ""
        assert metadata["title"] == "No title"

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    def test_recursive_crawl_circular_references(
        self, mock_extract_links, mock_fetch_url
    ):
        """Test recursive crawling with circular references."""
        # Set up the mocks
        mock_fetch_url.side_effect = [
            "<html><body>Page 1</body></html>",
            "<html><body>Page 2</body></html>",
        ]
        # Create circular references
        mock_extract_links.side_effect = [
            ["https://example.com/page2"],
            ["https://example.com/page1"],
        ]

        # Call the function
        result = recursive_crawl("https://example.com/page1", max_pages=5)

        # Check the result - should only have 2 pages despite circular references
        assert len(result) == 2
        assert "https://example.com/page1" in result
        assert "https://example.com/page2" in result

        # Check that fetch_url was called only twice
        assert mock_fetch_url.call_count == 2
