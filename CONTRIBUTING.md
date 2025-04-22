# Contributing to Metropole.AI

Thank you for your interest in contributing to Metropole.AI! This document provides guidelines and instructions for setting up your development environment and contributing to the project.

## 📋 Table of Contents

- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Using the Makefile](#using-the-makefile)
- [Pre-commit Hooks](#pre-commit-hooks)
- [Testing](#testing)
- [Best Practices](#best-practices)
- [Project Structure](#project-structure)

## 🔧 Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/METPOLE_AI.git
   cd METPOLE_AI
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install development dependencies**

   ```bash
   pip install pytest pytest-cov black ruff mypy pre-commit
   ```

5. **Set up pre-commit hooks**

   ```bash
   pre-commit install
   ```

6. **Create a `.env` file**

   ```env
   OPENAI_API_KEY=your-openai-api-key
   CHROMA_DB_PATH=./data/index
   SECRET_KEY=your-secret-key
   ```

## 🔄 Development Workflow

1. **Create a new branch for your feature or bugfix**

   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes and commit them**

   ```bash
   git add .
   git commit -m "Your descriptive commit message"
   ```

   The pre-commit hooks will automatically run to check and format your code.

3. **Push your changes to your fork**

   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create a pull request**

   Open a pull request from your fork to the main repository.

## 🛠️ Using the Makefile

The project includes a Makefile that defines common development tasks:

- **Run the FastAPI server with hot reload**

  ```bash
  make run
  ```

- **Run all tests**

  ```bash
  make test
  ```

- **Run unit tests only**

  ```bash
  make test-unit
  ```

- **Run tests with coverage**

  ```bash
  make test-cov
  ```

- **Run linting checks**

  ```bash
  make lint
  ```

- **Format code**

  ```bash
  make format
  ```

- **Run the crawler**

  ```bash
  make crawl
  ```

- **Run the embedding process**

  ```bash
  make embed
  ```

- **Run the full pipeline**

  ```bash
  make pipeline
  ```

- **Clean up cache and temporary files**

  ```bash
  make clean
  ```

- **Display help**

  ```bash
  make help
  ```

## 🔍 Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality. The hooks include:

- **trailing-whitespace**: Removes trailing whitespace
- **end-of-file-fixer**: Ensures files end with a newline
- **check-yaml**: Validates YAML files
- **check-added-large-files**: Prevents large files from being committed
- **check-merge-conflict**: Checks for merge conflict markers
- **debug-statements**: Checks for debugger imports and py37+ breakpoint() calls
- **mixed-line-ending**: Ensures consistent line endings
- **black**: Formats Python code
- **ruff**: Lints Python code

To run the pre-commit hooks manually:

```bash
pre-commit run --all-files
```

## 🧪 Testing

The project includes a comprehensive test suite. For more details, see [tests/README.md](tests/README.md).

- **Run all tests**

  ```bash
  pytest
  ```

- **Run specific test categories**

  ```bash
  # Run only unit tests
  pytest -m unit

  # Run only integration tests
  pytest -m integration

  # Run only crawler tests
  pytest -m crawler

  # Run only embedding tests
  pytest -m embedding

  # Run only retrieval tests
  pytest -m retrieval

  # Run only edge case tests
  pytest -m edge_case
  ```

- **Run tests with coverage**

  ```bash
  pytest --cov=app tests/
  ```

## 💡 Best Practices

### Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines
- Use [Google-style docstrings](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings)
- Use type hints for all function parameters and return values
- Keep functions small and focused on a single task
- Use descriptive variable and function names

### Commit Messages

- Use clear, descriptive commit messages
- Start with a verb in the imperative mood (e.g., "Add", "Fix", "Update")
- Reference issue numbers when applicable

### Pull Requests

- Keep pull requests focused on a single feature or bugfix
- Include tests for new features or bugfixes
- Update documentation as needed
- Ensure all tests pass before submitting

### Documentation

- Update README files when adding new features
- Document public functions and classes with docstrings
- Include examples in docstrings when appropriate
- Keep documentation up-to-date with code changes

## 📁 Project Structure

The project is organized into the following directories:

- **app/**: Main application code
  - **api/**: FastAPI routes and API endpoints
  - **crawler/**: Web crawling and content extraction
  - **embedder/**: Text embedding and vector storage
  - **retriever/**: Vector retrieval and question answering
  - **utils/**: Utility functions
  - **vector_store/**: Vector database initialization and demo

- **data/**: Data storage
  - **html/**: Raw HTML files
  - **processed/**: Processed content and corpus
  - **index/**: Vector database files
  - **logs/**: Log files

- **frontend/**: React frontend application

- **tests/**: Test suite
  - **test_crawler/**: Tests for crawler component
  - **test_embedder/**: Tests for embedder component
  - **test_retriever/**: Tests for retriever component
  - **test_integration/**: Integration tests

For more detailed information about specific components, refer to the README files in each directory:

- [app/crawler/README.md](app/crawler/README.md): HTML content extraction
- [app/embedder/README.md](app/embedder/README.md): Corpus embedding
- [tests/README.md](tests/README.md): Test suite structure and usage
