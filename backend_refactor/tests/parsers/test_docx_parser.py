import pytest
from backend_refactor.parsers.docx_parser import DOCXParser


def test_docx_parser_initialization():
    """Test that DOCXParser can be instantiated."""
    parser = DOCXParser()
    assert parser is not None


def test_docx_parser_parse_not_implemented(test_docx_file):
    """Test that parse method raises NotImplementedError."""
    parser = DOCXParser()
    with pytest.raises(NotImplementedError):
        parser.parse(test_docx_file)
