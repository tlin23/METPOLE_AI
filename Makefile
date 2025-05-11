# Metropole.AI Makefile
# This file defines common development tasks



.PHONY: help serve serve-prod front test lint format crawl extract embed pipeline clean repo repo-py repo-py-js reset-env

# Default Python interpreter
PYTHON := $(shell which python)

# Default URL for crawling
START_URL := https://www.metropoleballard.com/home
MAX_PAGES := 50

PIPELINE := backend/pipeline.py

# Load environment variables from .env
include .env
export

help:
	@echo "Metropole.AI Makefile"
	@echo "====================="
	@echo "Available commands:"
	@echo "  make serve       - Run the FastAPI server with hot reload"
	@echo "  make serve-prod  - Run the FastAPI server without hot reload"
	@echo "  make front       - Run the frontend development server"
	@echo "  make test        - Run all tests"
	@echo "  make lint        - Run linting checks (ruff, mypy)"
	@echo "  make format      - Format code with black"
	@echo "  make crawl       - Run the crawler"
	@echo "  make extract     - Extract text from HTML files"
	@echo "  make embed       - Run the embedding process"
	@echo "  make pipeline    - Run the full pipeline (crawl, process, embed)"
	@echo "  make clean       - Clean up cache and temporary files"
	@echo "  make repo        - Run repomix on all files except markdown"
	@echo "  make repo-py     - Run repomix on Python files only"
	@echo "  make repo-py-js  - Run repomix on Python and JavaScript files"
	@echo "  make reset-env   - Rebuild the virtual environment using Python 3.11"

# Run the FastAPI server with hot reload
serve:
	uvicorn backend.server:service --reload --host 127.0.0.1 --port 8000

# Run the FastAPI server without hot reload (for production-like environment)
serve-prod:
	uvicorn backend.server:service --host 0.0.0.0 --port 8000

# Run both frontend and backend development servers
front:
	@echo "Starting frontend development server..."
	cd frontend && npm run dev
	@echo "Frontend development server started."

# Run all tests
test:
	PYTHONPATH=backend ./backend/venv/bin/python -m pytest


# Run linting checks
lint:
	@which ruff > /dev/null || (echo "Error: ruff is not installed. Install with 'pip install ruff'"; exit 1)
	@which mypy > /dev/null || (echo "Error: mypy is not installed. Install with 'pip install mypy'"; exit 1)
	ruff check .
	mypy backend/ tests/

# Format code
format:
	@which black > /dev/null || (echo "Error: black is not installed. Install with 'pip install black'"; exit 1)
	black backend/ tests/ *.py

# Run the crawler
crawl:
	python3 -m backend.pipeline --step crawl --start-url $(START_URL) --max-pages $(MAX_PAGES)

# Extract text from html files
extract:
	python3 -m backend.pipeline --step process

# Run the embedding process
embed:
	python3 -m backend.pipeline --step embed

# Run the full pipeline
pipeline:
	python3 -m backend.pipeline --step all --start-url $(START_URL) --max-pages $(MAX_PAGES)

# Run the full prod pipeline
pipeline-prod:
	python3 -m backend.pipeline --step all --start-url $(START_URL) --max-pages $(MAX_PAGES) -p

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

repo:
	npx repomix . --ignore '**/*.md'

repo-py:
	npx repomix . --include '**/*.py'

repo-py-js:
	npx repomix . --include '**/*.py', 'frontend/src'

# Rebuild the virtual environment using Python 3.11
reset-env:
	@echo "🚨 Resetting Python 3.11 environment..."
	rm -rf venv
	python3.11 -m venv venv
	source venv/bin/activate && \
	pip install --upgrade pip setuptools wheel && \
	pip install -r requirements.txt
	@echo "✅ Environment reset complete!"
