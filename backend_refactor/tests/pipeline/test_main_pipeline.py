import pytest
from unittest.mock import patch
from backend_refactor.pipeline.main_pipeline import parse_args, main


def test_parse_args_web_mode():
    """Test argument parsing for web mode."""
    args = [
        "--mode",
        "web",
        "--input",
        "http://test.com",
        "--output",
        "/tmp/output",
        "--db-path",
        "/tmp/db",
        "--collection",
        "test_collection",
        "--allowed-domains",
        "test.com",
        "example.com",
    ]

    parsed = parse_args(args)
    assert parsed.mode == "web"
    assert parsed.input == "http://test.com"
    assert parsed.output == "/tmp/output"
    assert parsed.db_path == "/tmp/db"
    assert parsed.collection == "test_collection"
    assert parsed.allowed_domains == ["test.com", "example.com"]
    assert not parsed.production


def test_parse_args_local_mode():
    """Test argument parsing for local mode."""
    args = [
        "--mode",
        "local",
        "--input",
        "/tmp/input",
        "--output",
        "/tmp/output",
        "--db-path",
        "/tmp/db",
        "--collection",
        "test_collection",
        "--allowed-extensions",
        ".pdf",
        ".docx",
    ]

    parsed = parse_args(args)
    assert parsed.mode == "local"
    assert parsed.input == "/tmp/input"
    assert parsed.output == "/tmp/output"
    assert parsed.db_path == "/tmp/db"
    assert parsed.collection == "test_collection"
    assert parsed.allowed_extensions == [".pdf", ".docx"]
    assert not parsed.production


def test_parse_args_all_mode():
    """Test argument parsing for all mode."""
    args = [
        "--mode",
        "all",
        "--input",
        "/tmp/input",
        "--output",
        "/tmp/output",
        "--db-path",
        "/tmp/db",
        "--collection",
        "test_collection",
        "--production",
    ]

    parsed = parse_args(args)
    assert parsed.mode == "all"
    assert parsed.input == "/tmp/input"
    assert parsed.output == "/tmp/output"
    assert parsed.db_path == "/tmp/db"
    assert parsed.collection == "test_collection"
    assert parsed.production


def test_parse_args_missing_required():
    """Test argument parsing with missing required arguments."""
    with pytest.raises(SystemExit):
        parse_args(["--mode", "web"])  # Missing required args


def test_main_web_pipeline(tmp_path):
    """Test main function with web pipeline."""
    args = [
        "--mode",
        "web",
        "--input",
        "http://test.com",
        "--output",
        str(tmp_path),
        "--db-path",
        str(tmp_path / "db"),
        "--collection",
        "test_collection",
    ]

    with patch("backend_refactor.pipeline.main_pipeline.run_web_pipeline") as mock_web:
        mock_web.return_value = {
            "parsed_json": tmp_path / "web/parsed/parsed_chunks.json"
        }
        assert main(args) == 0
        mock_web.assert_called_once()


def test_main_local_pipeline(tmp_path):
    """Test main function with local pipeline."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    args = [
        "--mode",
        "local",
        "--input",
        str(input_dir),
        "--output",
        str(tmp_path),
        "--db-path",
        str(tmp_path / "db"),
        "--collection",
        "test_collection",
    ]

    with patch(
        "backend_refactor.pipeline.main_pipeline.run_local_pipeline"
    ) as mock_local:
        mock_local.return_value = {
            "parsed_json": tmp_path / "local/parsed/parsed_chunks.json"
        }
        assert main(args) == 0
        mock_local.assert_called_once()


def test_main_all_pipeline(tmp_path):
    """Test main function with all mode."""
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    args = [
        "--mode",
        "all",
        "--input",
        str(input_dir),
        "--output",
        str(tmp_path),
        "--db-path",
        str(tmp_path / "db"),
        "--collection",
        "test_collection",
    ]

    with patch(
        "backend_refactor.pipeline.main_pipeline.run_web_pipeline"
    ) as mock_web, patch(
        "backend_refactor.pipeline.main_pipeline.run_local_pipeline"
    ) as mock_local:
        mock_web.return_value = {
            "parsed_json": tmp_path / "web/parsed/parsed_chunks.json"
        }
        mock_local.return_value = {
            "parsed_json": tmp_path / "local/parsed/parsed_chunks.json"
        }
        assert main(args) == 0
        mock_web.assert_called_once()
        mock_local.assert_called_once()


def test_main_error_handling(tmp_path):
    """Test main function error handling."""
    args = [
        "--mode",
        "web",
        "--input",
        "http://test.com",
        "--output",
        str(tmp_path),
        "--db-path",
        str(tmp_path / "db"),
        "--collection",
        "test_collection",
    ]

    with patch(
        "backend_refactor.pipeline.main_pipeline.run_web_pipeline",
        side_effect=Exception("Test error"),
    ):
        assert main(args) == 1
