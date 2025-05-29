import json
import pytest
from unittest.mock import patch, MagicMock


from backend_legacy.embedder.embed_corpus import (
    load_corpus,
    embed_corpus,
)


@pytest.fixture
def sample_corpus():
    return [
        {
            "chunk_id": "chunk_1",
            "document_id": "doc_1",
            "document_title": "Title 1",
            "document_name": "doc_name_1",
            "section": "Header 1",
            "content": "Sample content",
            "tags": ["tag1", "tag2"],
        },
        {
            "chunk_id": "chunk_2",
            "document_id": "doc_2",
            "document_title": "Title 2",
            "document_name": "doc_name_2",
            "section": "Header 2",
            "content": "More sample content",
            "tags": ["tag3"],
        },
    ]


def test_load_corpus(tmp_path, sample_corpus):
    corpus_path = tmp_path / "corpus.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(sample_corpus, f)
    loaded = load_corpus(str(corpus_path))
    assert len(loaded) == 2
    assert loaded[0]["chunk_id"] == "chunk_1"


@patch("backend_legacy.embedder.embed_corpus.chromadb.PersistentClient")
@patch(
    "backend_legacy.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction"
)
def test_embed_corpus(mock_embed_fn_class, mock_chroma_class, tmp_path, sample_corpus):
    # Create a separate directory for the corpus file to prevent it from being deleted
    # when clean_index=True removes the chroma_path directory
    corpus_dir = tmp_path / "corpus_dir"
    corpus_dir.mkdir()
    corpus_path = corpus_dir / "corpus.json"
    with open(corpus_path, "w", encoding="utf-8") as f:
        json.dump(sample_corpus, f)

    # Create a separate directory for the Chroma DB
    chroma_dir = tmp_path / "chroma_dir"
    chroma_dir.mkdir()

    mock_embed_fn = MagicMock()
    mock_embed_fn.embed_documents.return_value = [[0.1, 0.2, 0.3]]
    mock_embed_fn_class.return_value = mock_embed_fn

    mock_collection = MagicMock()
    mock_collection.count.return_value = 0
    mock_collection.add = MagicMock()
    mock_client = MagicMock()
    mock_client.list_collections.return_value = []
    mock_client.create_collection.return_value = mock_collection
    mock_chroma_class.return_value = mock_client

    embed_corpus(
        corpus_path=str(corpus_path),
        chroma_db_path=str(chroma_dir),
        collection_name="test_collection",
        batch_size=1,
    )

    mock_collection.add.assert_called()
