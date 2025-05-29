import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from requests import RequestException
from backend.data_processing.crawlers.web_crawler import WebCrawler


def test_web_crawler_initialization():
    """Test WebCrawler initialization with and without allowed domains."""
    # Test without allowed domains
    crawler = WebCrawler()
    assert crawler.allowed_patterns is None
    assert crawler.processed_items == set()
    assert crawler.max_pages is None
    assert crawler.page_count == 0
    assert crawler.page_content == {}

    # Test with allowed domains and max pages
    domains = ["example.com", "test.com"]
    crawler = WebCrawler(allowed_domains=domains, max_pages=10)
    assert crawler.allowed_patterns == domains
    assert crawler.max_pages == 10


def test_is_allowed_domain():
    """Test domain filtering functionality."""
    crawler = WebCrawler(allowed_domains=["example.com"])

    assert crawler._is_allowed_domain("https://example.com/page1")
    assert crawler._is_allowed_domain("https://sub.example.com/page2")
    assert not crawler._is_allowed_domain("https://other.com/page3")

    # Test with no allowed domains
    crawler = WebCrawler()
    assert crawler._is_allowed_domain("https://any.com/page")


def test_get_links():
    """Test link extraction from HTML content."""
    crawler = WebCrawler(allowed_domains=["example.com"])
    html = """
    <html>
        <body>
            <a href="https://example.com/page1">Link 1</a>
            <a href="/page2">Link 2</a>
            <a href="https://other.com/page3">Link 3</a>
            <a href="#">Fragment</a>
            <a href="">Empty</a>
            <a>No href</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://example.com"

    links = crawler._get_links(base_url, soup)
    assert len(links) == 2
    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    assert "https://other.com/page3" not in links


def test_save_html(temp_dir):
    """Test HTML file saving functionality."""
    crawler = WebCrawler()
    url = "https://example.com/test/page"
    content = "<html><body>Test content</body></html>"

    output_path = crawler._save_html(url, content, temp_dir)

    assert output_path.exists()
    assert output_path.name == "example.com_test_page.html"
    assert output_path.read_text() == content

    # Test root URL
    url = "https://example.com/"
    output_path = crawler._save_html(url, content, temp_dir)
    assert output_path.name == "example.com_index.html"


@patch("requests.get")
def test_extract_single_page(mock_get, temp_dir, mock_response):
    """Test extraction of a single page with no links."""
    mock_get.return_value = mock_response

    crawler = WebCrawler(allowed_domains=["example.com"])
    input_path = "https://example.com/"
    output_dir = temp_dir / "output"

    # Clear links in mock_response so it won't crawl further
    mock_response.text = "<html><body>No links</body></html>"

    saved_files = crawler.extract(input_path, output_dir)

    assert len(saved_files) == 1
    assert saved_files[0].exists()
    assert len(crawler.processed_items) == 1
    assert crawler.page_count == 1
    assert len(crawler.page_content) == 1


@patch("requests.get")
def test_extract_with_max_pages(mock_get, temp_dir, mock_response):
    """Test extraction with max pages limit."""
    mock_get.return_value = mock_response

    crawler = WebCrawler(allowed_domains=["example.com"], max_pages=2)
    input_path = "https://example.com/"
    output_dir = temp_dir / "output"

    saved_files = crawler.extract(input_path, output_dir)

    assert len(saved_files) == 2  # Initial page + one link
    assert crawler.page_count == 2
    assert len(crawler.page_content) == 2


@patch("requests.get")
def test_extract_with_invalid_url(mock_get, temp_dir):
    """Test extraction with an invalid URL."""
    crawler = WebCrawler()
    input_path = "not-a-url"

    with pytest.raises(ValueError):
        crawler.extract(input_path, temp_dir)


@patch("requests.get")
def test_extract_with_network_error(mock_get, temp_dir):
    """Test extraction handling of network errors."""
    mock_get.side_effect = RequestException("Network error")

    crawler = WebCrawler()
    input_path = "https://example.com"

    saved_files = crawler.extract(input_path, temp_dir)
    assert len(saved_files) == 0
    assert len(crawler.processed_items) == 0
    assert crawler.page_count == 0
    assert len(crawler.page_content) == 0


def test_extract_cleanup_output_dir(temp_dir):
    """Test that output directory is cleaned up before extraction."""
    output_dir = temp_dir / "output"
    output_dir.mkdir()
    (output_dir / "existing_file.txt").touch()

    crawler = WebCrawler()
    with patch("requests.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")
        crawler.extract("https://example.com", output_dir)

    # Directory should exist but be empty
    assert output_dir.exists()
    assert len(list(output_dir.iterdir())) == 0


@patch("requests.get")
def test_extract_multiple_pages(mock_get, temp_dir):
    """Test extraction of multiple pages with different content."""
    # Create mock responses for different pages
    mock_responses = {
        "https://example.com/": Mock(
            text="""
            <html>
                <body>
                    <a href="https://example.com/page1">Link 1</a>
                    <a href="https://example.com/page2">Link 2</a>
                </body>
            </html>
            """,
            raise_for_status=Mock(),
        ),
        "https://example.com/page1": Mock(
            text="<html><body>Page 1 Content</body></html>", raise_for_status=Mock()
        ),
        "https://example.com/page2": Mock(
            text="<html><body>Page 2 Content</body></html>", raise_for_status=Mock()
        ),
    }

    def mock_get_side_effect(url, *args, **kwargs):
        return mock_responses[url]

    mock_get.side_effect = mock_get_side_effect

    crawler = WebCrawler(allowed_domains=["example.com"])
    input_path = "https://example.com/"
    output_dir = temp_dir / "output"

    saved_files = crawler.extract(input_path, output_dir)

    # Verify number of files
    assert len(saved_files) == 3
    assert crawler.page_count == 3
    assert len(crawler.page_content) == 3

    # Verify file names and content
    file_names = {f.name for f in saved_files}
    assert "example.com_index.html" in file_names
    assert "example.com_page1.html" in file_names
    assert "example.com_page2.html" in file_names

    # Verify content was saved correctly
    for file_path in saved_files:
        content = file_path.read_text()
        if "index.html" in file_path.name:
            assert "Link 1" in content
            assert "Link 2" in content
        elif "page1.html" in file_path.name:
            assert "Page 1 Content" in content
        elif "page2.html" in file_path.name:
            assert "Page 2 Content" in content

    # Verify visited URLs
    assert len(crawler.processed_items) == 3
    assert "https://example.com/" in crawler.processed_items
    assert "https://example.com/page1" in crawler.processed_items
    assert "https://example.com/page2" in crawler.processed_items
