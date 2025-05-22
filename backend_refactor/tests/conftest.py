# backend_refactor/tests/conftest.py

import pytest
from unittest.mock import Mock, MagicMock
from backend_refactor.models.content_chunk import ContentChunk


@pytest.fixture
def wrap_parser_class():
    """Utility to wrap a mock parser in an instantiable class with a parse() method."""

    def wrap(parser_mock):
        class ParserWrapper:
            def __init__(self):
                self.parse = parser_mock.side_effect

        return ParserWrapper

    return wrap


@pytest.fixture
def wrapped_parser_classes(wrap_parser_class):
    """Returns a PARSER_MAP-like dictionary with real mocked parser classes."""

    def make_parser(ext):
        parse_mock = Mock()

        def parse_side_effect(file_path):
            return [
                ContentChunk(
                    chunk_id=f"{ext}_chunk1",
                    file_name=file_path.stem,
                    file_ext=ext,
                    page_number=1,
                    text_content=f"Sample {ext} content",
                    document_title=f"{ext.upper()} Doc",
                )
            ]

        parse_mock.side_effect = parse_side_effect
        return wrap_parser_class(parse_mock)

    return {
        ".html": make_parser("html"),
        ".pdf": make_parser("pdf"),
        ".docx": make_parser("docx"),
    }


@pytest.fixture
def sample_chunks():
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
def mock_chroma_client():
    collection = Mock()
    collection.add = Mock()
    client = Mock()
    client.get_or_create_collection = Mock(return_value=collection)
    return client


@pytest.fixture
def mock_openai_client():
    client = Mock()
    client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(content="This is a test response from the AI model.")
            )
        ]
    )
    return client
