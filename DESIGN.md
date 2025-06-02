# Design Doc: Docker-Proof Database Path Handling for CLI & API

## Background & Motivation

Current DB path handling across CLI tools, admin scripts, and API endpoints is inconsistent. Some tools accept a DB file path as a CLI argument, others use hardcoded defaults, and some (like `dump_db`) work because the correct path is explicitly given. This inconsistency leads to issues, especially in Docker/containerized environments, where the app may point to the wrong SQLite file or create a fresh DB.

**Goal:**
Unify and standardize all database access in CLI and API code to reliably use a single, Docker-configured path, eliminating ambiguity and risk of silent failures or empty databases.

---

## Design Requirements

### 1. Source of Truth

- All DB access must use a single environment variable:
  `METROPOLE_DB_PATH`

### 2. Absolute Path

- The environment variable **must always contain an absolute path** (e.g., `/data/app.db`) inside the container.
- Docker/compose configs and deployment scripts must ensure the volume is mounted at this path.

### 3. Fail Fast

- If `METROPOLE_DB_PATH` is not set, all entry points (CLI, API, admin scripts) must:

  - Fail immediately,
  - Emit a clear, prominent error via logging and/or stderr,
  - Exit with a non-zero code (for CLI) or return an error code (for API).

### 4. Always Read Directly From Environment

- All DB connections must **read the env var each time** they connect (no module-level or config-file caching).
- No default/fallback path allowed.

### 5. No CLI Overrides

- All CLI tools and scripts must **remove support for specifying the DB path as a command-line argument**.
  The environment variable is the only accepted way to specify the DB location.

### 6. Logging and Error Style

- Follow the project’s existing logging/error handling patterns (e.g., via the logger for API, stderr for CLI).
- Error message for missing env var should be clear and actionable.

### 7. SQLite Error Handling

- Do not pre-validate that the file exists or is a valid DB;
  allow SQLite to throw its native errors.

### 8. Test/CI Environment Flexibility

- Automated tests and CI jobs **may set **\`\`** internally or use test-specific values**.
- No requirement for a “real” DB file in tests unless the test is designed for that.

---

## Implementation Scope

- **Affected code:**

  - All CLI tools (admin.py, dump_db, etc.)
  - All FastAPI or Flask route handlers and app/database initialization code
  - All helper or model modules that connect to SQLite directly

- **Not affected:**

  - Anything not touching the database
  - Dockerfile and compose configs (handled separately)

---

## Implementation Steps

1. **Refactor all DB access code:**

   - Remove any default DB file paths or CLI argument parsing for DB location.
   - At every DB connect, read `os.environ['METROPOLE_DB_PATH']`.
   - If the env var is missing, log and exit/fail as per the entry point’s style.

2. **Update documentation:**

   - CLI help, README, and deployment docs must state that `METROPOLE_DB_PATH` is mandatory and must be an absolute path.

3. **Tests:**

   - Refactor any test helpers to always set `METROPOLE_DB_PATH` for test DBs.
   - Do not break existing test functionality.

4. **Verify Docker setup:**

   - Ensure that Docker/compose templates and any deploy scripts set and mount `METROPOLE_DB_PATH` as an absolute path.

---

## Error Message Example

When missing:

```
[ERROR] METROPOLE_DB_PATH not set. Please set the environment variable to the absolute path of your SQLite DB file.
```

---

## Risks & Trade-offs

- **Efficiency:** Reading the env var every time is a micro-optimization loss, but maximizes clarity and prevents subtle bugs.
- **Strictness:** CLI users must adapt to the env-var-only approach, but this prevents accidental divergence across environments.
- **Containerization:** Absolute paths remove ambiguity, but require careful Docker volume setup (which is good practice anyway).

---

## Future Considerations

- If future migration to a different DB system (e.g., Postgres), this pattern makes switching the connection string seamless.
- If supporting multi-tenant or multi-DB use, revisit the “always from env” rule.

---

## Acceptance Criteria

- No code in the codebase can access the DB without the env variable set.
- No CLI or API uses a hardcoded or default DB path.
- All DB connections work inside Docker, provided `METROPOLE_DB_PATH` is set and mounted.
- Tests still run by explicitly setting the env var per test.

---

**Ready for implementation.**
