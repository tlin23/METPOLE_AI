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


@pytest.fixture
def mock_extractors():
    web_extractor = Mock()
    web_extractor.extract.return_value = [Path("test1.html"), Path("test2.html")]

    local_extractor = Mock()
    local_extractor.extract.return_value = [Path("test1.pdf"), Path("test2.docx")]

    return web_extractor, local_extractor


def test_save_chunks_to_json(sample_chunks, tmp_path):
    output_dir = tmp_path / "output"
    json_path = _save_chunks_to_json(sample_chunks, output_dir)

    assert json_path.exists()
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert len(data) == 2
        assert data[0]["chunk_id"] == "chunk1"
        assert data[1]["chunk_id"] == "chunk2"


def test_process_files(wrapped_parser_classes, tmp_path):
    files = [Path("test1.html"), Path("test2.pdf"), Path("test3.docx")]
    with patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP", wrapped_parser_classes
    ):
        chunks = _process_files(files, tmp_path)
        assert len(chunks) == 3
        assert any(c.file_ext == "html" for c in chunks)
        assert any(c.file_ext == "pdf" for c in chunks)
        assert any(c.file_ext == "docx" for c in chunks)


def test_run_web_pipeline(mock_extractors, wrapped_parser_classes, tmp_path):
    web_extractor, _ = mock_extractors
    with patch(
        "backend_refactor.pipeline.pipeline_runner.WebExtractor",
        return_value=web_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP",
        {
            ".html": wrapped_parser_classes[".html"],
        },
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
        mock_embed.assert_called_once()


def test_run_local_pipeline(mock_extractors, wrapped_parser_classes, tmp_path):
    _, local_extractor = mock_extractors
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
        input_dir = tmp_path / "input"
        input_dir.mkdir(exist_ok=True)
        (input_dir / "test1.pdf").touch()
        (input_dir / "test2.docx").touch()

        run_local_pipeline(
            input_dir=input_dir,
            output_dir=tmp_path,
            db_path=str(tmp_path / "db"),
            collection_name="test_collection",
        )
        mock_embed.assert_called_once()
