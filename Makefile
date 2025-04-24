# Metropole.AI Makefile
# This file defines common development tasks

.PHONY: run test lint format embed crawl serve clean help

# Default Python interpreter
PYTHON := python3

# Default URL for crawling
START_URL := https://www.metropoleballard.com/home
MAX_PAGES := 50

# Default test settings
TEST_PATH := tests/

help:
	@echo "Metropole.AI Makefile"
	@echo "====================="
	@echo "Available commands:"
	@echo "  make run         - Run the FastAPI server with hot reload"
	@echo "  make serve       - Run the FastAPI server without hot reload"
	@echo "  make test        - Run all tests"
	@echo "  make test-unit   - Run unit tests only"
	@echo "  make test-cov    - Run tests with coverage report"
	@echo "  make lint        - Run linting checks (ruff, mypy)"
	@echo "  make format      - Format code with black"
	@echo "  make crawl       - Run the crawler"
	@echo "  make embed       - Run the embedding process"
	@echo "  make pipeline    - Run the full pipeline (crawl, process, embed)"
	@echo "  make clean       - Clean up cache and temporary files"

# Run the FastAPI server with hot reload
run:
	uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Run the FastAPI server without hot reload (for production-like environment)
serve:
	uvicorn main:app --host 0.0.0.0 --port 8000

# Run all tests
test:
	$(PYTHON) run_tests.py -v

# Run unit tests only
test-unit:
	$(PYTHON) run_tests.py -v -m unit

# Run tests with coverage
test-cov:
	$(PYTHON) run_tests.py -v -c --html-report

# Run linting checks
lint:
	@which ruff > /dev/null || (echo "Error: ruff is not installed. Install with 'pip install ruff'"; exit 1)
	@which mypy > /dev/null || (echo "Error: mypy is not installed. Install with 'pip install mypy'"; exit 1)
	ruff check .
	mypy app/ tests/

# Format code
format:
	@which black > /dev/null || (echo "Error: black is not installed. Install with 'pip install black'"; exit 1)
	black app/ tests/ *.py

# Run the crawler
crawl:
	$(PYTHON) -c "from app.crawler.crawl import recursive_crawl; recursive_crawl('$(START_URL)', max_pages=$(MAX_PAGES), save_to_files=True)"

# Run the embedding process
embed:
	$(PYTHON) -c "from app.embedder.embed_corpus import embed_corpus; from app.config import CHROMA_DB_PATH; embed_corpus(corpus_path='data/processed/metropole_corpus.json', chroma_path=CHROMA_DB_PATH, collection_name='metropole_documents')"

# Run the full pipeline
pipeline:
	$(PYTHON) run_pipeline.py --start-url $(START_URL) --max-pages $(MAX_PAGES)

# Clean up cache and temporary files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type f -name "coverage.xml" -delete
	find . -type f -name "repomix-output.xml" -delete

repo-py:
	npx repomix . --include '**/*.py'

repo-py-js:
	npx repomix . --include '**/*.py', 'frontend/src'
