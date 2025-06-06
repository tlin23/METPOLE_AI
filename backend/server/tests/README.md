# Server Tests

This directory contains the test suite for the server codebase. The tests are organized into unit tests and integration tests, with comprehensive coverage reporting.

## Running Tests

To run the entire test suite with coverage:

```bash
# From the backend directory
pytest server/tests --cov=backend.server --cov-report=term-missing --cov-report=html --cov-fail-under=90
```

To run specific test categories:

```bash
# Run only unit tests
pytest server/tests -m unit --cov=backend.server --cov-report=term-missing

# Run only integration tests
pytest server/tests -m integration --cov=backend.server --cov-report=term-missing

# Run API endpoint tests
pytest server/tests -m api --cov=backend.server --cov-report=term-missing

# Run model tests
pytest server/tests -m model --cov=backend.server --cov-report=term-missing
```

## Coverage Reports

The test suite generates two types of coverage reports:

1. **Terminal Report**: Shows missing lines in the terminal output
2. **HTML Report**: Generates a detailed HTML report in `htmlcov/` directory

To view the HTML report, open `htmlcov/index.html` in your browser after running the tests.

## Coverage Requirements

- Minimum coverage requirement: 90%
- Tests will fail if coverage falls below this threshold
- Focus on covering all business logic and edge cases

## Test Organization

- `unit/`: Unit tests for models and business logic
- `integration/`: Integration tests for API endpoints
- `factories/`: Test data factories
- `conftest.py`: Shared fixtures and test configuration

## Adding New Tests

1. Place tests in the appropriate directory based on type
2. Use the provided test markers to categorize tests
3. Ensure new code is covered by tests
4. Run the test suite to verify coverage requirements are met

## Best Practices

- Use factory fixtures for test data creation
- Mock external services and authentication
- Test both success and error cases
- Keep tests isolated and independent
- Document complex test scenarios
