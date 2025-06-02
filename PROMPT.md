# IMPLEMENTATION PROMPT: Docker-Proof DB Path Handling (METROPOLE_DB_PATH)

## Overview

Refactor all CLI tools, admin scripts, API endpoints, and any helper/module that connects to the SQLite database so that **all database access** uses the environment variable `METROPOLE_DB_PATH` as a required absolute path.

**No part of the codebase should connect to a DB file without `METROPOLE_DB_PATH` set, and there must be no way to specify the DB file via a CLI argument or fallback path.**

---

## Implementation Tasks

1. **Enforce single source of DB path:**

   - Remove any CLI arguments, function parameters, or config options for specifying the database path.
   - At every point a DB connection is opened (including API route handlers, CLI commands, admin scripts, and model helpers), _always_ read the value of `os.environ['METROPOLE_DB_PATH']` at connection time.
   - Ensure that the value is an absolute path (e.g., `/data/app.db` inside Docker).
   - If `METROPOLE_DB_PATH` is not set, log an error (following the existing logging/stderr style for the entry point) and exit/fail immediately:
     - For CLI: exit non-zero and print to stderr.
     - For API: log and return an error response/code.

2. **No CLI overrides:**

   - Remove any support for specifying the DB file via CLI arguments (e.g., `--db-path` or positional DB path args).
   - Remove or deprecate any references in help texts or docs for DB path CLI args.

3. **Always fresh read from environment:**

   - Do not cache or store the DB path anywhere in the codebase; always access it from `os.environ` at connection time.

4. **Do not pre-validate SQLite files:**

   - Only check that the environment variable is present and non-empty. Do not check file existence or SQLite format. Allow SQLite to raise errors as appropriate.

5. **Logging & error handling:**

   - Follow the codebase’s current logging and error pattern for both CLI and API entry points.
   - Use clear, actionable errors. Example:
     ```
     [ERROR] METROPOLE_DB_PATH not set. Please set the environment variable to the absolute path of your SQLite DB file.
     ```

6. **Testing/CI flexibility:**

   - In test and CI code, it’s acceptable to set `METROPOLE_DB_PATH` to a test or temp file before running tests.
   - Do **not** introduce any fallback to a default test DB—fail if unset.

7. **Documentation:**

   - Update CLI help, README, and any deployment docs to clearly state that `METROPOLE_DB_PATH` is mandatory, must be an absolute path, and is the _only_ way to specify the DB location.

8. **Verify Docker setup (out of scope for code, but required for completion):**

   - Make sure Docker/compose configs and deployment scripts always set and mount `METROPOLE_DB_PATH` correctly.

9. **Code cleanup:**
   - Remove any dead code, legacy config options, or TODOs related to DB path selection.
   - Add or update docstrings/comments as needed to clarify that `METROPOLE_DB_PATH` is the only supported mechanism.

---

## Acceptance Criteria

- All DB access code fails if `METROPOLE_DB_PATH` is unset.
- No CLI or API code uses a hardcoded or default DB path.
- No CLI argument or config allows specifying the DB file.
- All connection points fetch the DB path from `os.environ` at time of connection.
- Existing logging/error style is followed.
- Tests can set the env var as needed but must not rely on fallbacks.
- Docs updated for the new behavior.

---

**Do not start implementation until you have reviewed the design doc. When finished, run/expand the test suite and verify the application runs in Docker using the new pattern. Clean up any dead code.**
