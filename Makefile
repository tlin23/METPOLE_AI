# Metropole.AI Makefile
# This file defines common development tasks

.PHONY: help serve serve-prod front test test-server test-pipeline lint format \
	clean repo repo-py repo-js repo-py-js repo-server reset-env \
	crawl sort parse embed pip-prod-full pip-dev-full pip-dev-fast pip-dev-local \
	clean-crawl clean-sort clean-parse clean-embed clean-all \
	admin-status admin-list admin-add admin-remove admin-reset-quota admin-check-quota
# Default URL for crawling
START_URL := https://www.metropoleballard.com/home
MAX_PAGES := 50

# Pipeline configuration
OUTPUT_DIR := ./backend/data
DEV_OUTPUT := $(OUTPUT_DIR)
PROD_OUTPUT := $(OUTPUT_DIR)
COLLECTION := metropole

# Base command for pipeline steps
PIPELINE_CMD := python -m backend.data_processing.pipeline.pipeline_cli

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
	@echo "Admin Commands (backend/server/cli/admin.py):"
	@echo "  make admin-status         - Check system status and admin privileges"
	@echo "  make admin-list           - List all admin users (requires admin privileges)"
	@echo "  make admin-add email=...  - Promote a user to admin (replace ... with email)"
	@echo "  make admin-remove email=... - Remove admin status from a user (replace ... with email)"
	@echo "  make admin-reset-quota email=... - Reset question quota for a user (replace ... with email)"
	@echo "  make admin-check-quota email=... - Check question quota for a user (replace ... with email)"
	@echo ""
	@echo "Pipeline Commands:"
	@echo "  make crawl       - Crawl web content"
	@echo "  make sort        - Sort crawled content"
	@echo "  make parse       - Parse sorted content"
	@echo "  make embed       - Embed parsed content"
	@echo "  make pip-prod-full - Run full pipeline in production mode"
	@echo "  make pip-dev-full  - Run full pipeline in development mode"
	@echo "  make pip-dev-fast  - Run parse and embed in development mode"
	@echo "  make pip-dev-local - Run sort, parse, and embed in development mode"
	@echo ""
	@echo "Utility Commands:"
	@echo "  make clean       - Clean up cache and temporary files"
	@echo "  make repo        - Run repomix on all files except markdown"
	@echo "  make repo-py     - Run repomix on Python files only"
	@echo "  make repo-js     - Run repomix on JavaScript files only"
	@echo "  make repo-py-js  - Run repomix on Python and JavaScript files"
	@echo "  make repo-server - Run repomix on server files"
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
	PYTHONPATH=backend ./backend/venv/bin/python -m pytest backend/server/tests backend/data_processing/tests

# Run only server tests
test-server:
	PYTHONPATH=backend ./backend/venv/bin/python -m pytest backend/server/tests --cov=backend.server --cov-report=term-missing --cov-report=html --cov-fail-under=90

# Run only data processing pipeline tests
test-pipeline:
	PYTHONPATH=backend ./backend/venv/bin/python -m pytest backend/data_processing/tests

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

repo-js:
	npx repomix frontend/src --include '**/*.js'

repo-py-js:
	npx repomix . --include '**/*.py', 'frontend/src'

repo-server:
	npx repomix backend/server --include '**/*.py'

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

# Pipeline targets
crawl:
	$(PIPELINE_CMD) --step crawl --input "$(START_URL)" --output $(OUTPUT_DIR) --collection $(COLLECTION) --allowed-domains metropoleballard.com

sort:
	$(PIPELINE_CMD) --step sort --input $(OUTPUT_DIR)/dev/local_input_source --output $(OUTPUT_DIR) --collection $(COLLECTION)

parse:
	$(PIPELINE_CMD) --step parse --input $(OUTPUT_DIR)/dev/sorted_documents --output $(OUTPUT_DIR) --collection $(COLLECTION)

