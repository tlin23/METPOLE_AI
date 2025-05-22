import unittest
from unittest.mock import patch
from pathlib import Path
import tempfile
import shutil
import sys
from backend_refactor.pipeline.pipeline_cli import parse_args, main


class TestPipelineCLI(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for testing
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = Path(self.test_dir) / "output"
        self.db_path = Path(self.test_dir) / "db"
        self.collection = "test_collection"
        self.input_dir = Path(self.test_dir) / "input"
        self.input_dir.mkdir(exist_ok=True)

    def tearDown(self):
        # Clean up temporary directories
        shutil.rmtree(self.test_dir)

    def test_parse_args_web_mode(self):
        args = [
            "--mode",
            "web",
            "--input",
            "https://example.com",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
            "--allowed-domains",
            "example.com",
            "test.com",
        ]
        parsed = parse_args(args)
        self.assertEqual(parsed.mode, "web")
        self.assertEqual(parsed.input, "https://example.com")
        self.assertEqual(parsed.output, str(self.output_dir))
        self.assertEqual(parsed.db_path, str(self.db_path))
        self.assertEqual(parsed.collection, self.collection)
        self.assertEqual(parsed.allowed_domains, ["example.com", "test.com"])
        self.assertFalse(parsed.production)

    def test_parse_args_local_mode(self):
        args = [
            "--mode",
            "local",
            "--input",
            str(self.test_dir),
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
            "--allowed-extensions",
            ".pdf",
            ".docx",
        ]
        parsed = parse_args(args)
        self.assertEqual(parsed.mode, "local")
        self.assertEqual(parsed.input, str(self.test_dir))
        self.assertEqual(parsed.allowed_extensions, [".pdf", ".docx"])

    def test_parse_args_all_mode(self):
        args = [
            "--mode",
            "all",
            "--input",
            "https://example.com",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        parsed = parse_args(args)
        self.assertEqual(parsed.mode, "all")

    def test_parse_args_production_mode(self):
        args = [
            "--mode",
            "web",
            "--input",
            "https://example.com",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
            "--production",
        ]
        parsed = parse_args(args)
        self.assertTrue(parsed.production)

    @patch("backend_refactor.pipeline.pipeline_cli.run_web_pipeline")
    def test_main_web_mode(self, mock_run_web):
        mock_run_web.return_value = {"parsed_json": "test.json"}
        args = [
            "--mode",
            "web",
            "--input",
            "https://example.com",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 0)
            mock_run_web.assert_called_once()

    @patch("backend_refactor.pipeline.pipeline_cli.run_local_pipeline")
    def test_main_local_mode(self, mock_run_local):
        mock_run_local.return_value = {"parsed_json": "test.json"}
        args = [
            "--mode",
            "local",
            "--input",
            str(self.test_dir),
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 0)
            mock_run_local.assert_called_once()

    def test_main_missing_input_web(self):
        args = [
            "--mode",
            "web",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 1)

    def test_main_missing_input_local(self):
        args = [
            "--mode",
            "local",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 1)

    def test_main_nonexistent_input_dir(self):
        args = [
            "--mode",
            "local",
            "--input",
            "/nonexistent/path",
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 1)

    @patch("backend_refactor.pipeline.pipeline_cli.run_web_pipeline")
    @patch("backend_refactor.pipeline.pipeline_cli.run_local_pipeline")
    def test_main_all_mode(self, mock_run_local, mock_run_web):
        mock_run_web.return_value = {"parsed_json": "web.json"}
        mock_run_local.return_value = {"parsed_json": "local.json"}

        args = [
            "--mode",
            "all",
            "--input",
            str(self.input_dir),
            "--output",
            str(self.output_dir),
            "--db-path",
            str(self.db_path),
            "--collection",
            self.collection,
        ]
        with patch.object(sys, "argv", ["pipeline_cli.py"] + args):
            result = main()
            self.assertEqual(result, 0)
            mock_run_web.assert_called_once()
            mock_run_local.assert_called_once()


if __name__ == "__main__":
    unittest.main()
