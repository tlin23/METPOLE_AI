"""
Integration tests for the full pipeline from crawling to retrieval.
"""

import os
import pytest
from unittest.mock import patch, MagicMock

from app.crawler.crawl import recursive_crawl
from app.crawler.extract_content import process_all_html_files
from app.crawler.add_metadata_and_tags import process_content_objects, save_to_json
from app.embedder.embed_corpus import embed_corpus
from app.retriever.ask import Retriever


@pytest.mark.integration
class TestFullPipeline:
    """Test the full pipeline from crawling to retrieval."""

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_full_pipeline(
        self,
        mock_openai,
        mock_retriever_client,
        mock_embedding_function,
        mock_embedder_client,
        mock_keybert,
        mock_extract_links,
        mock_fetch_url,
        temp_dir,
    ):
        """Test the full pipeline from crawling to retrieval."""
        # Set up the temp directories
        html_dir = os.path.join(temp_dir, "html")
        processed_dir = os.path.join(temp_dir, "processed")
        index_dir = os.path.join(temp_dir, "index")

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Set up the mocks for crawling
        mock_fetch_url.side_effect = [
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Page 1</title>
            </head>
            <body>
                <main>
                    <h1>Main Heading</h1>
                    <section>
                        <h2>Section 1</h2>
                        <p>This is the first paragraph of section 1.</p>
                        <p>This is the second paragraph of section 1.</p>
                    </section>
                    <section>
                        <h2>Section 2</h2>
                        <p>This is the first paragraph of section 2.</p>
                        <ul>
                            <li>List item 1</li>
                            <li>List item 2</li>
                        </ul>
                    </section>
                </main>
            </body>
            </html>
            """,
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Page 2</title>
            </head>
            <body>
                <main>
                    <h1>Page 2 Heading</h1>
                    <section>
                        <h2>Section 1</h2>
                        <p>This is the content of page 2, section 1.</p>
                    </section>
                </main>
            </body>
            </html>
            """,
        ]

        mock_extract_links.side_effect = [["https://example.com/page2"], []]

        # Set up the mock for KeyBERT
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = [
            ("test", 0.9),
            ("content", 0.8),
            ("section", 0.7),
        ]
        mock_keybert.return_value = mock_keybert_instance

        # Set up the mocks for ChromaDB
        mock_embedder_client_instance = MagicMock()
        mock_embedder_collection = MagicMock()
        mock_embedder_client_instance.get_or_create_collection.return_value = (
            mock_embedder_collection
        )
        mock_embedder_client.return_value = mock_embedder_client_instance

        mock_retriever_client_instance = MagicMock()
        mock_retriever_collection = MagicMock()
        mock_retriever_client_instance.get_or_create_collection.return_value = (
            mock_retriever_collection
        )
        mock_retriever_client.return_value = mock_retriever_client_instance

        # Set up the mock for OpenAI
        mock_openai_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a sample response from the LLM."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_openai_client

        # Set up the retriever collection's query method to return sample results
        mock_retriever_collection.query.return_value = {
            "ids": [["chunk_test_001", "chunk_test_002"]],
            "documents": [
                [
                    "This is the first paragraph of section 1.",
                    "This is the first paragraph of section 2.",
                ]
            ],
            "metadatas": [
                [
                    {
                        "page_id": "page_test_001",
                        "page_title": "Test Page 1",
                        "section_header": "Section 1",
                        "tags": "test,content,section",
                    },
                    {
                        "page_id": "page_test_001",
                        "page_title": "Test Page 1",
                        "section_header": "Section 2",
                        "tags": "test,content,section",
                    },
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        # Step 1: Crawl the website
        with patch.dict(os.environ, {"PYTHONPATH": os.getcwd()}):
            content_dict = recursive_crawl(
                "https://example.com/page1", max_pages=2, save_to_files=True
            )

            # Check that the crawl was successful
            assert len(content_dict) == 2
            assert "https://example.com/page1" in content_dict
            assert "https://example.com/page2" in content_dict

            # Write the HTML files to the temp directory
            for i, (url, html) in enumerate(content_dict.items()):
                file_path = os.path.join(html_dir, f"test_page_{i+1}.html")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(html)

            # Step 2: Process the HTML files
            results = process_all_html_files(html_dir)

            # Check that the processing was successful
            assert len(results) == 2

            # Create content objects
            content_objects = []
            for file_path, content in results.items():
                page_title = content["title"]
                page_name = os.path.basename(file_path).replace(".html", "")

                for section in content["sections"]:
                    section_header = section["header"]

                    for chunk in section["chunks"]:
                        chunk_object = {
                            "page_title": page_title,
                            "page_name": page_name,
                            "section_header": section_header,
                            "content": chunk["content"],
                            "content_html": chunk["content_html"],
                        }
                        content_objects.append(chunk_object)

            # Step 3: Add metadata and tags
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects", content_objects
            ):
                processed_objects = process_content_objects()

                # Check that the metadata and tags were added
                assert len(processed_objects) == len(content_objects)
                for obj in processed_objects:
                    assert "chunk_id" in obj
                    assert "page_id" in obj
                    assert "tags" in obj

                # Save to JSON
                corpus_path = os.path.join(processed_dir, "test_corpus.json")
                save_to_json(processed_objects, corpus_path)

                # Check that the file was created
                assert os.path.exists(corpus_path)

            # Step 4: Embed the corpus
            embed_corpus(
                corpus_path=corpus_path,
                chroma_path=index_dir,
                collection_name="test_collection",
                batch_size=10,
            )

            # Check that the embeddings were created
            mock_embedder_collection.add.assert_called_once()

            # Step 5: Query the vector store
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                retriever = Retriever()

                # Query the vector store
                query_results = retriever.query("test query", n_results=2)

                # Check that the query was successful
                assert "ids" in query_results
                assert "documents" in query_results
                assert "metadatas" in query_results

                # Generate an answer
                chunks = []
                for i, doc_id in enumerate(query_results["ids"][0]):
                    chunk = MagicMock()
                    chunk.text = query_results["documents"][0][i]
                    chunk.metadata = query_results["metadatas"][0][i]
                    chunks.append(chunk)

                answer_result = retriever.generate_answer("What is the answer?", chunks)

                # Check that the answer was generated
                assert "answer" in answer_result
                assert (
                    answer_result["answer"] == "This is a sample response from the LLM."
                )


@pytest.mark.integration
@pytest.mark.edge_case
class TestFullPipelineEdgeCases:
    """Test edge cases for the full pipeline."""

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_pipeline_with_empty_content(
        self,
        mock_openai,
        mock_retriever_client,
        mock_embedding_function,
        mock_embedder_client,
        mock_keybert,
        mock_extract_links,
        mock_fetch_url,
        temp_dir,
    ):
        """Test the pipeline with empty content."""
        # Set up the temp directories
        html_dir = os.path.join(temp_dir, "html")
        processed_dir = os.path.join(temp_dir, "processed")
        index_dir = os.path.join(temp_dir, "index")

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Set up the mocks for crawling with empty content
        mock_fetch_url.side_effect = [
            """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Empty Page</title>
            </head>
            <body>
                <main>
                    <h1>Empty Heading</h1>
                    <section>
                        <h2>Empty Section</h2>
                        <!-- No content here -->
                    </section>
                </main>
            </body>
            </html>
            """
        ]

        mock_extract_links.return_value = []

        # Set up the mock for KeyBERT
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = (
            []
        )  # No keywords for empty content
        mock_keybert.return_value = mock_keybert_instance

        # Set up the mocks for ChromaDB
        mock_embedder_client_instance = MagicMock()
        mock_embedder_collection = MagicMock()
        mock_embedder_client_instance.get_or_create_collection.return_value = (
            mock_embedder_collection
        )
        mock_embedder_client.return_value = mock_embedder_client_instance

        mock_retriever_client_instance = MagicMock()
        mock_retriever_collection = MagicMock()
        mock_retriever_client_instance.get_or_create_collection.return_value = (
            mock_retriever_collection
        )
        mock_retriever_client.return_value = mock_retriever_client_instance

        # Set up the mock for OpenAI
        mock_openai_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "I don't have specific information about that."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_openai_client

        # Set up the retriever collection's query method to return empty results
        mock_retriever_collection.query.return_value = {
            "ids": [[]],
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
        }

        # Step 1: Crawl the website
        with patch.dict(os.environ, {"PYTHONPATH": os.getcwd()}):
            content_dict = recursive_crawl(
                "https://example.com/empty", max_pages=1, save_to_files=True
            )

            # Check that the crawl was successful
            assert len(content_dict) == 1

            # Write the HTML file to the temp directory
            file_path = os.path.join(html_dir, "empty_page.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_dict["https://example.com/empty"])

            # Step 2: Process the HTML files
            results = process_all_html_files(html_dir)

            # Check that the processing was successful
            assert len(results) == 1

            # Create content objects
            content_objects = []
            for file_path, content in results.items():
                page_title = content["title"]
                page_name = os.path.basename(file_path).replace(".html", "")

                for section in content["sections"]:
                    section_header = section["header"]

                    for chunk in section["chunks"]:
                        chunk_object = {
                            "page_title": page_title,
                            "page_name": page_name,
                            "section_header": section_header,
                            "content": chunk["content"],
                            "content_html": chunk["content_html"],
                        }
                        content_objects.append(chunk_object)

            # Step 3: Add metadata and tags
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects", content_objects
            ):
                processed_objects = process_content_objects()

                # Check that the metadata and tags were added
                assert len(processed_objects) == len(content_objects)

                # Save to JSON
                corpus_path = os.path.join(processed_dir, "empty_corpus.json")
                save_to_json(processed_objects, corpus_path)

            # Step 4: Embed the corpus
            embed_corpus(
                corpus_path=corpus_path,
                chroma_path=index_dir,
                collection_name="empty_collection",
                batch_size=10,
            )

            # Step 5: Query the vector store
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                retriever = Retriever()

                # Query the vector store
                query_results = retriever.query("test query", n_results=2)

                # Check that the query returned empty results
                assert query_results["ids"][0] == []

                # Generate an answer with empty chunks
                answer_result = retriever.generate_answer("What is the answer?", [])

                # Check that the answer was generated
                assert "answer" in answer_result
                assert answer_result["is_general_knowledge"] is True

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    @patch("app.retriever.ask.chromadb.PersistentClient")
    @patch("app.retriever.ask.openai.OpenAI")
    def test_pipeline_with_missing_tags(
        self,
        mock_openai,
        mock_retriever_client,
        mock_embedding_function,
        mock_embedder_client,
        mock_keybert,
        mock_extract_links,
        mock_fetch_url,
        temp_dir,
    ):
        """Test the pipeline with content missing tags."""
        # Set up the temp directories
        html_dir = os.path.join(temp_dir, "html")
        processed_dir = os.path.join(temp_dir, "processed")
        index_dir = os.path.join(temp_dir, "index")

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Set up the mocks for crawling
        mock_fetch_url.return_value = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <main>
                <h1>Main Heading</h1>
                <section>
                    <h2>Section 1</h2>
                    <p>This is a paragraph.</p>
                </section>
            </main>
        </body>
        </html>
        """

        mock_extract_links.return_value = []

        # Set up the mock for KeyBERT to return empty tags
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = []
        mock_keybert.return_value = mock_keybert_instance

        # Set up the mocks for ChromaDB
        mock_embedder_client_instance = MagicMock()
        mock_embedder_collection = MagicMock()
        mock_embedder_client_instance.get_or_create_collection.return_value = (
            mock_embedder_collection
        )
        mock_embedder_client.return_value = mock_embedder_client_instance

        mock_retriever_client_instance = MagicMock()
        mock_retriever_collection = MagicMock()
        mock_retriever_client_instance.get_or_create_collection.return_value = (
            mock_retriever_collection
        )
        mock_retriever_client.return_value = mock_retriever_client_instance

        # Set up the mock for OpenAI
        mock_openai_client = MagicMock()
        mock_completion = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is a sample response from the LLM."
        mock_choice.message = mock_message
        mock_completion.choices = [mock_choice]
        mock_openai_client.chat.completions.create.return_value = mock_completion
        mock_openai.return_value = mock_openai_client

        # Set up the retriever collection's query method to return results with missing tags
        mock_retriever_collection.query.return_value = {
            "ids": [["chunk_test_001"]],
            "documents": [["This is a paragraph."]],
            "metadatas": [
                [
                    {
                        "page_id": "page_test_001",
                        "page_title": "Test Page",
                        "section_header": "Section 1",
                        "tags": "",
                    }
                ]
            ],
            "distances": [[0.1]],
        }

        # Step 1: Crawl the website
        with patch.dict(os.environ, {"PYTHONPATH": os.getcwd()}):
            content_dict = recursive_crawl(
                "https://example.com/page", max_pages=1, save_to_files=True
            )

            # Write the HTML file to the temp directory
            file_path = os.path.join(html_dir, "test_page.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_dict["https://example.com/page"])

            # Step 2: Process the HTML files
            results = process_all_html_files(html_dir)

            # Create content objects
            content_objects = []
            for file_path, content in results.items():
                page_title = content["title"]
                page_name = os.path.basename(file_path).replace(".html", "")

                for section in content["sections"]:
                    section_header = section["header"]

                    for chunk in section["chunks"]:
                        chunk_object = {
                            "page_title": page_title,
                            "page_name": page_name,
                            "section_header": section_header,
                            "content": chunk["content"],
                            "content_html": chunk["content_html"],
                        }
                        content_objects.append(chunk_object)

            # Step 3: Add metadata and tags
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects", content_objects
            ):
                processed_objects = process_content_objects()

                # Check that the metadata was added but tags are empty
                assert len(processed_objects) == len(content_objects)
                for obj in processed_objects:
                    assert "chunk_id" in obj
                    assert "page_id" in obj
                    assert "tags" in obj
                    assert obj["tags"] == []  # Tags should be empty

                # Save to JSON
                corpus_path = os.path.join(processed_dir, "no_tags_corpus.json")
                save_to_json(processed_objects, corpus_path)

            # Step 4: Embed the corpus
            embed_corpus(
                corpus_path=corpus_path,
                chroma_path=index_dir,
                collection_name="no_tags_collection",
                batch_size=10,
            )

            # Step 5: Query the vector store
            with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
                retriever = Retriever()

                # Query the vector store
                query_results = retriever.query("test query", n_results=2)

                # Generate an answer
                chunks = []
                for i, doc_id in enumerate(query_results["ids"][0]):
                    chunk = MagicMock()
                    chunk.text = query_results["documents"][0][i]
                    chunk.metadata = query_results["metadatas"][0][i]
                    chunks.append(chunk)

                answer_result = retriever.generate_answer("What is the answer?", chunks)

                # Check that the answer was generated
                assert "answer" in answer_result
                assert (
                    answer_result["answer"] == "This is a sample response from the LLM."
                )

    @patch("app.crawler.crawl.fetch_url")
    @patch("app.crawler.crawl.extract_links")
    @patch("app.crawler.add_metadata_and_tags.KeyBERT")
    @patch("app.embedder.embed_corpus.chromadb.PersistentClient")
    @patch("app.embedder.embed_corpus.embedding_functions.DefaultEmbeddingFunction")
    @patch("app.retriever.ask.chromadb.PersistentClient")
    def test_pipeline_with_missing_api_key(
        self,
        mock_retriever_client,
        mock_embedding_function,
        mock_embedder_client,
        mock_keybert,
        mock_extract_links,
        mock_fetch_url,
        temp_dir,
    ):
        """Test the pipeline with missing OpenAI API key."""
        # Set up the temp directories
        html_dir = os.path.join(temp_dir, "html")
        processed_dir = os.path.join(temp_dir, "processed")
        index_dir = os.path.join(temp_dir, "index")

        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(processed_dir, exist_ok=True)
        os.makedirs(index_dir, exist_ok=True)

        # Set up the mocks for crawling
        mock_fetch_url.return_value = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Page</title>
        </head>
        <body>
            <main>
                <h1>Main Heading</h1>
                <section>
                    <h2>Section 1</h2>
                    <p>This is a paragraph.</p>
                </section>
            </main>
        </body>
        </html>
        """

        mock_extract_links.return_value = []

        # Set up the mock for KeyBERT
        mock_keybert_instance = MagicMock()
        mock_keybert_instance.extract_keywords.return_value = [
            ("test", 0.9),
            ("content", 0.8),
        ]
        mock_keybert.return_value = mock_keybert_instance

        # Set up the mocks for ChromaDB
        mock_embedder_client_instance = MagicMock()
        mock_embedder_collection = MagicMock()
        mock_embedder_client_instance.get_or_create_collection.return_value = (
            mock_embedder_collection
        )
        mock_embedder_client.return_value = mock_embedder_client_instance

        mock_retriever_client_instance = MagicMock()
        mock_retriever_collection = MagicMock()
        mock_retriever_client_instance.get_or_create_collection.return_value = (
            mock_retriever_collection
        )
        mock_retriever_client.return_value = mock_retriever_client_instance

        # Step 1: Crawl the website
        with patch.dict(os.environ, {"PYTHONPATH": os.getcwd()}):
            content_dict = recursive_crawl(
                "https://example.com/page", max_pages=1, save_to_files=True
            )

            # Write the HTML file to the temp directory
            file_path = os.path.join(html_dir, "test_page.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content_dict["https://example.com/page"])

            # Step 2: Process the HTML files
            results = process_all_html_files(html_dir)

            # Create content objects
            content_objects = []
            for file_path, content in results.items():
                page_title = content["title"]
                page_name = os.path.basename(file_path).replace(".html", "")

                for section in content["sections"]:
                    section_header = section["header"]

                    for chunk in section["chunks"]:
                        chunk_object = {
                            "page_title": page_title,
                            "page_name": page_name,
                            "section_header": section_header,
                            "content": chunk["content"],
                            "content_html": chunk["content_html"],
                        }
                        content_objects.append(chunk_object)

            # Step 3: Add metadata and tags
            with patch(
                "app.crawler.add_metadata_and_tags.content_objects", content_objects
            ):
                processed_objects = process_content_objects()

                # Save to JSON
                corpus_path = os.path.join(processed_dir, "api_key_corpus.json")
                save_to_json(processed_objects, corpus_path)

            # Step 4: Embed the corpus
            embed_corpus(
                corpus_path=corpus_path,
                chroma_path=index_dir,
                collection_name="api_key_collection",
                batch_size=10,
            )

            # Step 5: Try to initialize the retriever with missing API key
            with patch.dict(os.environ, {"OPENAI_API_KEY": ""}):
                # Should raise ValueError
                with pytest.raises(ValueError) as excinfo:
                    Retriever()

                # Check the exception
                assert "OPENAI_API_KEY" in str(excinfo.value)
