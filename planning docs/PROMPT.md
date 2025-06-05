# Modular Refactor and Testing Blueprint

## Project Blueprint: Modular, Testable Refactor

### High-Level Stages

1. **Establish Baseline**

   - Write integration tests to capture current behavior.
   - Freeze functionality—no new features until refactor is complete.

2. **Prepare for Modularization**

   - Identify all business logic currently spread across routes, admin, feedback, and other modules.
   - Catalog CRUD, domain logic, and DB access in routes, CLI, database, and retriever.

3. **Set Up `services/` and `db/` Foundations**

   - Create `services/` and `db/` directories.
   - Define clear interface contracts for services and DB repositories.
   - Define app-specific exception classes for standardized error handling.

4. **Refactor DB Layer**

   - Move all pure DB access code to `db/`.
   - Ensure all data access goes through `db/` (not direct ORM calls elsewhere).
   - Test: Verify CRUD in isolation.

5. **Refactor Service Layer**

   - Move business logic out of routes/CLI into `services/`.
   - Each service uses only `db/` for data access.
   - Test: Unit and integration tests on services.

6. **Refactor API Layer**

   - Update `routes.py` to call into services only.
   - Add error/response formatting from service exceptions.

7. **Refactor CLI Layer**

   - Update CLI commands to call into services only.
   - Add error/response formatting for CLI.

8. **Unify Testing and Error Handling**

   - Ensure standardized error handling across API and CLI.
   - Comprehensive test coverage (unit, integration, CLI/API).

9. **Wiring & Cleanup**

   - Remove obsolete/legacy code.
   - Ensure all modules are integrated and test-passing.

---

## Breakdown Into Iterative Chunks

### First Pass: Medium Chunks

1. Write baseline tests for current routes and CLI behavior.
2. Create `services/` and `db/` directories, and define interface skeletons.
3. Move all DB access code from `routes.py`, `admin.py`, and `feedback.py` to `db/`.
4. Move business logic from above into new `services/`.
5. Refactor `routes.py` to delegate to services only.
6. Refactor CLI modules to delegate to services only.
7. Implement standardized error handling with app-specific exceptions.
8. Expand and unify tests for all layers.
9. Cleanup, integration, and removal of old code.

---

### Second Pass: Small, Safe Steps

#### Chunk 1: Write Baseline Tests

- 1.1 Write integration tests for API endpoints in `routes.py`.
- 1.2 Write CLI tests for `admin.py` and `feedback.py`.

#### Chunk 2: Set Up Structure

- 2.1 Create empty `services/` and `db/` directories.
- 2.2 Add `__init__.py` and placeholder files for future services/db modules.
- 2.3 Define base repository and service interfaces as Python ABCs or Protocols.

#### Chunk 3: Move and Refactor DB Layer

- 3.1 Move models and DB access functions to `db/` modules.
- 3.2 Refactor any ORM or SQL logic to live only in `db/`.
- 3.3 Add tests for `db/` repositories.

#### Chunk 4: Move and Refactor Service Layer

- 4.1 Move pure business logic from API/CLI to `services/`.
- 4.2 Make services depend on `db/` repositories only.
- 4.3 Add unit tests for service methods.

#### Chunk 5: Refactor API Layer

- 5.1 Change `routes.py` endpoints to call into services only.
- 5.2 Handle exceptions from services and format error responses.

#### Chunk 6: Refactor CLI Layer

- 6.1 Update `admin.py` and `feedback.py` to use services only.
- 6.2 Handle exceptions and format CLI error messages.

#### Chunk 7: Standardize Error Handling

- 7.1 Define custom exception classes for app errors.
- 7.2 Ensure both API and CLI catch and format these exceptions.

#### Chunk 8: Expand & Unify Tests

- 8.1 Add/expand tests for cross-layer workflows (API + service + db, CLI + service + db).
- 8.2 Add regression tests for any legacy edge cases.

#### Chunk 9: Wire Up & Cleanup

- 9.1 Remove unused legacy code from routes/CLI.
- 9.2 Final test and QA pass.

---

### Third Pass: Atomic Steps

#### Chunk 1: Write Baseline Tests

- 1.1.1 Add a test file for API endpoints (`test_routes.py`).
- 1.1.2 Write test cases for each route’s current behavior.
- 1.2.1 Add a test file for CLI (`test_admin_cli.py`, `test_feedback_cli.py`).
- 1.2.2 Write test cases for each CLI command.

#### Chunk 2: Set Up Structure

- 2.1.1 Create `backend/server/services/` and `backend/server/db/`.
- 2.1.2 Add `__init__.py` files to both.
- 2.2.1 Add placeholder files: `question_service.py`, `answer_service.py`, etc.
- 2.2.2 Add `repositories.py` in `db/`.
- 2.3.1 Define base interfaces (`BaseRepository`, `BaseService`).

#### Chunk 3: Move and Refactor DB Layer

- 3.1.1 Move models from `server/database/models/` to `db/` as needed.
- 3.1.2 Move all direct DB access functions into corresponding repositories.
- 3.2.1 Refactor original code to import from `db/`.
- 3.3.1 Write unit tests for each repository function.

#### Chunk 4: Move and Refactor Service Layer

- 4.1.1 Identify all business logic in API/CLI.
- 4.1.2 Move each logical group into its service module.
- 4.2.1 Make services depend on repositories, not models directly.
- 4.3.1 Write tests for service logic (mock repositories as needed).

