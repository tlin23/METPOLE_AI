# Design Doc: Refactor Messages Data Model to 1:1 Q\&A Structure

## Overview

Currently, the Messages table stores individual entries for both questions and answers, distinguished by a “Type” column. This leads to redundancy, complexity, and the potential for mismatched Q/A pairs. This document proposes a new data model in which each message row represents a **single Q\&A pair**. This will simplify data management, querying, and downstream processing.

---

## Goals

- Store every Q\&A as a single row.
- Remove the “Type” and “Message” columns.
- All CRUD operations, APIs, and admin CLI should use the new model.
- Update all tests and clean up legacy/unused code.

---

## New Messages Schema

| Field              | Type       | Notes                                                   |
| ------------------ | ---------- | ------------------------------------------------------- |
| message_id         | UUID / INT | Unique identifier                                       |
| session_id         | UUID / INT | Identifies conversation session                         |
| user_id            | UUID / INT | User who sent the question                              |
| question           | TEXT       | The question text                                       |
| answer             | TEXT       | The answer text                                         |
| prompt             | TEXT       | System prompt used for generating the answer            |
| question_timestamp | DATETIME   | When the question was asked                             |
| answer_timestamp   | DATETIME   | When the answer was generated                           |
| response_time      | FLOAT      | answer_timestamp - question_timestamp (can be computed) |
| retrieved_chunks   | JSON       | JSON array/object representing the retrieved chunks     |

- **All fields are required** except potentially `retrieved_chunks` (depending on pipeline flow).
- No attachments/media are supported (text only).

---

## Migration & Code Refactor Plan

### 1. Database Migration

- Drop “Type” and “Message” columns.
- Add new fields: `question`, `answer`, `prompt`, `question_timestamp`, `answer_timestamp`, `response_time`.
- Update or create the `retrieved_chunks` column as JSON type if not already.
- Remove any old/legacy fields not in the new schema.

### 2. Model Update

- Update the ORM/data class for Messages to match the new schema.

### 3. Data Ingestion Logic

- Update message creation to enforce 1:1 Q/A: a row is only created if both question and answer exist.
- Always save the system prompt used to generate the answer.
- Set timestamps appropriately; always compute `response_time` as the delta.

### 4. API & CLI

- Update all endpoints and admin CLI commands to use the new Q\&A structure.
- Remove any logic that assumes separate question/answer rows or “Type” filtering.
- All query, search, filter, and list operations should operate on Q\&A pairs.

### 5. Tests & Validation

- Update or rewrite tests to cover the new structure.
- Remove tests for deprecated functionality (e.g., creating messages with only Q or A).
- Ensure full CRUD and edge case coverage (no empty Q/A pairs, correct timestamp handling, etc.).

### 6. Code Cleanup

- Remove all unused/irrelevant code from the old design (models, routes, admin scripts, etc.).
- Clean up comments, docstrings, and documentation to reflect new model.

---

## Notes

- `response_time` can be stored for convenience, but should always match `answer_timestamp - question_timestamp`.
- `prompt` is required for every Q\&A pair and must match what was used to generate the answer.
- `retrieved_chunks` remains as a JSON array/object.

---

## Risks & Mitigations

- **Data migration risk:** Legacy messages may need a migration script to join Q/A pairs before schema changes.
- **Orphaned data:** Prevent creation of partial rows (e.g., question with no answer).
- **API/CLI compatibility:** Ensure all integrations are updated to match new schema.

---

## Deliverables

1. New Messages schema and migration scripts.
2. Updated model and data access logic.
3. Refactored APIs and admin CLI.
4. Complete test suite covering new behavior.
5. Documentation and developer notes.

---

## Out of Scope

- No support for message editing/versioning.
- No media/attachment fields.

---

## Handoff Notes

- Remove all fields not listed in the new schema.
- Update all dependent files and tests accordingly.
- Clean up code and documentation.

---
