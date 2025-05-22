import pytest
from pathlib import Path
from backend_refactor.parsers.base import BaseParser


def test_base_parser_is_abstract():
    """Test that BaseParser cannot be instantiated directly."""
    with pytest.raises(TypeError):
        BaseParser()


def test_base_parser_requires_parse_method():
    """Test that subclasses must implement parse method."""

    class DummyParser(BaseParser):
        pass

    with pytest.raises(TypeError):
        DummyParser()


def test_base_parser_abstract_method_signature():
    """Test that parse method has correct signature."""

    class DummyParser(BaseParser):
        def parse(self, file_path: Path) -> list:
            return []

    parser = DummyParser()
    result = parser.parse(Path("test.txt"))
    assert isinstance(result, list)
