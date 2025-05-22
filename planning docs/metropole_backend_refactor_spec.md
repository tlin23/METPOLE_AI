
# 🔧 Metropole.AI Backend Refactor Specification

## ✨ Objective

Refactor and simplify the current backend codebase to align with the new design spec, prioritizing **clarity**, **extensibility**, and **behavioral preservation**.

---

## 🏗️ High-Level Architecture

### Components
| Component   | Responsibility                                                  |
|-------------|------------------------------------------------------------------|
| Extractors  | Fetch and organize raw documents from web or local sources      |
| Parsers     | Parse documents into structured `ContentChunk` JSON per file    |
| Embedder    | Convert `ContentChunk`s to embeddings in ChromaDB               |
| Retriever   | Query ChromaDB and generate answers via OpenAI (`ask.py`)       |
| Orchestrator| CLI pipeline script coordinating extraction → parsing → embedding|

---

## 📁 Directory Structure (Refactored)

```
backend/
  extractors/
    base.py
    web_extractor.py
    local_extractor.py

  parsers/
    base.py
    html_parser.py
    pdf_parser.py
    docx_parser.py

  models/
    content_chunk.py

  pipeline/
    main_pipeline.py
    pipeline_runner.py

  embedder/
    embedding_utils.py

  retriever/
    ask.py

  configer/
    config.py
    logging_config.py

  tests/
    extractors/
    parsers/
    pipeline/
    embedder/
    retriever/
```

---

## 🔑 Key Design Decisions

### ✅ CLI-Driven Pipeline
- `main_pipeline.py --mode [web|local|all] --production`

### ✅ Unified Extractor Interface
- `BaseExtractor` + `WebExtractor` and `LocalExtractor`
- Orchestration handles organizing files by extension

### ✅ Unified Parser Interface
- Matches `Processor` pattern
- Implementations for `html`, `pdf`, `docx`
- Stub others with `NotImplementedError`

### ✅ Unified Embedding Logic
- Single utility for embedding `ContentChunk` list

### ✅ Formal Data Model

```python
class ContentChunk(BaseModel):
    chunk_id: str
    file_name: str
    file_ext: str
    page_number: int
    text_content: str
    document_title: Optional[str] = None
```

### ✅ Disk-Based Processing
- Intermediate outputs saved to disk
- One output `.json` per input file

### ✅ Logging
- Preserve and improve verbose logging

### ✅ Configuration
- Centralized in `config.py`
- `.env` for secrets

### ❌ Excluded (for now)
- Tag extraction (KeyBERT)
- DIY classification
- Splitting `ask.py`

---

## 🧪 Testing Strategy (TDD-First)

### Layout

```
tests/
  extractors/
  parsers/
  pipeline/
  embedder/
  retriever/
```

### Focus Areas

| Component       | Test Focus                                           |
|----------------|------------------------------------------------------|
| Extractors      | File discovery, download, and output structure       |
| Parsers         | Page parsing, output format, stubs                   |
| Embedding       | Chunk hashing, upload to Chroma                     |
| Pipeline Runner | Mode branching, dry run, output validation          |
| Retriever       | Query logic, GPT output, prompt building             |

---

## 🔁 Error Handling

| Layer       | Strategy                                                     |
|------------|--------------------------------------------------------------|
| Extractors  | Log and skip failed fetches                                  |
| Parsers     | Per-file failure tolerance                                   |
| Embedding   | Fail-fast if Chroma errors                                   |
| Retriever   | Soft-fail, return empty result on error                      |
| Pipeline    | Wrap steps in try/except with logs                           |

---

## 🚧 Implementation Plan

### `models/content_chunk.py`
- [ ] Define `ContentChunk`

### `extractors/`
- [ ] `BaseExtractor`, `WebExtractor`, `LocalExtractor`

### `parsers/`
- [ ] `BaseParser`, `HTMLParser`, `PDFParser`, `DOCXParser`

### `embedder/embedding_utils.py`
- [ ] Embed chunks utility

### `pipeline/main_pipeline.py`
- [ ] CLI entrypoint

### `pipeline/pipeline_runner.py`
- [ ] Shared step logic

### `retriever/ask.py`
- [ ] Clean up, docstrings

### `tests/`
- [ ] TDD-first tests per module