#### Chunk 5: Refactor API Layer

- 5.1.1 Refactor each endpoint to call the relevant service.
- 5.2.1 Replace inline error handling with service exception catching.

#### Chunk 6: Refactor CLI Layer

- 6.1.1 Refactor each CLI command to call the relevant service.
- 6.2.1 Replace inline error handling with standardized error formatting.

#### Chunk 7: Standardize Error Handling

- 7.1.1 Define `AppException` and subclasses in a new `exceptions.py`.
- 7.2.1 Refactor services to raise only app exceptions.
- 7.2.2 Update API/CLI layers to catch and handle these.

#### Chunk 8: Expand & Unify Tests

- 8.1.1 Add tests that span API/service/db.
- 8.2.1 Add regression/edge case tests for CLI/service/db.

#### Chunk 9: Wire Up & Cleanup

- 9.1.1 Remove direct DB/model logic from API and CLI.
- 9.2.1 Delete any legacy code no longer in use.
- 9.3.1 Do a final run of all tests to confirm green.

---

## Final "LLM Prompt" Series for Each Step

Below, you’ll find prompts for a code-gen LLM. Each prompt is atomic and builds on the last. Each is tagged and ready for pasting.

### Prompt 1: Write Baseline API and CLI Tests

```text
You are working on a FastAPI + CLI project.
First, add a new test file `test_routes.py` under `backend/server/tests/`.
Write integration test cases for each existing endpoint in `routes.py`, using FastAPI’s TestClient.
Test expected successful responses and main error cases.

Then, add `test_admin_cli.py` and `test_feedback_cli.py` under `backend/server/tests/`.
Write tests for each CLI command as they currently behave, using `subprocess` or `CliRunner` as appropriate.

Do NOT change any production code. Just add the new test files and make sure the current system’s behaviors are captured in tests.
```

### Prompt 2: Set Up Service and DB Directory Structure

```text
Create two new directories under `backend/server/`: `services/` and `db/`.
Add `__init__.py` files to both.

Inside `services/`, add empty modules for each main app domain (e.g., `question_service.py`, `answer_service.py`, `session_service.py`, `feedback_service.py`, `access_service.py`).

Inside `db/`, add a `repositories.py` file for DB access code, and copy over any reusable base models or code from `server/database/models/` that are needed for DB ops.

Define minimal Python abstract base classes or Protocols for `BaseRepository` (in `db/`) and `BaseService` (in `services/`) for code organization.

Do NOT move logic yet—just set up structure and stubs.
```

### Prompt 3: Move and Refactor DB Layer

```text
Move all pure database access code (CRUD, queries, model-to-db mapping) from `server/database/` and any direct DB calls from `routes.py`, `admin.py`, and `feedback.py` into the new `db/repositories.py`.

Refactor the code so that only `db/repositories.py` (and the `db/` package) is responsible for low-level data access.

Write or move unit tests for each repository function to `tests/`.

Update imports in old modules to pull from the new `db/` package.

Do NOT move business logic—just data access.
```

### Prompt 4: Move and Refactor Service Layer

```text
Identify all business logic currently in API routes, admin CLI, and feedback CLI.

Move this logic into corresponding service classes in `services/`, grouped by domain (question, answer, session, feedback, access).

Each service should depend only on `db/` repositories for data access.

Write unit tests for each service in `tests/`, mocking out repository dependencies.

Leave API and CLI as thin layers that still call into old code for now—do not update those yet.
```

### Prompt 5: Refactor API Layer to Use Services

```text
Refactor every FastAPI endpoint in `routes.py` so that it calls the relevant `services/` class or function, and never talks directly to the DB or models.

Handle all business logic, validation, and data processing in `services/` only.

For error handling, catch exceptions raised from the service layer and return standardized error responses in API format.

Add/expand tests to cover all updated endpoint behaviors.
```

### Prompt 6: Refactor CLI Layer to Use Services

```text
Refactor all CLI commands in `admin.py` and `feedback.py` so they call only into the new `services/` layer, and never call DB/models directly.

Update all CLI output and error handling to use standardized exception handling—catching app-specific exceptions and formatting them for CLI output.

Add/expand tests to ensure CLI commands function as before, now via services.
```

### Prompt 7: Implement Standardized Error Handling

```text
Create an `exceptions.py` module (in `backend/server/` or shared utils).

Define an `AppException` base class and domain-specific subclasses (e.g., `NotFoundException`, `ValidationException`, `AccessDeniedException`).

Refactor all `services/` to raise only these exceptions, never generic exceptions.

Update both API and CLI layers to catch only `AppException` subclasses, returning/printing error messages in a standardized way.

Add/expand tests to cover error cases across API, CLI, and service layers.
```

### Prompt 8: Expand and Unify Tests

```text
Expand test coverage for all workflows (API → service → db, CLI → service → db).
Include integration, edge case, and regression tests, especially for any tricky data or permission scenarios.

Make sure tests cover both expected outputs and error conditions.

Refactor any legacy test code to use new services/db layers.

All new and old tests must pass.
```

### Prompt 9: Wire Up and Cleanup

```text
Remove any remaining legacy logic from API and CLI that has been superseded by `services/` and `db/`.

Delete or archive obsolete modules and code paths.

Verify the system by running all tests (unit, integration, CLI, API).

The codebase should now be fully modular, testable, and up to best practices.
```

---
