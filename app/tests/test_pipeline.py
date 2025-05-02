import pytest
from unittest.mock import patch

from app.run_pipeline import run_pipeline


@patch("app.run_pipeline.recursive_crawl")
@patch("app.run_pipeline.process_all_html_files")
@patch("app.run_pipeline.embed_corpus_data")
def test_run_pipeline_all_steps_called(mock_embed, mock_process, mock_crawl):
    # Mock crawl output
    mock_crawl.return_value = {"http://example.com": "<html>Test</html>"}

    # Mock processed output
    mock_process.return_value = [
        {
            "chunk_id": "chunk_1",
            "page_id": "page_1",
            "content": "Example content",
            "tags": ["tag1"],
        }
    ]

    # Run pipeline
    run_pipeline(start_url="http://example.com", max_pages=1)

    # Assert all steps were called
    mock_crawl.assert_called_once_with(
        "http://example.com", max_pages=1, save_to_files=True
    )
    mock_process.assert_called_once()
    mock_embed.assert_called_once()


@patch("app.run_pipeline.recursive_crawl")
@patch("app.run_pipeline.process_all_html_files")
@patch("app.run_pipeline.embed_corpus_data")
def test_run_pipeline_error_handling(mock_embed, mock_process, mock_crawl):
    # Simulate crawl error
    mock_crawl.side_effect = Exception("Crawl failed")

    with pytest.raises(Exception, match="Crawl failed"):
        run_pipeline(start_url="http://example.com", max_pages=1)

    # Ensure remaining steps were not executed
    mock_process.assert_not_called()
    mock_embed.assert_not_called()
