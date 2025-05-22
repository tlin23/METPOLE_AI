# 🧭 Prompt Plan: Metropole.AI Backend Refactor

This plan outlines a sequence of code-generation prompts for implementing the Metropole.AI backend refactor using a TDD-first approach. Each section includes a short explanation and one code-generation prompt to feed into tools like Aider or Cursor.

---

### 1. Define `ContentChunk` Pydantic model ✅

```text
Create a file at `backend/models/content_chunk.py`. Define a `ContentChunk` class using Pydantic. The model should include:

- `chunk_id: str`
- `file_name: str`
- `file_ext: str`
- `page_number: int`
- `text_content: str`
- `document_title: Optional[str] = None`

Also write corresponding unit tests in `tests/models/test_content_chunk.py` that verify initialization and validation behavior.
```

---

### 2. Define `BaseExtractor` protocol ✅

````text
Create `backend/extractors/base.py` and define a `BaseExtractor` interface with a method:

```python
def extract(self, input_path: Path, output_dir: Path) -> List[Path]:
````

It should raise `NotImplementedError`. This will be the contract used by both extractors. Include test scaffolding in `tests/extractors/test_base.py`.

`````

### 3. Implement `WebExtractor` ✅

```text
Create `backend/extractors/web_extractor.py`. Implement a class `WebExtractor(BaseExtractor)`.

- Recursively crawls `input_path` (a URL root).
- Saves HTML files to `output_dir/html/`.
- Returns list of saved file paths.

Write test cases in `tests/extractors/test_web_extractor.py` using `unittest.mock` and `tempfile`.
```

### 4. Implement `LocalExtractor`

```text
Create `backend/extractors/local_extractor.py`. Implement `LocalExtractor(BaseExtractor)`:

- Walks `input_path` (a local dir).
- Copies/symlinks files by extension into subfolders in `output_dir/`.
- Returns list of organized file paths.

Write tests for correct file detection and output structure.
```

---

### 5. Define `BaseParser` protocol

````text
In `backend/parsers/base.py`, define a `BaseParser` with:

```python
def parse(self, file_path: Path) -> List[ContentChunk]:
`````

Stub with `NotImplementedError`. Add test scaffold in `tests/parsers/test_base.py`.

````

### 6. Implement `HTMLParser` (stub)

```text
Create `backend/parsers/html_parser.py`. Implement `HTMLParser(BaseParser)` that raises `NotImplementedError`.

Add a placeholder test in `tests/parsers/test_html_parser.py`.
````

### 7. Implement `PDFParser` (stub)

```text
Create `backend/parsers/pdf_parser.py`. Implement `PDFParser(BaseParser)` that raises `NotImplementedError`.

Include stub test in `tests/parsers/test_pdf_parser.py`.
```

### 8. Implement `DOCXParser` (stub)

```text
Create `backend/parsers/docx_parser.py`. Implement `DOCXParser(BaseParser)` that raises `NotImplementedError`.

Add stub test in `tests/parsers/test_docx_parser.py`.
```

---

### 9. Build `embed_chunks` function

````text
In `backend/embedder/embedding_utils.py`, write:

```python
def embed_chunks(chunks: List[ContentChunk], collection_name: str, db_path: str) -> None:
````

This should convert chunks to text embeddings and store them in ChromaDB.

Write tests in `tests/embedder/test_embedding_utils.py`, mocking the embedding and DB client.

````

---

### 10. Implement `pipeline_runner.py`

```text
In `backend/pipeline/pipeline_runner.py`, implement functions:

- `run_web_pipeline(...)`
- `run_local_pipeline(...)`

Each should:
1. Call the appropriate extractor
2. Dispatch to parser by file extension
3. Write parsed JSON
4. Embed using `embed_chunks(...)`

Write integration tests for these flows using temp dirs and mocks.
````

### 11. Build CLI in `main_pipeline.py`

```text
In `backend/pipeline/main_pipeline.py`, implement a CLI using `argparse`:

- Accept `--mode [web|local|all]`
- Accept `--production` flag
- Dispatch to corresponding pipeline runner functions

Add tests in `tests/pipeline/test_main_pipeline.py`.
```

---

### 12. Refactor `ask.py` for clarity

```text
In `backend/retriever/ask.py`, clean up variable names, add missing docstrings, and remove redundant logic.

Do not split the module. Write regression tests in `tests/retriever/test_ask.py` to validate retrieval and prompt construction.
```

---

### 13. End-to-end test with mocks

```text
Write an integration test in `tests/test_pipeline_e2e.py` that mocks all subcomponents and verifies a full run:

- Extraction → Parsing → Embedding → Ask
- Output: saved chunks and retriever results

Use temporary directories and fixture files for test inputs.
```
