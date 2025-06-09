# Developer Specification: Admin SQL Query UI using sqlite-web

---

## 1. Overview

Provide a web-based SQL query and data inspection UI for the app's SQLite database (`app.db`).
This tool should be accessible only to admin users, support both free-form SQL and predefined queries, and allow CSV/JSON export—all while enforcing read-only access.

---

## 2. Requirements

### 2.1 Functional

- **Web UI for querying app.db**, exposed at `/admin/db-query` on the main app domain.
- **Free-form SQL**: Allow any `SELECT` query.
- **Predefined queries & entity browsers** for Users, Sessions, Questions, Answers, Feedback.
- **Full-text/content search** for any table.
- **Paginated results** and filters for predefined queries.
- **Export/Download**: Results can be downloaded as CSV/JSON.
- **Read-only**: Absolutely no insert/update/delete or schema changes.
- **Result size limit**: Maximum 500 rows returned per query.
- **Authentication**: Only allow Google OAuth authenticated users.

  - Restrict access to specific Google Workspace/allowed email list via oauth2-proxy.

- **Authorization**:
  - Access is controlled via oauth2-proxy's allowed email list.
  - No additional backend checks needed.

### 2.2 Non-Functional

- **Performance**: Query UI must not block or degrade app performance; long-running queries should timeout or be paginated.
- **Security**:

  - Never expose the database file publicly.
  - No write access, ever.
  - All admin traffic over HTTPS.
  - Ensure session/cookie isolation (since same domain).

- **Simplicity**: Default sqlite-web UI is sufficient—no need for rebranding.

---

## 3. Architecture Choices

### 3.1 Tool Selection

- Use [sqlite-web](https://github.com/coleifer/sqlite-web) as the query UI.

  - Launched in `--read-only` mode.
  - Pointed at the same `app.db` used by the backend.

### 3.2 Deployment

- Run sqlite-web as a separate process (e.g., Docker container or systemd service).
- Expose on `localhost` or an internal port (e.g., `127.0.0.1:8080`).

### 3.3 Integration

- Set up a **reverse proxy** (Nginx, Caddy, or via FastAPI) on `/admin/db-query` to route traffic to sqlite-web.
  - Use [oauth2-proxy](https://oauth2-proxy.github.io/oauth2-proxy/) for Google OAuth, configured for allowed emails.
  - No additional backend authorization checks needed.

### 3.4 Frontend

- Add a new "DB Query" link to the admin menu/sidebar in your app frontend (only visible to admins).
- Clicking the link opens `/admin/db-query` (either as a new tab or embedded iframe).

---

## 4. Data Handling Details

- **Read-only mode**: sqlite-web should be started with `--read-only`.
- **Row limit**: sqlite-web's max results per page set to 500 (either via config/flag, or documented for admin users).
- **Exports**: sqlite-web supports CSV, JSON, XLSX for results; no data ever leaves unless explicitly exported by an admin.
- **Session handling**: Only authenticated (and if possible, authorized) sessions can see or interact with sqlite-web.
- **No sensitive data**: All columns are deemed safe for admin viewing.

---

## 5. Error Handling Strategies

- **Invalid queries**: sqlite-web will display SQL errors in the UI. No stack traces or backend logs are exposed.
- **Unauthorized access**:

  - If unauthenticated: redirect to Google login.
  - If authenticated but not admin (if strict mode): display "Access Denied".

- **Server errors (e.g., db locked, connection lost)**: Standard sqlite-web error page, with clear message for the admin.
- **Over-limit queries**: If more than 500 rows requested, results should be truncated and a notice shown (sqlite-web default).

---

## 6. Testing Plan

### 6.1 Manual Testing

- **Authentication**

  - Unauthenticated users are redirected to login.
  - Authenticated non-admins cannot access (if in strict mode).
  - Admins can access and use all features.

- **Query Execution**

  - Free-form `SELECT` queries work as expected.
  - INSERT/UPDATE/DELETE and PRAGMA statements are blocked.
  - Predefined queries (via sqlite-web UI) list entities as expected.

- **Result Limit**

  - Large SELECTs are truncated at 500 rows, with clear messaging.

- **Export**

  - Download results as CSV and JSON.

- **Error Handling**

  - SQL errors are handled gracefully in the UI.
  - Database unavailable errors are shown with a clear message.

### 6.2 Security Testing

- Attempt to bypass auth by direct access to sqlite-web port (should be blocked by firewall).
- Attempt cross-origin access—verify CORS protections.
- Attempt "write" queries—confirm failure.
- Verify no sensitive session tokens or cookies are leaked between main app and sqlite-web.

### 6.3 Automated Testing

- Integration test for reverse proxy:

  - Only allow traffic with a valid Google-authenticated session.
  - Optionally: mock or test the `is_admin` DB check.

- (Optional) E2E test with a headless browser to verify end-to-end flow.

---

## 7. Operations

- **Startup**:

  - `sqlite-web --read-only --host 127.0.0.1 --port 8080 /path/to/app.db`

- **Reverse Proxy**:

  - Nginx (or FastAPI) proxies `/admin/db-query` to `localhost:8080`.

- **Oauth2-proxy**:

  - Handles Google sign-in, email allowlist matches your admin users.

- **App Documentation**:

  - Provide instructions for admins, including usage notes and result limits.

---

## 8. References

- [sqlite-web GitHub](https://github.com/coleifer/sqlite-web)
- [oauth2-proxy Documentation](https://oauth2-proxy.github.io/oauth2-proxy/)

---

**Hand this spec directly to your developer for immediate implementation.**
