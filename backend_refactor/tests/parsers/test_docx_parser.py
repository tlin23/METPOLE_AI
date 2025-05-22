import pytest
from pathlib import Path
from backend_refactor.parsers.docx_parser import DOCXParser


def test_docx_parser_initialization():
    """Test that DOCXParser can be instantiated."""
    parser = DOCXParser()
    assert parser is not None


def test_docx_parser_parse_not_implemented():
    """Test that parse method raises NotImplementedError."""
    parser = DOCXParser()
    with pytest.raises(NotImplementedError):
        parser.parse(Path("test.docx"))
