import pytest
from unittest.mock import patch, MagicMock

from backend.api.models import ChunkResult
from backend.retriever.ask import Retriever


@pytest.fixture
def tmp_retriever(tmp_path):
    """Returns a Retriever instance using a temp writable Chroma DB path."""
    chroma_path = tmp_path / "index"
    chroma_path.mkdir(parents=True, exist_ok=True)
    return Retriever(chroma_path=str(chroma_path))


@pytest.fixture
def sample_chunks():
    return [
        ChunkResult(
            text="This is a test chunk",
            metadata={
                "chunk_id": "chunk_123",
                "page_title": "Test Page",
                "section_header": "Intro",
            },
            distance=0.1,
        ),
        ChunkResult(
            text="Another chunk of content",
            metadata={
                "chunk_id": "chunk_456",
                "page_title": "Another Page",
                "section_header": "FAQ",
            },
            distance=0.2,
        ),
    ]


@patch("backend.retriever.ask.chromadb.PersistentClient")
@patch("backend.retriever.ask.OpenAI")
def test_query_returns_results(mock_openai, mock_chroma, tmp_path):
    chroma_path = tmp_path / "index"
    chroma_path.mkdir(parents=True, exist_ok=True)

    mock_collection = MagicMock()
    mock_collection.count.return_value = 2
    mock_collection.query.return_value = {
        "documents": [["doc1", "doc2"]],
        "metadatas": [[{"chunk_id": "chunk_1"}, {"chunk_id": "chunk_2"}]],
        "distances": [[0.1, 0.2]],
    }
    mock_chroma.return_value.get_or_create_collection.return_value = mock_collection

    retriever = Retriever(chroma_path=str(chroma_path))
    results = retriever.query("What is Metropole?")
    assert "documents" in results
    assert len(results["documents"][0]) == 2


def test_generate_answer_with_flags(sample_chunks, tmp_retriever):
    with patch.object(
        tmp_retriever, "_construct_prompt", return_value="mock prompt"
    ), patch.object(
        tmp_retriever, "_prepare_source_info", return_value="Chunk sources"
    ), patch(
        "backend.retriever.ask.client.chat.completions.create"
    ) as mock_create:

        mock_create.return_value.choices = [
            MagicMock(
                message=MagicMock(
                    content="You can try these DIY tips to fix the issue."
                )
            )
        ]

        result = tmp_retriever.generate_answer("How do I fix a leak?", sample_chunks)

        assert result["contains_diy_advice"] is True
        assert "DIY" in result["answer"]
        assert "Chunk sources" in result["source_info"]


def test_prepare_source_info_formatting(sample_chunks, tmp_retriever):
    info = tmp_retriever._prepare_source_info(sample_chunks)
    assert "chunk_123" in info
    assert "Test Page" in info
    assert "chunk_456" in info


def test_construct_prompt_structure(sample_chunks, tmp_retriever):
    prompt = tmp_retriever._construct_prompt("What are the amenities?", sample_chunks)
    assert "Question:" in prompt
    assert "Building Content:" in prompt
    assert "Chunk 1" in prompt
    assert "Section: Intro" in prompt
    assert "Page: Test Page" in prompt
