from unittest.mock import MagicMock

from backend.crawler import utils


def test_clean_text_removes_special_chars():
    raw = "Some\u200btext\nwith\u202apunctuations… and “quotes”."
    cleaned = utils.clean_text(raw)
    assert "\u200b" not in cleaned
    assert "\u202a" not in cleaned
    assert "\n" not in cleaned
    assert "..." in cleaned
    assert '"' in cleaned


def test_hash_id_consistency():
    text = "Same text"
    assert utils.hash_id(text) == utils.hash_id(text)


def test_extract_tags_with_short_text():
    mock_model = MagicMock()
    result = utils.extract_tags_with_keybert("Too short", mock_model)
    assert result == []


def test_extract_tags_with_keybert_calls_model():
    text = "This is a test sentence with enough content to extract meaningful tags."
    mock_model = MagicMock()
    mock_model.extract_keywords.return_value = [("tag1", 0.9), ("tag2", 0.8)]
    tags = utils.extract_tags_with_keybert(text, mock_model)
    mock_model.extract_keywords.assert_called_once()
    assert tags == ["tag1", "tag2"]
