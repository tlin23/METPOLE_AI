import pytest
from unittest.mock import patch, Mock
from bs4 import BeautifulSoup
from requests import RequestException
from backend_refactor.extractors.web_extractor import WebExtractor


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test output."""
    return tmp_path


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = Mock()
    mock.text = """
    <html>
        <body>
            <a href="https://example.com/page1">Link 1</a>
            <a href="https://example.com/page2">Link 2</a>
            <a href="https://other.com/page3">Link 3</a>
        </body>
    </html>
    """
    mock.raise_for_status = Mock()
    return mock


def test_web_extractor_initialization():
    """Test WebExtractor initialization with and without allowed domains."""
    # Test without allowed domains
    extractor = WebExtractor()
    assert extractor.allowed_domains is None
    assert extractor.visited_urls == set()

    # Test with allowed domains
    domains = ["example.com", "test.com"]
    extractor = WebExtractor(allowed_domains=domains)
    assert extractor.allowed_domains == domains


def test_is_allowed_domain():
    """Test domain filtering functionality."""
    extractor = WebExtractor(allowed_domains=["example.com"])

    assert extractor._is_allowed_domain("https://example.com/page1")
    assert extractor._is_allowed_domain("https://sub.example.com/page2")
    assert not extractor._is_allowed_domain("https://other.com/page3")

    # Test with no allowed domains
    extractor = WebExtractor()
    assert extractor._is_allowed_domain("https://any.com/page")


def test_get_links():
    """Test link extraction from HTML content."""
    extractor = WebExtractor(allowed_domains=["example.com"])
    html = """
    <html>
        <body>
            <a href="https://example.com/page1">Link 1</a>
            <a href="/page2">Link 2</a>
            <a href="https://other.com/page3">Link 3</a>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "html.parser")
    base_url = "https://example.com"

    links = extractor._get_links(base_url, soup)
    assert len(links) == 2
    assert "https://example.com/page1" in links
    assert "https://example.com/page2" in links
    assert "https://other.com/page3" not in links


def test_save_html(temp_dir):
    """Test HTML file saving functionality."""
    extractor = WebExtractor()
    url = "https://example.com/test/page"
    content = "<html><body>Test content</body></html>"

    output_path = extractor._save_html(url, content, temp_dir)

    assert output_path.exists()
    assert output_path.name == "test_page.html"
    assert output_path.read_text() == content


@patch("requests.get")
def test_extract_single_page(mock_get, temp_dir, mock_response):
    """Test extraction of a single page with no links."""
    mock_get.return_value = mock_response

    extractor = WebExtractor(allowed_domains=["example.com"])
    input_path = "https://example.com/"
    output_dir = temp_dir / "output"

    # Clear links in mock_response so it won't crawl further
    mock_response.text = "<html><body>No links</body></html>"

    saved_files = extractor.extract(input_path, output_dir)

    assert len(saved_files) == 1
    assert saved_files[0].exists()
    assert len(extractor.visited_urls) == 1


@patch("requests.get")
def test_extract_with_invalid_url(mock_get, temp_dir):
    """Test extraction with an invalid URL."""
    extractor = WebExtractor()
    input_path = "not-a-url"

    with pytest.raises(ValueError):
        extractor.extract(input_path, temp_dir)


@patch("requests.get")
def test_extract_with_network_error(mock_get, temp_dir):
    """Test extraction handling of network errors."""
    mock_get.side_effect = RequestException("Network error")

    extractor = WebExtractor()
    input_path = "https://example.com"

    saved_files = extractor.extract(input_path, temp_dir)
    assert len(saved_files) == 0
    assert len(extractor.visited_urls) == 0
