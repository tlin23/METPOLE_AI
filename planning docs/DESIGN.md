# Modular Backend Refactor — Developer Specification

## Project Objective

Refactor the backend codebase to achieve **modularity, testability, and maintainability**.
Separate concerns into distinct layers (API, CLI, Services, DB), standardize error handling, and improve test coverage to enable rapid, safe iteration and clearer code.

---

## Requirements

### Functional Requirements

1. **Modularization**

   - All business logic must reside in a new `services/` layer, separated from API and CLI entry points.
   - All database access (CRUD, queries) must be in a new `db/` layer.
   - API routes (`routes.py`) and CLI scripts (`admin.py`, `feedback.py`, etc.) should be thin, delegating work to the service layer.

2. **CLI Split**

   - Split current `admin.py` into “access management” and “database CRUD.”
   - Feedback commands should move into CRUD CLI.
   - Each CLI command should only call service functions (never DB or models directly).

3. **Standardization**

   - Error handling should be consistent across API and CLI, using app-specific exceptions.
   - All service and DB functions must be fully tested.

4. **Testing**

   - Full suite of tests (unit, integration, regression) covering API, CLI, services, and DB.
   - Baseline tests must be written to capture current behavior before refactoring.

### Non-Functional Requirements

- **Readability:**
  Code should be self-explanatory, modular, and follow Python best practices.
- **Maintainability:**
  All new modules must be testable in isolation.
- **Extensibility:**
  Future business logic changes should affect only the service layer.
- **Atomicity:**
  All migration steps must be atomic and verifiable by tests.

---

## Architecture Overview

### Layered Design

- **API Layer** (`routes.py`)

  - Defines FastAPI endpoints and request/response schemas.
  - No business logic or DB access.
  - Calls into the `services/` layer for all operations.
  - Handles and formats exceptions from services.

- **CLI Layer** (`admin.py`, `feedback.py`, future CLI scripts)

  - Handles argument parsing, user output.
  - No business logic or DB access.
  - Calls `services/` for all operations.
  - Handles and formats exceptions from services.

- **Service Layer** (`services/`)

  - Contains all business logic, validation, and orchestration.
  - Calls into `db/` for data access.
  - Raises only app-specific exceptions for known errors.
  - Structured by domain: e.g., `QuestionService`, `AnswerService`, `SessionService`, `FeedbackService`, `AccessService`.

- **DB Layer** (`db/`)

  - Handles all raw data persistence and queries.
  - No business logic.
  - Structured as repositories or DAOs, each responsible for one entity/table.

---

### Directory Structure

```
backend/server/
  api/
    routes.py
    models.py
  cli/
    admin.py
    feedback.py
    access.py       # New for access management CLI
    db_crud.py      # New for CRUD CLI commands
  services/
    __init__.py
    question_service.py
    answer_service.py
    session_service.py
    feedback_service.py
    access_service.py
    # ...other services as needed
  db/
    __init__.py
    repositories.py
    models/         # ORM/data models (as needed)
  exceptions.py     # App-specific exception hierarchy
  tests/
    test_routes.py
    test_admin_cli.py
    test_feedback_cli.py
    test_services.py
    test_repositories.py
    # ...other test files
```

---

## Data Handling & Flow

- **Data access** is only allowed through the `db/` layer.
- **Business rules and cross-table logic** live in `services/`.
- **API and CLI** call only service methods.
- **No direct access** to models or DB from routes or CLI scripts.

### Data Lifecycles

- Create, read, update, delete (CRUD) for each entity is implemented in repositories.
- Services enforce invariants (e.g., every question must have an answer, every feedback links to an answer).
- Deleting a question must cascade delete its answer and feedback (enforced in service, delegated to repository).
- Soft deletes are not used; all deletes are hard (per requirements).

---

## Error Handling

- All errors raised in `services/` should be subclasses of `AppException` (defined in `exceptions.py`).
- Example exceptions:

  - `NotFoundException`
  - `ValidationException`
  - `AccessDeniedException`

- **API**: Catch these exceptions and return clear, standardized JSON error responses.
- **CLI**: Catch these exceptions and print human-readable error messages.

---

## Testing Strategy

1. **Baseline Testing**

   - Before refactor, write comprehensive tests for all current API and CLI behaviors.

2. **Unit Testing**

   - Each function/method in services and repositories must have direct unit tests.
   - Use mocking to isolate dependencies.

3. **Integration Testing**

   - End-to-end tests that verify full workflow through API and CLI layers, touching actual service and DB code.

4. **Regression/Edge Testing**

   - Ensure all previously supported edge cases are covered after each stage.
   - Add regression tests for all bug fixes and migration issues.

5. **Continuous Testing**

   - All stages of the migration must pass tests before moving forward.
   - Use CI for automated test runs.

---

## Migration and Implementation Process

Follow this iterative, atomic approach:

1. **Write baseline tests for API and CLI.**
2. **Set up `services/` and `db/` directories with interfaces and stubs.**
3. **Move all database access logic into the `db/` layer, test thoroughly.**
4. **Migrate all business logic into service modules, test each.**
5. **Refactor API endpoints to call only service methods.**
6. **Refactor CLI commands to call only service methods.**
7. **Implement and enforce standardized error handling.**
8. **Expand and unify all tests (unit, integration, regression).**
9. **Remove any legacy code not needed in the new structure.**
10. **Final QA: Ensure all modules are integrated and all tests pass.**

---

## Best Practices and Conventions

- **Domain-driven:**
  Services and repositories are organized by business domain/entity.
- **Thin entrypoints:**
  API and CLI layers should do no more than parameter parsing and error formatting.
- **Test first:**
  All migration is test-driven; no code is left untested.
- **Consistent error responses:**
  No leaking of raw exceptions—only app-specific, user-friendly errors.
- **Documentation:**
  Each service and repository should be documented with clear docstrings.

---

## Deliverables

- New `services/` and `db/` modules, fully tested.
- Updated `api/` and `cli/` modules, thinned out and delegating to services.
- Exception handling and formatting, consistent across all interfaces.
- Comprehensive tests for all modules, with all legacy tests passing.
- Clean, modular, and maintainable backend ready for future feature growth.

---
