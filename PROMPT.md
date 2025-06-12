# Step-by-Step Project Blueprint: DESIGN.md

> **NOTE:** The frontend is developed and deployed separately (not behind Nginx), e.g., to Vercel/Netlify. Nginx only proxies backend and db endpoints.

## PHASE 1: Foundation & Infrastructure

### 1.1. Repository Structure & Base Services

- [ ] Confirm project directory structure for `backend`, `frontend`, `nginx`, and Docker.
- [ ] Set up and test Docker Compose with these services: `backend`, `sqlite-web`, `nginx` (use placeholder apps as needed).
- [ ] The frontend is developed and deployed separately (e.g., Vercel/Netlify), not served by Nginx.

### 1.2. Nginx Reverse Proxy Baseline

- [ ] Write an initial Nginx config that:
  - Proxies `/api/*` to FastAPI (backend)
  - Proxies `/db/*` to sqlite-web (DB admin)
- [ ] Nginx does **not** serve or proxy the frontend. The frontend is expected to be deployed on its own domain.
- [ ] Enable required proxy headers (`Host`, `X-Forwarded-Proto`, etc.)

### 1.3. Environment Management

- [ ] Set up `.env` files for dev and prod; all secrets and config via env vars.
- [ ] Implement Docker volume for persistent SQLite storage.
- [ ] Document all required env vars (Google OAuth, DB path, admin email, etc.).

---

## PHASE 2: Authentication & Security

### 2.1. Google OAuth Flow (Frontend)

- [ ] Implement Google OAuth login/logout in React frontend.
- [ ] On success: save ID token, attach as `Authorization: Bearer ...` on all API requests.
- [ ] Handle token refresh and expired/invalid tokens (with re-login UX).

### 2.2. Backend Auth Middleware

- [ ] FastAPI expects `Authorization: Bearer <Google ID token>` on protected routes.
- [ ] Middleware verifies token (via Google) and extracts user info, admin status.
- [ ] All endpoints (except `/api/health`) require auth.

### 2.3. Admin RBAC & Env

- [ ] Backend checks admin status via `email in ADMIN_EMAILS` (from env).
- [ ] Protect `/api/admin/*` endpoints, return 403 if not admin.

### 2.4. SQLite-web Security

- [ ] Restrict `/db/*` in Nginx via either:
  - Internal-only access (Option A: preferred)
  - HTTP basic auth (Option B: fallback)
- [ ] Validate restriction with manual test.

---

## PHASE 3: Core API & Data Flow

### 3.1. FastAPI API Routes

- [ ] Implement `/api/health` (public), `/api/ask`, `/api/feedback`, `/api/admin/*`.
- [ ] All data models (Pydantic) match OpenAPI and business logic.
- [ ] RBAC and error handling per DESIGN.md.

### 3.2. SQLite Models & Persistence

- [ ] Implement DB schema (users, questions, answers, feedback, etc.).
- [ ] All DB reads/writes via secure, transactional code.
- [ ] Scripts for migrations/schema updates.

### 3.3. Connect All Components

- [ ] End-to-end flow: user logs in, asks a question, receives response, can give feedback, admin can view analytics, etc.

---

## PHASE 4: Error Handling, Logging, and Testing

### 4.1. Error Handling

- [ ] Frontend: handles OAuth errors, API errors, 401/403, rate limits, etc.
- [ ] Backend: returns clear JSON errors, logs all critical errors, quota/rate limit, etc.
- [ ] Nginx: configured to block/401 unauthorized `/db`, return 502/504 on backend/DB failures.

### 4.2. Testing

- [ ] Unit tests for all core backend functions (token validation, API logic).
- [ ] Integration tests: E2E login, ask, feedback, admin flows.
- [ ] Security tests: invalid/expired tokens, regular user blocks, admin-only access.
- [ ] Manual tests: DB admin locked down, production traffic is secure.
- [ ] Load tests (optional): backend and DB stress.

### 4.3. CI Pipeline

- [ ] Set up CI: lint, unit + integration tests, Docker build check.

---

## PHASE 5: Production Readiness

### 5.1. CORS & HTTPS

- [ ] Strict CORS on FastAPI (production domains only).
- [ ] HTTPS (via Fly.io or Nginx) in production.

### 5.2. Secrets & Environment Parity

- [ ] All configuration via environment variables.
- [ ] Document and test prod/dev switching.

### 5.3. Deployment

- [ ] Only expose Nginx’s port (e.g., 8080 or 443/80) to the outside world.
- [ ] The backend and sqlite-web are only accessible through Nginx reverse proxy.
- [ ] The frontend is deployed separately and communicates with backend and db endpoints via the public Nginx URL.
- [ ] Persistent DB volume.
- [ ] Fly.io or Docker Compose ready to deploy.

---

# From Blueprint to Implementation: Iterative Chunks

## Chunk Breakdown (Each builds on the last)

### Chunk 1: Docker + Directory Scaffold

- Initialize directories and Docker Compose with placeholder services: `backend`, `sqlite-web`, `nginx`.
- The frontend is not part of Docker Compose; it is developed and deployed separately.
- Add persistent volume mapping for the database.

### Chunk 2: Nginx Reverse Proxy Routing

