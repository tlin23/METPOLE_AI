import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from backend_refactor.pipeline.pipeline_runner import (
    run_web_pipeline,
    run_local_pipeline,
    _process_files,
    _save_chunks_to_json,
)
from backend_refactor.models.content_chunk import ContentChunk


@pytest.fixture
def wrapped_parser_classes(mock_parsers):
    """Wrap parser mocks in callable classes for use in PARSER_MAP patching."""

    def wrap(parser_mock):
        class ParserWrapper:
            def __init__(self):
                self.parse = parser_mock.parse

        return ParserWrapper

    html_parser, pdf_parser, docx_parser = mock_parsers
    return {
        ".html": wrap(html_parser),
        ".pdf": wrap(pdf_parser),
        ".docx": wrap(docx_parser),
    }


@pytest.fixture
def sample_chunks():
    """Create sample ContentChunk objects for testing."""
    return [
        ContentChunk(
            chunk_id="chunk1",
            file_name="test1",
            file_ext="html",
            page_number=1,
            text_content="Test content 1",
            document_title="Test Doc 1",
        ),
        ContentChunk(
            chunk_id="chunk2",
            file_name="test2",
            file_ext="pdf",
            page_number=1,
            text_content="Test content 2",
            document_title="Test Doc 2",
        ),
    ]


@pytest.fixture
def mock_extractors():
    """Create mock extractors."""
    web_extractor = Mock()
    web_extractor.extract.return_value = [Path("test1.html"), Path("test2.html")]

    local_extractor = Mock()
    local_extractor.extract.return_value = [Path("test1.pdf"), Path("test2.docx")]

    return web_extractor, local_extractor


@pytest.fixture
def mock_parsers():
    """Create mock parsers."""
    html_parser = Mock()
    html_parser.parse.return_value = [
        ContentChunk(
            chunk_id="html1",
            file_name="test1",
            file_ext="html",
            page_number=1,
            text_content="HTML content",
            document_title="HTML Doc",
        )
    ]

    pdf_parser = Mock()
    pdf_parser.parse.return_value = [
        ContentChunk(
            chunk_id="pdf1",
            file_name="test1",
            file_ext="pdf",
            page_number=1,
            text_content="PDF content",
            document_title="PDF Doc",
        )
    ]

    docx_parser = Mock()
    docx_parser.parse.return_value = [
        ContentChunk(
            chunk_id="docx1",
            file_name="test2",
            file_ext="docx",
            page_number=1,
            text_content="DOCX content",
            document_title="DOCX Doc",
        )
    ]

    return html_parser, pdf_parser, docx_parser


def test_save_chunks_to_json(sample_chunks, tmp_path):
    """Test saving chunks to JSON file."""
    output_dir = tmp_path / "output"
    json_path = _save_chunks_to_json(sample_chunks, output_dir)

    assert json_path.exists()
    assert json_path.name == "parsed_chunks.json"

    # Verify JSON content
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["chunk_id"] == "chunk1"
        assert data[1]["chunk_id"] == "chunk2"


def test_process_files(wrapped_parser_classes, tmp_path):
    files = [Path("test1.html"), Path("test2.pdf"), Path("test3.docx")]

    with patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP",
        wrapped_parser_classes,
    ):
        chunks = _process_files(files, tmp_path)

        assert len(chunks) == 3
        assert any(c.file_ext == "html" for c in chunks)
        assert any(c.file_ext == "pdf" for c in chunks)
        assert any(c.file_ext == "docx" for c in chunks)


def test_run_web_pipeline(
    mock_extractors, mock_parsers, wrapped_parser_classes, tmp_path
):
    web_extractor, _ = mock_extractors
    html_parser, _, _ = mock_parsers

    with patch(
        "backend_refactor.pipeline.pipeline_runner.WebExtractor",
        return_value=web_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP",
        {".html": wrapped_parser_classes[".html"]},
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.embed_chunks"
    ) as mock_embed:

        result = run_web_pipeline(
            url="http://test.com",
            output_dir=tmp_path,
            db_path=str(tmp_path / "db"),
            collection_name="test_collection",
        )

        assert "html_files" in result
        assert "parsed_json" in result
        html_parser.parse.assert_called()
        mock_embed.assert_called_once()


def test_run_local_pipeline(
    mock_extractors, mock_parsers, wrapped_parser_classes, tmp_path
):
    _, local_extractor = mock_extractors
    _, pdf_parser, docx_parser = mock_parsers

    with patch(
        "backend_refactor.pipeline.pipeline_runner.LocalExtractor",
        return_value=local_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP",
        {
            ".pdf": wrapped_parser_classes[".pdf"],
            ".docx": wrapped_parser_classes[".docx"],
        },
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.embed_chunks"
    ) as mock_embed:

        run_local_pipeline(
            input_dir=tmp_path / "input",
            output_dir=tmp_path,
            db_path=str(tmp_path / "db"),
            collection_name="test_collection",
        )

        pdf_parser.parse.assert_called()
        docx_parser.parse.assert_called()
        mock_embed.assert_called_once()
