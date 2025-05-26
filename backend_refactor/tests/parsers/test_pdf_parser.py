import pytest
from backend_refactor.parsers.pdf_parser import PDFParser


def test_pdf_parser_initialization():
    """Test that PDFParser can be instantiated."""
    parser = PDFParser()
    assert parser is not None


def test_pdf_parser_parse_not_implemented(test_pdf_file):
    """Test that parse method raises NotImplementedError."""
    parser = PDFParser()
    with pytest.raises(NotImplementedError):
        parser.parse(test_pdf_file)
