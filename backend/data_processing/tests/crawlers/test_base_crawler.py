import pytest
from pathlib import Path
from backend.data_processing.crawlers.base_crawler import BaseCrawler


def test_base_crawler_is_abstract():
    """Test that BaseCrawler cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseCrawler()


def test_base_crawler_requires_extract_method():
    """Test that subclasses must implement extract method."""

    class DummyCrawler(BaseCrawler):
        pass

    with pytest.raises(TypeError):
        DummyCrawler()


def test_base_crawler_abstract_method_signature():
    """Test that extract method has correct signature."""

    class DummyCrawler(BaseCrawler):
        def extract(self, input_path: Path, output_dir: Path):
            return []

    crawler = DummyCrawler()
    result = crawler.extract(Path("test"), Path("output"))
    assert isinstance(result, list)
