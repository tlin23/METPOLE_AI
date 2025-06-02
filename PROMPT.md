# Cursor Implementation Prompt: Messages 1:1 Q\&A Refactor

## Objective

Refactor the Messages data model and all related logic to enforce a strict 1:1 Question-Answer (Q\&A) structure, as detailed in the design doc.

---

## Tasks

### 1. **Schema Migration**

- Remove the `Type` and `Message` columns from the Messages table.
- Add the following fields:

  - `question` (TEXT, required)
  - `answer` (TEXT, required)
  - `prompt` (TEXT, required)
  - `question_timestamp` (DATETIME, required)
  - `answer_timestamp` (DATETIME, required)
  - `response_time` (FLOAT, required; always computed as `answer_timestamp - question_timestamp`)

- Ensure `retrieved_chunks` is stored as a JSON array/object (required, but may be empty).
- Remove any legacy or unused fields not in the new schema.

### 2. **Model and Data Layer Update**

- Update the Messages ORM/model class to match the new schema exactly.
- Update data access logic to always create/save rows with complete Q\&A pairs (question + answer + required metadata).
- Make `prompt` a required field (cannot be NULL).
- Ensure `response_time` is always calculated from the timestamps.

### 3. **API and CLI Refactor**

- Update all backend endpoints and admin CLI operations to:

  - Work with the new Q\&A pair structure.
  - Remove or refactor any logic or routes that relied on message `Type` or separate Q/A entries.
  - Return, query, and filter messages as Q\&A pairs.

- Update API docs/comments as needed.

### 4. **Test Refactor**

- Update or rewrite tests to cover the new Q\&A schema and logic.
- Remove or update tests that reference the old message structure or separate Q/A rows.
- Ensure test coverage for:

  - Creating, reading, and listing Q\&A pairs
  - Timestamps and response_time calculation
  - Querying and filtering by session_id, user_id, etc.

### 5. **Code Cleanup**

- Remove unused code, models, helpers, and scripts related to the legacy message structure.
- Update docstrings and comments to reflect the new design.

### 6. **Validation & Consistency**

- Ensure that no partial messages are ever saved (a row must have both question and answer, plus all required fields).
- All references to messages in the codebase (CRUD, admin, API, retrieval, analytics) must use the new schema.

### 7. **Documentation**

- Update any developer docs, READMEs, or in-repo documentation for the new Q\&A message model.

---

## Acceptance Criteria

- There are no remaining uses of the old message structure or Type-based logic in the codebase.
- All functionality, including API, CLI, and admin operations, works with the new Q\&A pair schema.
- Tests are updated and passing.
- Code is clean, no unused models or logic remain.

---

## Notes

- Reference the design doc for full requirements and field details.
- This refactor is breaking—migrate any legacy data as necessary before deployment.
- Ask clarifying questions if any ambiguity arises during implementation.

---