- Write `nginx.conf.template` that proxies `/api/*` to backend:8000, `/db/*` to sqlite-web:8081.
- Do **not** proxy or serve the frontend in Nginx.
- Add config to pass proxy headers.
- Update Docker Compose to build Nginx with correct config.

### Chunk 3: Frontend Google OAuth

- Set up React Google OAuth library (in separately deployed frontend).
- On login, store Google ID token.
- Add `Authorization: Bearer ...` to all API calls to `/api/*`.
- Handle logout and expired tokens.

### Chunk 4: Backend Auth Middleware

- Implement FastAPI middleware that checks for `Authorization: Bearer ...`.
- Validate token with Google API, extract user/email.
- Check admin status from env.
- Protect `/api/admin/*` endpoints.

### Chunk 5: Secure SQLite-web

- Add HTTP basic auth (or IP allowlist) to `/db/*` route in Nginx, test restriction.

### Chunk 6: API Endpoints & Data Models

- Build `/api/health`, `/api/ask`, `/api/feedback`, `/api/admin/*` routes and Pydantic models.

### Chunk 7: Database Models & Schema

- Define SQLite schema, implement model code for users, questions, answers, feedback.

### Chunk 8: End-to-End Happy Path

- Connect all: login → ask question → store answer → give feedback → admin query.

### Chunk 9: Error Handling & Logging

- Implement clear errors, frontend error UX, backend logging.

### Chunk 10: Testing & CI

- Add unit, integration, security, and manual tests. Set up CI for checks and Docker build.

### Chunk 11: Production Prep

- Harden CORS, secrets, HTTPS, and ensure all config/envs are production-ready.

---

# Granular Step Breakdown (Smallest Steps, Ready for LLM Prompts)

For each chunk, here is how to break into “prompt-sized” steps:

## Chunk 1: Docker + Directory Scaffold

- Create `backend/`, `frontend/`, `nginx/` directories.
- Write initial `docker-compose.yml` with three services: `backend` (FastAPI, expose 8000), `sqlite-web` (expose 8081), `nginx` (reverse proxy, expose 8080).
- Mount a persistent volume for SQLite DB at `/data/app.db` for sqlite-web and backend.
- Use placeholder Dockerfiles/images for now.
- **Note:** The frontend is developed and deployed separately (not in Compose).

## Chunk 2: Nginx Reverse Proxy Routing

- Write `nginx.conf.template` that:
  - Proxies `/api/*` to backend:8000
  - Proxies `/db/*` to sqlite-web:8081
  - Passes Host and X-Forwarded-Proto headers
- Do **not** proxy or serve the frontend in Nginx.
- Update docker-compose.yml to build Nginx using this config.
- Test with curl to verify routing works for all endpoints.

## Chunk 3: Google OAuth Login (Frontend)

- Set up Google OAuth in the React frontend (deployed separately):
  - Implement login/logout button using Google Identity Services
  - On success, save ID token in memory/state
  - Attach Authorization: Bearer <ID token> to all fetch/XHR requests to /api/\*
  - Handle token expiration, prompt user to re-login if 401/403 returned

## Chunk 4: Backend Auth Middleware

- In FastAPI backend, implement a dependency/middleware that:
  - Extracts Authorization: Bearer <Google ID token> from incoming requests
  - Verifies the token with Google (use google.oauth2)
  - Extracts user info and email; checks if user is admin via ADMIN_EMAILS env var
  - Deny access to /api/admin/\* if not admin
  - Add logging for failed auth attempts

## Chunk 5: Secure SQLite-web

- Configure nginx.conf.template so that /db/\* is protected with HTTP basic auth using .htpasswd, or use IP restriction.
- Update docker-compose.yml to mount .htpasswd into nginx container if using basic auth.
- Test manual access: unauthorized users cannot load /db, authorized users can.

## Chunk 6: API Endpoints & Models

- Implement the following in FastAPI:
  - /api/health (public)
  - /api/ask (protected, returns dummy answer)
  - /api/feedback (protected, stores feedback)
  - /api/admin/me (admin only, returns email/is_admin)
- Define all request/response models using Pydantic.
- Write basic unit tests for each endpoint.

## Chunk 7: Database Models & Schema

- Write the SQLite schema for users, questions, answers, feedback tables.
- Implement Python model code to CRUD each table.
- Add migration/upgrade scripts.
- Write unit tests for each DB model method.

## Chunk 8: End-to-End Happy Path

- In frontend, login and send `ask` request, display answer
- Submit feedback, admin verifies in `/api/admin` endpoint

## Chunk 9: Error Handling & Logging

- In frontend, show clear error for 401/403, prompt re-login
- In backend, log failed auth attempts, return structured error JSON
- In Nginx, configure 401/403 for `/db/*`

## Chunk 10: Testing & CI

- Write basic pytest unit tests for backend models and API
- Add integration test for login → ask → feedback flow
- Add security tests (invalid token, non-admin to admin route)
- Configure GitHub Actions for lint/test/build

## Chunk 11: Production Prep

- Harden CORS for prod domains
- Enforce HTTPS in Nginx/fly.toml
- Move all secrets to env vars
- Document prod/dev configuration

---

# Cursor/LLM-Ready Prompt Series

Below are prompts you can feed an LLM for incremental, test-driven implementation. (Use one at a time per chunk, check in working code before proceeding.)

---

## Prompt 1: Scaffold Docker + Directory
