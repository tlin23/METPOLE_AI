# Blueprint: Robust Test Coverage for Server Codebase

---

## 1. High-Level Phases

1. **Set Up Test Environment** DONE
2. **Implement Test Factories/Fixtures** DONE
3. **Unit Test All Model Logic** DONE
4. **Integration Test All API Endpoints**
5. **Mock All External Services and Auth**
6. **Enable Code Coverage & Reporting**
7. **Iterative Gaps Review and Coverage Expansion**
8. **Maintain Directory Organization and Developer Ergonomics**

---

## 2. Break Into Chunks

### PHASE 1: Set Up Test Environment

- 1.1. Create/verify a separate SQLite test database.
- 1.2. Ensure schema is initialized and isolation between tests is enforced.
- 1.3. Add or update `conftest.py` with DB setup/teardown fixtures.

### PHASE 2: Implement Test Factories/Fixtures

- 2.1. Write reusable factory functions/fixtures for all models (`User`, `Session`, `Question`, `Answer`, `Feedback`).
- 2.2. Factories should support linked object creation (e.g., `Answer` auto-creates a `Question` if none provided).
- 2.3. Place factories in `tests/factories/` or `conftest.py`.

### PHASE 3: Unit Test All Model Logic

- 3.1. Write tests for each model’s create, update, delete methods.
- 3.2. Test business logic methods (e.g., `User.increment_question_count`, `Answer.search_answers`).
- 3.3. Include edge cases: invalid input, quota exceeded, duplicate, not found, etc.
- 3.4. Assert both return values and DB state.

### PHASE 4: Integration Test All API Endpoints

- 4.1. For each API endpoint, write a test hitting the real FastAPI service using `TestClient`.
- 4.2. Use factories to seed data; assert both API response and DB state.
- 4.3. Cover success and error paths (bad inputs, missing objects, quota exceeded, etc.).
- 4.4. Mock only external APIs and authentication.

### PHASE 5: Mock All External Services and Auth

- 5.1. Patch/mimic OpenAI, Google OAuth, and any other non-local service in both unit and integration tests.
- 5.2. For authentication, inject user/admin context as needed.

### PHASE 6: Enable Code Coverage & Reporting

- 6.1. Add `pytest-cov` (or similar) to requirements and test runner.
- 6.2. Run suite with coverage, review reports, and set targets.
- 6.3. Document coverage generation process in project docs/README.

### PHASE 7: Iterative Gaps Review and Coverage Expansion

- 7.1. Review uncovered code lines/branches; add targeted tests.
- 7.2. Add regression tests for discovered bugs.
- 7.3. Ensure new features and bugfixes come with corresponding tests.

### PHASE 8: Maintain Directory Organization and Developer Ergonomics

- 8.1. Keep `tests/integration/`, `tests/unit/`, `tests/factories/`, `conftest.py` clean and organized.
- 8.2. Add documentation/comments to fixtures and helpers.
- 8.3. Provide a “how to run” section for the test suite in the README.

---

## 3. Chunks → Small, Safe Steps (2nd Iteration)

Below, **each prompt can be given directly to a code-generation LLM** to incrementally build the suite in a test-driven, integrated way.

---

### Step 1: Test Environment Setup

**Prompt 1.1:**

```
Set up a test database for all server tests using SQLite. Add a fixture in conftest.py that:
- Creates a fresh test.db before test session
- Initializes schema from the production schema SQL
- Cleans (truncates) all tables before each test function
- Tears down (deletes) test.db after tests finish
Ensure no tests can ever write to the production DB.
```

---

### Step 2: Factory Fixtures

**Prompt 2.1:**

```
Write pytest factory fixtures for User, Session, Question, Answer, and Feedback models.
- Each factory should accept parameters for key fields.
- Support creating objects with linked dependencies (e.g., Answer factory should auto-create a Question if none provided).
- Factories should be reusable in both unit and integration tests.
Place these factories in tests/factories/ or conftest.py.
```

---

### Step 3: Unit Test Models

**Prompt 3.1:**

```
For each model (User, Session, Question, Answer, Feedback), write unit tests in tests/unit/ that:
- Cover create, update, get, list, search, and delete methods.
- Use factory fixtures for setup.
- Test normal operations and edge cases (e.g., duplicate keys, foreign key constraints, quota logic).
- Assert both the method’s return values and actual DB state.
```

---

### Step 4: Integration Test API Endpoints

**Prompt 4.1:**

```
For each API endpoint (e.g., /api/ask, /api/feedback), write integration tests in tests/integration/ that:
- Use FastAPI TestClient to hit endpoints with real HTTP requests.
- Use factories to create prerequisite data (e.g., users, sessions).
- Mock authentication to inject user/admin as needed.
- Mock all external APIs (e.g., OpenAI) using patching or fixtures.
- Assert response status code, payload, and side-effects in the database.
- Cover both success and error cases for each endpoint.
```

---

### Step 5: Mocking External Services and Auth

**Prompt 5.1:**

```
Write test fixtures or context managers to globally patch external services:
- Patch OpenAI API so no real network calls are made, returning canned responses.
- Patch Google OAuth and any other third-party auth so tests can easily set user context.
- Document where and how these mocks should be applied for both unit and integration tests.
```

---

### Step 6: Code Coverage Reporting

**Prompt 6.1:**

```
Integrate pytest-cov (or similar) into the test runner.
- Ensure a coverage report is generated with each test run.
- Set up an easy command (e.g., make test or pytest --cov=server) to generate a report.
- Output coverage summaries and highlight uncovered lines/branches.
- Add instructions to the README.
```

---

### Step 7: Closing Gaps and Regression Coverage

**Prompt 7.1:**

```
After running the test suite, examine the code coverage report.
- Identify any uncovered lines, branches, or error handling code.
- Write targeted tests for these areas in either unit or integration test directories.
- Add regression tests for any bugs fixed during implementation.
- Ensure that any new feature or fix includes appropriate tests before merging.
```

---

### Step 8: Documentation and Maintenance

**Prompt 8.1:**

```
Document the testing strategy and developer workflow:
- Update the README or a dedicated TESTING.md with instructions for running tests, adding tests, and interpreting coverage.
- Document the structure of tests, factories, and fixtures.
- Add comments to tricky fixtures and any test helper utilities for maintainability.
```

---

## 4. Review and Finalize Steps

- Each prompt can be tackled as an atomic PR or codegen job.
- Prompts build on each other—first tests will depend on test DB, then factories, then models, then endpoints, etc.
- Early and frequent testing ensures all new code is integrated and tested as soon as it is written.
- No code is orphaned; every piece is wired into the test suite and validated.
- Maintainability, readability, and clear organization are enforced at every step.

---

## 5. Summary Table (For Implementation Prompts)

| Step | Goal                   | Output                                    | Prompt Ref |
| ---- | ---------------------- | ----------------------------------------- | ---------- |
| 1    | Test DB ready          | Isolated test DB, conftest.py fixture     | 1.1        |
| 2    | Factory fixtures       | User, Session, Question, Answer, Feedback | 2.1        |
| 3    | Model unit tests       | CRUD, logic, edge cases                   | 3.1        |
| 4    | API integration tests  | Full API + DB + mocks, all endpoints      | 4.1        |
| 5    | Mock external services | OpenAI & auth globally mocked             | 5.1        |
| 6    | Code coverage reports  | pytest-cov integration & docs             | 6.1        |
| 7    | Gaps closed            | Tests for uncovered lines & regressions   | 7.1        |
| 8    | Docs & workflow        | Developer/testing workflow docs           | 8.1        |
