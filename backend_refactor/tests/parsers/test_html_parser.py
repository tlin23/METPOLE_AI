import pytest
from pathlib import Path
from backend_refactor.parsers.html_parser import HTMLParser


def test_html_parser_initialization():
    """Test that HTMLParser can be instantiated."""
    parser = HTMLParser()
    assert parser is not None


def test_html_parser_parse_not_implemented():
    """Test that parse method raises NotImplementedError."""
    parser = HTMLParser()
    with pytest.raises(NotImplementedError):
        parser.parse(Path("test.html"))
