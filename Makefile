# Metropole.AI Makefile
# This file defines common development tasks

.PHONY: help serve serve-prod front test lint format \
	crawl parse embed crawl-and-parse pipeline pipeline-prod \
	local-crawl local-parse local-embed local-pipeline local-pipeline-prod \
	clean repo repo-py repo-py-js reset-env

# Default URL for crawling
START_URL := https://www.metropoleballard.com/home
MAX_PAGES := 50
OUTPUT_DIR := ./backend_refactor/data/output
COLLECTION := metropole
LOCAL_INPUT_DIR := ./backend_refactor/data/local_input_source

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
	@echo ""
	@echo "Web Processing Commands:"
	@echo "  make crawl       - Run the crawler only"
	@echo "  make parse       - Parse crawled files into chunks"
	@echo "  make embed       - Run the embedding process"
	@echo "  make crawl-and-parse - Run crawl and parse steps"
	@echo "  make pipeline    - Run the full pipeline (crawl, parse, embed)"
	@echo "  make pipeline-prod - Run the full pipeline in production mode"
	@echo ""
	@echo "Local File Processing Commands:"
	@echo "  make local-crawl - Copy and organize local files"
	@echo "  make local-parse - Parse local files into chunks"
	@echo "  make local-embed - Embed parsed local files"
	@echo "  make local-pipeline - Run full pipeline on local files"
	@echo "  make local-pipeline-prod - Run full pipeline on local files in production mode"
	@echo ""
	@echo "Utility Commands:"
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

test-qa:
	python3 backend/scripts/test_qa/ask_sample_questions.py

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

# Web Processing Commands

# Crawl website content from metropoleballard.com
web-crawl:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step crawl \
		--input $(START_URL) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-domains metropoleballard.com

# Process local files from data/documents directory
local-crawl:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step crawl \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx

# Common Pipeline Steps

# Parse crawled files into chunks
parse:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step parse \
		--input $(OUTPUT_DIR)/dev/crawled \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx

# Run the embedding process
embed:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step embed \
		--input $(OUTPUT_DIR)/dev/parsed \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION)

# Combined Pipeline Commands

# Run crawl and parse steps for website content
web-crawl-and-parse:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step crawl_and_parse \
		--input $(START_URL) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-domains metropoleballard.com \
		--allowed-extensions .html .pdf .docx

# Run crawl and parse steps for local files
local-crawl-and-parse:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step crawl_and_parse \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx

# Run the full pipeline on website content (development mode)
web-pipeline:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(START_URL) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-domains metropoleballard.com \
		--allowed-extensions .html .pdf .docx

# Run the full pipeline on website content (production mode)
web-pipeline-prod:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(START_URL) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-domains metropoleballard.com \
		--allowed-extensions .html .pdf .docx \
		--production

# Run full pipeline on local files (development mode)
local-pipeline:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx

# Run full pipeline on local files (production mode)
local-pipeline-prod:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx \
		--production

# Run full pipeline on both web and local content (development mode)
all-pipeline:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx

# Run full pipeline on both web and local content (production mode)
all-pipeline-prod:
	python3 -m backend_refactor.pipeline.pipeline_cli \
		--step all \
		--input $(LOCAL_INPUT_DIR) \
		--output $(OUTPUT_DIR) \
		--collection $(COLLECTION) \
		--allowed-extensions .html .pdf .docx \
		--production

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

# Inspect vector database contents
inspect-db:
	python -m backend.scripts.inspect_db
