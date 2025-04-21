# Test Suite for Metropole AI

This test suite provides comprehensive testing for all components of the Metropole AI system, including crawling, chunking, embedding, retrieval, and LLM output.

## Test Structure

The test suite is organized into the following directories:

- `tests/test_crawler/`: Tests for the crawler component, including web crawling, content extraction, and metadata/tagging
- `tests/test_embedder/`: Tests for the embedder component, including embedding generation and corpus processing
- `tests/test_retriever/`: Tests for the retriever component, including vector store querying and LLM answer generation
- `tests/test_integration/`: Integration tests that cover the entire pipeline from crawling to retrieval

## Running Tests

### Prerequisites

Make sure you have all the required dependencies installed:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov
```

### Running All Tests

To run all tests:

```bash
pytest
```

### Running Specific Test Categories

You can run specific categories of tests using markers:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only crawler tests
pytest -m crawler

# Run only chunking tests
pytest -m chunking

# Run only embedding tests
pytest -m embedding

# Run only retrieval tests
pytest -m retrieval

# Run only edge case tests
pytest -m edge_case
```

### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=app tests/
```

For a detailed HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

## Test Fixtures

The test suite uses fixtures defined in `tests/conftest.py` to provide common test data and mock objects. These fixtures include:

- Sample HTML content with various structures
- Sample content objects with metadata
- Sample corpus data with tags
- Mock ChromaDB clients
- Mock OpenAI clients
- Mock KeyBERT models

## Edge Cases

The test suite includes tests for various edge cases, such as:

- Missing tags in content
- Empty content chunks
- Malformed HTML
- Missing API keys
- Circular references in crawling
- Empty search results

## Adding New Tests

When adding new tests, follow these guidelines:

1. Place tests in the appropriate directory based on the component being tested
2. Use the existing fixtures from `conftest.py` when possible
3. Add appropriate markers to categorize the test
4. Include tests for both normal operation and edge cases
5. Use descriptive test names that clearly indicate what is being tested

## Continuous Integration

The test suite is designed to be run in a CI environment. When setting up CI, make sure to:

1. Install all dependencies
2. Set up any required environment variables (e.g., `OPENAI_API_KEY` for integration tests)
3. Run the tests with coverage reporting
4. Fail the build if test coverage falls below a certain threshold

Example GitHub Actions workflow:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Test with pytest
      run: |
        pytest --cov=app --cov-report=xml
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v1
