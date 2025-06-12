# Metropole Developer Specification

## 1. Summary & Goals

Build a production-grade, secure, and maintainable web application with:

- FastAPI backend (API, logic, DB ops)
- React/Vite frontend (OAuth, UI)
- SQLite-web for DB admin (secured)
- Nginx as reverse proxy for all components
- Google OAuth (handled in frontend)
- Stateless backend, token-based authentication

---

## 2. System Architecture

```
           +-------------+
           |   Browser   |
           +------+------+         +-------------------+
                  |                 |    Google OAuth   |
         (ID token via frontend)    +---------+---------+
                  |                           |
           +------v------+          +---------v---------+
           |   Frontend  |          |  Google Identity  |
           +------^------+          +-------------------+
                  |
       +----------+----------+
       |  Nginx Reverse Proxy|
       +----------+----------+
          |             |
   /api/* |             | /db/*
       +--v--+      +---v------+
       |FastAPI|     |SQLite-web|
       +------+      +----------+
```

**Key principles:**

- Frontend is the OAuth client; backend is stateless and only validates tokens.
- All traffic routes through Nginx for unified entry and easy deployment.
- SQLite-web is secured (IP restriction or HTTP basic auth).

---

## 3. Component Responsibilities

### Frontend

- Handles Google OAuth (login/logout, token management).
- On API requests: attaches `Authorization: Bearer <Google ID token>`.
- Handles token refresh, logout UX, error reporting.

### Backend (FastAPI)

- Expects `Authorization: Bearer <Google ID token>` on protected endpoints.
- Verifies tokens with Google, extracts user info, determines admin status.
- Provides `/api/*` endpoints, including:
  - `/api/health`
  - `/api/ask`
  - `/api/admin/*` (admin-restricted)
  - `/api/feedback` etc.
- Does NOT manage OAuth sessions, cookies, or state.
- RBAC (admin/regular user) enforced by email matching.

### Nginx

- Forwards `/api/*` to FastAPI (port 8000)
- Forwards `/db/*` to SQLite-web (port 8081)
- Handles SSL/TLS (if needed), and adds required proxy headers.
- Restricts `/db` via IP allowlist or HTTP basic auth (not exposed publicly).

### SQLite-web

- Exposed only via `/db/*` (Nginx controls access)
- Database volume is persistent and backed up.

---

## 4. Data Handling

- All sensitive operations require a valid Google ID token.
- User identity comes from the verified token (`sub`, `email`).
- Admin access determined by `email in ADMIN_EMAILS`.
- Database (SQLite) is stored in a persistent Docker/Fly volume.
- No session state; all requests validated individually.
- User data (e.g. questions, answers) stored in SQLite.
- DB migrations and schema changes are managed with scripts.

---

## 5. Error Handling

- **Frontend:**

  - Handles OAuth errors (token invalid, expired, consent revoked) and prompts user to re-login.
  - Handles HTTP 401/403 by redirecting to login.
  - Gracefully degrades if token is missing or expired.

- **Backend:**

  - Returns HTTP 401 for missing/invalid tokens.
  - Returns HTTP 403 for unauthorized/admin endpoints.
  - Returns HTTP 429 with clear error messages for quota/rate limits.
  - All errors return clear JSON: `{ "success": false, "message": "...", ... }`
  - Logs all failed auth attempts and critical errors.

- **Nginx:**
  - Returns 401/403 for protected routes if auth fails (if basic auth used).
  - Returns 502/504 for backend or SQLite-web errors.

---

## 6. Security

- Google ID token validated **on every API request** (backend never trusts the client alone).
- SQLite-web restricted by IP (only localhost, or your VPN), or by HTTP basic auth at Nginx (if accessed remotely).
- No sensitive data in URL parameters.
- HTTPS enforced in production.
- All service secrets (Google client, admin emails, DB path) stored as environment variables, not hardcoded.
- CORS configured strictly for production domains.

---

## 7. Deployment

- Use **single Nginx reverse proxy** in Docker Compose for local dev and Fly.io for prod.
- Only expose Nginx’s port (8080 or 443/80) to the outside world.
- Docker Compose example: backend, frontend, sqlite-web, nginx.
- Fly.io: only port 8080 open in `fly.toml`.
- Database volume mounted at `/data/app.db` for persistence.

---

## 8. SQLite-web Admin Security Options

- **Option A (Recommended):** Only expose `/db` via `flyctl proxy` (internal-only, never public).
- **Option B:** Add `auth_basic` in Nginx for `/db`, with `.htpasswd`.
- **Option C:** (Advanced) Proxy `/db` via FastAPI and require Google ID token.

---

## 9. Testing Plan

- **Unit tests:** All core backend functions, including token validation and all API endpoints.
- **Integration tests:** End-to-end flows for login, asking questions, admin actions.
- **Security tests:** Attempt API calls with invalid/expired tokens, no tokens, regular users to admin endpoints, etc.
- **Manual tests:** Verify SQLite-web is restricted, both locally and in prod.
- **Load tests:** Simulate high load on backend and DB to ensure stability.
- **CI pipeline:** Linting, unit + integration tests, Docker build verification.

---

## 10. Explicit Requirements

- All API requests must send `Authorization: Bearer <Google ID token>`.
- Backend must verify the token with Google every request.
- Admin email list is controlled by the `ADMIN_EMAILS` environment variable.
- SQLite DB is always mounted on persistent storage.
- SQLite-web must **not** be publicly accessible without protection.
- Nginx must pass `X-Forwarded-Proto`, `Host`, and all relevant proxy headers.
- All configuration must be possible via environment variables for prod/dev parity.

---

## 11. References

- [FastAPI docs](https://fastapi.tiangolo.com/)
- [Google Identity/OAuth docs](https://developers.google.com/identity)
- [SQLite-web](https://github.com/coleifer/sqlite-web)
- [Nginx docs](https://nginx.org/en/docs/)
- [Fly.io docs](https://fly.io/docs/)

---

**End of spec**