embed:
	$(PIPELINE_CMD) --step embed --input $(OUTPUT_DIR)/dev/json_chunks --output $(OUTPUT_DIR) --collection $(COLLECTION)

# Full pipeline runs
pip-prod-full:
	$(PIPELINE_CMD) --step all --input "$(START_URL)" --output $(OUTPUT_DIR) --collection $(COLLECTION) --allowed-domains metropoleballard.com --production

pip-dev-full:
	$(PIPELINE_CMD) --step all --input "$(START_URL)" --output $(OUTPUT_DIR) --collection $(COLLECTION) --allowed-domains metropoleballard.com

pip-dev-fast:
	$(PIPELINE_CMD) --step parse --input $(OUTPUT_DIR)/dev/sorted_documents --output $(OUTPUT_DIR) --collection $(COLLECTION)
	$(PIPELINE_CMD) --step embed --input $(OUTPUT_DIR)/dev/json_chunks --output $(OUTPUT_DIR) --collection $(COLLECTION)

pip-dev-local:
	$(PIPELINE_CMD) --step sort --input $(OUTPUT_DIR)/dev/local_input_source --output $(OUTPUT_DIR) --collection $(COLLECTION)
	$(PIPELINE_CMD) --step parse --input $(OUTPUT_DIR)/dev/sorted_documents --output $(OUTPUT_DIR) --collection $(COLLECTION)
	$(PIPELINE_CMD) --step embed --input $(OUTPUT_DIR)/dev/json_chunks --output $(OUTPUT_DIR) --collection $(COLLECTION)

# Cleaning targets
clean-crawl:
	rm -rf $(OUTPUT_DIR)/dev/local_input_source $(OUTPUT_DIR)/dev/sorted_documents $(OUTPUT_DIR)/dev/json_chunks $(OUTPUT_DIR)/dev/chroma_db
	rm -rf $(OUTPUT_DIR)/prod/local_input_source $(OUTPUT_DIR)/prod/sorted_documents $(OUTPUT_DIR)/prod/json_chunks $(OUTPUT_DIR)/prod/chroma_db

clean-sort:
	rm -rf $(OUTPUT_DIR)/dev/sorted_documents $(OUTPUT_DIR)/dev/json_chunks $(OUTPUT_DIR)/dev/chroma_db
	rm -rf $(OUTPUT_DIR)/prod/sorted_documents $(OUTPUT_DIR)/prod/json_chunks $(OUTPUT_DIR)/prod/chroma_db

clean-parse:
	rm -rf $(OUTPUT_DIR)/dev/json_chunks $(OUTPUT_DIR)/dev/chroma_db
	rm -rf $(OUTPUT_DIR)/prod/json_chunks $(OUTPUT_DIR)/prod/chroma_db

clean-embed:
	rm -rf $(OUTPUT_DIR)/dev/chroma_db
	rm -rf $(OUTPUT_DIR)/prod/chroma_db

clean-all:
	rm -rf $(OUTPUT_DIR)

# === Admin CLI commands ===
admin-status:
	python3 -m backend.server.cli.admin status

admin-list:
	python3 -m backend.server.cli.admin list

admin-add:
	@if [ -z "$$email" ]; then echo "Usage: make admin-add email=someone@example.com"; exit 1; fi; \
	python3 -m backend.server.cli.admin add $$email

admin-remove:
	@if [ -z "$$email" ]; then echo "Usage: make admin-remove email=someone@example.com"; exit 1; fi; \
	python3 -m backend.server.cli.admin remove $$email

admin-reset-quota:
	@if [ -z "$$email" ]; then echo "Usage: make admin-reset-quota email=someone@example.com"; exit 1; fi; \
	python3 -m backend.server.cli.admin quota reset $$email

admin-check-quota:
	@if [ -z "$$email" ]; then echo "Usage: make admin-check-quota email=someone@example.com"; exit 1; fi; \
	python3 -m backend.server.cli.admin quota check $$email
