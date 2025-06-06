# Test Coverage Specification for Server Codebase

## Overview

This specification defines the requirements, design, and testing strategy to ensure that all main business logic of the server codebase is robustly and meaningfully covered by tests. The goal is to provide confidence in code correctness, prevent regressions, and facilitate safe refactoring.

---

## Requirements

### 1. Coverage Scope

- **All core business logic** must be covered by tests, including:

  - API endpoint logic (integration-style tests)
  - Model and business logic methods (unit-style tests)

- **Authentication/authorization** should be mocked to focus on business logic.
- **External services** (OpenAI, Google OAuth, etc.) must always be mocked in all tests.

### 2. Data Layer

- **All tests run against a real, isolated SQLite test database** (never the production DB).
- Database state is set up and torn down per test or test module to guarantee isolation.

### 3. Factories/Fixtures

- **Factory-style fixtures** are used to create test users, sessions, questions, answers, and feedback entries.
- Factories should support creating objects with interrelated dependencies.

### 4. Directory Structure

```
server/
  tests/
    integration/     # Integration tests: API endpoint coverage with real DB, mocked external APIs, mocked auth
    unit/            # Unit tests: Direct model/business logic testing with real DB
    factories/       # (optional) Custom pytest factories or use conftest.py for common fixtures
    conftest.py      # Shared fixtures and test DB setup
```

### 5. Code Coverage

- Code coverage reporting is enabled (e.g., via `pytest-cov`).
- Coverage must be tracked for all main server modules.
- Gaps in coverage must be tracked and prioritized for additional tests.

---

## Architecture & Data Handling

### 1. Test Database

- Use a dedicated SQLite database file (e.g., `test.db`) set via environment variable or test config.
- **Never** connect to or mutate the production DB during tests.
- Schema is initialized before the test session.
- Tables are truncated/cleaned between tests for isolation.

### 2. Test Data Factories

- Each main model (`User`, `Session`, `Question`, `Answer`, `Feedback`) has a factory fixture for convenient test data creation.
- Factories support required relationships (e.g., creating an `Answer` auto-creates a `Question` if not provided).
- Example factory usage:

  ```python
  @pytest.fixture
  def user_factory():
      def make_user(email="test@example.com", is_admin=False):
          return User.create_or_update(str(uuid4()), email, is_admin)
      return make_user
  ```

- Factories reside in `tests/factories/` or in `tests/conftest.py`.

---

## Testing Strategy

### 1. Integration Tests (`tests/integration/`)

- Use FastAPI’s `TestClient` to send HTTP requests to real API endpoints.
- Mock **only**:

  - Authentication (user context injection)
  - External APIs (OpenAI, etc.)

- Use factory fixtures to seed database with real data.
- Validate:

  - HTTP status codes and response payloads
  - Database side-effects (data is persisted/updated/deleted as expected)
  - Edge cases: quota exceeded, invalid inputs, unauthorized access, feedback for non-existent answers, etc.

- Example integration tests:

  - Ask question (`POST /api/ask`): checks answer, quota logic, DB state.
  - Feedback endpoints: create, update, fetch, delete feedback and check DB.

### 2. Unit Tests (`tests/unit/`)

- Test model methods and core business logic directly (without HTTP layer).
- No mocking of DB layer; tests use real test DB and factory data.
- Cover:

  - Object creation, updates, deletion
  - Quota increment/reset logic
  - Complex filtering, searching, or aggregation logic

- Edge cases and error handling:

  - E.g., exceeding quotas, duplicate entries, invalid foreign keys, etc.

### 3. Error Handling

- Tests should assert that the correct error is raised for:

  - Invalid input data (missing/incorrect fields)
  - Quota exceeded
  - Not found errors (e.g., feedback/answer not found)
  - Unauthorized access (if relevant, even if mocked)

- API errors should be validated against expected HTTP status and error structure.

### 4. Shared Fixtures and Test Setup

- `conftest.py` contains:

  - Test DB setup and teardown (with isolation)
  - Global mocks for external APIs/auth
  - Common factory and helper fixtures

---

## Coverage Reporting

- Use `pytest-cov` or equivalent:

  - Report overall and per-module coverage.
  - Highlight uncovered lines/branches.
  - Reports should be easy to generate (e.g., `pytest --cov=server`).

- Target: **High coverage** (ideally 90%+ for main logic; gaps are tracked and triaged).

---

## Summary Table

| Test Type        | Directory                       | Uses Real DB? | Mocks?              | Focus                                      |
| ---------------- | ------------------------------- | ------------- | ------------------- | ------------------------------------------ |
| Integration API  | tests/integration/              | Yes           | Auth, external APIs | API endpoints, business logic, persistence |
| Unit/model logic | tests/unit/                     | Yes           | External APIs only  | Model methods, pure logic, edge cases      |
| Shared Fixtures  | tests/factories/ or conftest.py | Yes           | None/Minimal        | Factory-style object creation, setup       |

---

## Developer Checklist

- [ ] Use only the test DB for all tests—never production DB.
- [ ] Always mock external APIs and authentication.
- [ ] Use factories for all model object creation.
- [ ] Write integration tests for every public API endpoint.
- [ ] Write unit tests for all important model/business logic methods.
- [ ] Validate both responses and database state in all tests.
- [ ] Assert correct error handling for all invalid scenarios.
- [ ] Maintain clear test organization in directories.
- [ ] Enable and monitor code coverage, targeting gaps as discovered.

---

## Notes

- **External services** must always be mocked (never call OpenAI, Google OAuth, etc. in CI or PR tests).
- **Test reliability and speed** are priorities; tests must be isolated, repeatable, and fast.
- **All team members** should be able to run the test suite locally and in CI with a single command.
