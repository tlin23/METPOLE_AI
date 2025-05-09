from unittest.mock import patch

from backend.crawler import crawl
import tempfile


@patch("backend.crawler.crawl.requests.get")
def test_fetch_url_success(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.text = "<html>Hello</html>"
    result = crawl.fetch_url("http://example.com")
    assert result == "<html>Hello</html>"


@patch("backend.crawler.crawl.requests.get", side_effect=Exception("Connection error"))
def test_fetch_url_failure(mock_get):
    result = crawl.fetch_url("http://example.com")
    assert result is None


def test_parse_html_returns_soup():
    html = "<html><body><p>Hello</p></body></html>"
    soup = crawl.parse_html(html)
    assert soup.find("p").text == "Hello"


def test_extract_text_removes_scripts():
    html = (
        "<html><head><script>alert(1);</script></head><body>Visible text</body></html>"
    )
    soup = crawl.parse_html(html)
    text = crawl.extract_text(soup)
    assert "alert" not in text
    assert "Visible text" in text


def test_extract_links_internal_and_relative():
    html = """
    <html><body>
    <a href="/about">About</a>
    <a href="http://example.com/contact">Contact</a>
    <a href="https://other.com">External</a>
    </body></html>
    """
    soup = crawl.parse_html(html)
    links = crawl.extract_links(soup, "http://example.com")
    assert "http://example.com/about" in links
    assert "http://example.com/contact" in links
    assert not any("other.com" in link for link in links)


@patch("backend.crawler.crawl.fetch_url", return_value="<html><body>Test</body></html>")
def test_recursive_crawl_single_page(mock_fetch):
    with tempfile.TemporaryDirectory() as temp_dir:
        output = crawl.recursive_crawl(temp_dir, "http://example.com", max_pages=1)
        assert "http://example.com" in output
        assert "Test" in output["http://example.com"]


@patch(
    "backend.crawler.crawl.fetch_url",
    return_value="<html><body><a href='/about'>More</a></body></html>",
)
def test_recursive_crawl_follows_internal_links(mock_fetch):
    with tempfile.TemporaryDirectory() as temp_dir:
        output = crawl.recursive_crawl(temp_dir, "http://example.com", max_pages=2)
        assert "http://example.com" in output
        assert any("about" in url for url in output)
