# backend_refactor/tests/test_pipeline_e2e.py

import json
import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from backend_refactor.pipeline.pipeline_runner import (
    run_web_pipeline,
    run_local_pipeline,
)


@pytest.fixture
def mock_extractors():
    web_extractor = Mock()
    web_extractor.extract.return_value = [Path("test1.html"), Path("test2.html")]

    local_extractor = Mock()
    local_extractor.extract.return_value = [Path("test1.pdf"), Path("test2.docx")]

    return web_extractor, local_extractor


def test_e2e_web_pipeline(
    tmp_path,
    mock_extractors,
    wrapped_parser_classes,
    mock_chroma_client,
    mock_openai_client,
):
    web_extractor, _ = mock_extractors
    output_dir = tmp_path / "output"
    db_path = tmp_path / "db"

    with patch(
        "backend_refactor.pipeline.pipeline_runner.WebExtractor",
        return_value=web_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP", wrapped_parser_classes
    ), patch(
        "chromadb.PersistentClient", return_value=mock_chroma_client
    ), patch(
        "openai.OpenAI", return_value=mock_openai_client
    ):

        result = run_web_pipeline(
            url="http://test.com",
            output_dir=output_dir,
            db_path=str(db_path),
            collection_name="test_collection",
        )

        assert (output_dir / "html").exists()
        assert (output_dir / "parsed").exists()

        json_path = result["parsed_json"]
        assert json_path.exists()
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) > 0
            assert all(isinstance(chunk, dict) for chunk in data)

        mock_chroma_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )
        collection = mock_chroma_client.get_or_create_collection.return_value
        collection.add.assert_called_once()
        mock_openai_client.chat.completions.create.assert_not_called()


def test_e2e_local_pipeline(
    tmp_path,
    mock_extractors,
    wrapped_parser_classes,
    mock_chroma_client,
    mock_openai_client,
):
    _, local_extractor = mock_extractors
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    output_dir = tmp_path / "output"
    db_path = tmp_path / "db"

    (input_dir / "test1.pdf").touch()
    (input_dir / "test2.docx").touch()

    with patch(
        "backend_refactor.pipeline.pipeline_runner.LocalExtractor",
        return_value=local_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP", wrapped_parser_classes
    ), patch(
        "chromadb.PersistentClient", return_value=mock_chroma_client
    ), patch(
        "openai.OpenAI", return_value=mock_openai_client
    ):

        result = run_local_pipeline(
            input_dir=input_dir,
            output_dir=output_dir,
            db_path=str(db_path),
            collection_name="test_collection",
        )

        assert (output_dir / "extracted").exists()
        assert (output_dir / "parsed").exists()

        json_path = result["parsed_json"]
        assert json_path.exists()
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert len(data) > 0
            assert all(isinstance(chunk, dict) for chunk in data)

        mock_chroma_client.get_or_create_collection.assert_called_once_with(
            name="test_collection"
        )
        collection = mock_chroma_client.get_or_create_collection.return_value
        collection.add.assert_called_once()
        mock_openai_client.chat.completions.create.assert_not_called()


def test_e2e_error_handling(
    tmp_path,
    mock_extractors,
    wrapped_parser_classes,
    mock_chroma_client,
    mock_openai_client,
):
    web_extractor, _ = mock_extractors
    web_extractor.extract.side_effect = Exception("Test error")

    output_dir = tmp_path / "output"
    db_path = tmp_path / "db"

    with patch(
        "backend_refactor.pipeline.pipeline_runner.WebExtractor",
        return_value=web_extractor,
    ), patch(
        "backend_refactor.pipeline.pipeline_runner.PARSER_MAP", wrapped_parser_classes
    ), patch(
        "chromadb.PersistentClient", return_value=mock_chroma_client
    ):

        with pytest.raises(Exception, match="Test error"):
            run_web_pipeline(
                url="http://test.com",
                output_dir=output_dir,
                db_path=str(db_path),
                collection_name="test_collection",
            )

        assert not (output_dir / "html").exists()
        assert not (output_dir / "parsed").exists()
        mock_chroma_client.get_or_create_collection.assert_not_called()
