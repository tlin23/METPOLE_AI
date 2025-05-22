import pytest
from pathlib import Path
from backend_refactor.parsers.pdf_parser import PDFParser


def test_pdf_parser_initialization():
    """Test that PDFParser can be instantiated."""
    parser = PDFParser()
    assert parser is not None


def test_pdf_parser_parse_not_implemented():
    """Test that parse method raises NotImplementedError."""
    parser = PDFParser()
    with pytest.raises(NotImplementedError):
        parser.parse(Path("test.pdf"))
