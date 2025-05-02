import json
from unittest.mock import patch, MagicMock

from app.crawler import extract_content


@patch("app.crawler.extract_content.partition_html")
@patch("app.crawler.extract_content.RecursiveCharacterTextSplitter")
@patch("app.crawler.extract_content.extract_tags_with_keybert")
def test_process_all_html_files(
    mock_extract_tags, mock_splitter_class, mock_partition, tmp_path
):
    # Create temp HTML input
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    html_file = html_dir / "test_file.html"
    html_file.write_text(
        "<html><body><p>This is a long enough paragraph to be tagged properly.</p></body></html>"
    )

    # Mock tag extraction directly
    mock_extract_tags.return_value = ["tag1", "tag2"]

    # Mock partition_html
    mock_element = MagicMock()
    mock_element.text = "This is a long enough paragraph to be tagged properly."
    mock_partition.return_value = [mock_element]

    # Mock text splitter
    mock_splitter = MagicMock()
    mock_splitter.split_text.return_value = [mock_element.text]
    mock_splitter_class.return_value = mock_splitter

    # Run extraction
    output_path = tmp_path / "corpus.json"
    result = extract_content.process_all_html_files(str(html_dir), str(output_path))

    # Assertions
    assert isinstance(result, list)
    assert len(result) == 1
    assert result[0]["chunk_id"].startswith("chunk_")
    assert result[0]["content"].startswith("This is a long enough paragraph")
    assert result[0]["tags"] == ["tag1", "tag2"]

    # Verify JSON output is written
    with output_path.open("r", encoding="utf-8") as f:
        saved = json.load(f)
        assert len(saved) == 1
        assert saved[0]["tags"] == ["tag1", "tag2"]
