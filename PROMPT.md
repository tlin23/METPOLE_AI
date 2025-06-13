# Step-by-Step Project Blueprint: DESIGN.md

## PHASE 1: Foundation & Infrastructure

### 1.1. Repository Structure & Base Services

- [ ] Confirm project directory structure for `backend`, `frontend`, `nginx`, and Docker.
- [ ] Set up and test Docker Compose with all four services: `frontend`, `backend`, `sqlite-web`, `nginx` (use placeholder apps as needed).

### 1.2. Nginx Reverse Proxy Baseline

- [ ] Write an initial Nginx config that:

  - Proxies `/api/*` to FastAPI (backend)
  - Proxies `/db/*` to sqlite-web (DB admin)
  - (Optional for prod) Serves static frontend or proxies to frontend dev server

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

- [ ] Single Nginx entrypoint (only Nginx port exposed).
- [ ] Persistent DB volume.
- [ ] Fly.io or Docker Compose ready to deploy.

---

# From Blueprint to Implementation: Iterative Chunks

## Chunk Breakdown (Each builds on the last)

### Chunk 1: Docker + Directory Scaffold

- Initialize directories and Docker Compose with placeholder services.

### Chunk 2: Nginx Reverse Proxy Routing

- Write basic Nginx config for proxying to backend, frontend, and sqlite-web.

### Chunk 3: Frontend Google OAuth

- Implement Google login flow in React, persist ID token, add auth header to fetch.

### Chunk 4: Backend Auth Middleware

- Add FastAPI token validation, admin email check, protect endpoints.

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

- Create `backend/`, `frontend/`, `nginx/` directories
- Write initial `docker-compose.yml` with dummy images for each service
- Add persistent volume mapping for the database

## Chunk 2: Nginx Reverse Proxy Routing

- Write `nginx.conf.template` that proxies `/api/*` to backend:8000, `/db/*` to sqlite-web:8081
- Add config to pass proxy headers
- Update Docker Compose to build Nginx with correct config

## Chunk 3: Frontend Google OAuth

- Set up React Google OAuth library
- On login, store Google ID token
- Add `Authorization: Bearer ...` to all API calls
- Handle logout and expired tokens

## Chunk 4: Backend Auth Middleware

- Implement FastAPI middleware that checks for `Authorization: Bearer ...`
- Validate token with Google API, extract user/email
- Check admin status from env
- Protect `/api/admin/*` endpoints

## Chunk 5: Secure SQLite-web

- Add HTTP basic auth for `/db/*` route in Nginx (use `.htpasswd`)
- Reload Nginx config and verify manual access is blocked for unauthorized users

## Chunk 6: API Endpoints & Models

- Implement `/api/health` route (public)
- Implement `/api/ask` route (protected, calls dummy logic)
- Implement `/api/feedback` (protected, create/read)
- Implement `/api/admin/me` (admin only)
- Create Pydantic models for requests/responses

## Chunk 7: Database Models & Schema

- Write initial SQLite schema (users, sessions, questions, answers, feedback)
- Implement Python code for DB CRUD for each model

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

```
Create the following directories in the project root: backend/, frontend/, nginx/.
Add a docker-compose.yml that defines four services:
  - backend (FastAPI, expose 8000)
  - frontend (Vite/React, expose 3000)
  - sqlite-web (expose 8081)
  - nginx (reverse proxy, expose 8080)
Mount a persistent volume for SQLite DB at /data/app.db for sqlite-web and backend.
Use placeholder Dockerfiles/images for now.
```

---

## Prompt 2: Nginx Reverse Proxy Baseline

```
Write an nginx.conf.template that:
  - Proxies /api/* to backend:8000
  - Proxies /db/* to sqlite-web:8081
  - Passes Host and X-Forwarded-Proto headers
Update docker-compose.yml to build Nginx using this config.
Test with curl to verify routing works for all endpoints.
```

---

## Prompt 3: Google OAuth Login (Frontend)

```
Set up Google OAuth in the React frontend:
  - Implement login/logout button using Google Identity Services
  - On success, save ID token in memory/state
  - Attach Authorization: Bearer <ID token> to all fetch/XHR requests to /api/*
  - Handle token expiration, prompt user to re-login if 401/403 returned
```

---

## Prompt 4: Backend Auth Middleware

```
In FastAPI backend, implement a dependency/middleware that:
  - Extracts Authorization: Bearer <Google ID token> from incoming requests
  - Verifies the token with Google (use google.oauth2)
  - Extracts user info and email; checks if user is admin via ADMIN_EMAILS env var
  - Deny access to /api/admin/* if not admin
  - Add logging for failed auth attempts
```

---

## Prompt 5: Secure SQLite-web

```
Configure nginx.conf.template so that /db/* is protected with HTTP basic auth using .htpasswd.
Update docker-compose.yml to mount .htpasswd into nginx container.
Test manual access: unauthorized users cannot load /db, authorized users can.
```

---

## Prompt 6: API Endpoints & Models

```
Implement the following in FastAPI:
  - /api/health (public)
  - /api/ask (protected, returns dummy answer)
  - /api/feedback (protected, stores feedback)
  - /api/admin/me (admin only, returns email/is_admin)
Define all request/response models using Pydantic.
Write basic unit tests for each endpoint.
```

---

## Prompt 7: Database Models & Schema

```
Write the SQLite schema for users, questions, answers, feedback tables.
Implement Python model code to CRUD each table.
Add migration/upgrade scripts.
Write unit tests for each DB model method.
```

---

## Prompt 8: End-to-End Happy Path

```
Connect all parts:
  - User logs in, frontend fetches /api/ask and displays response
  - User submits feedback, see confirmation
  - Admin logs in, fetches /api/admin/me, verifies admin access
Write integration test for login-ask-feedback-admin roundtrip.
```

---

## Prompt 9: Error Handling & Logging

```
Frontend: show clear error message for 401/403 or token expiry; auto-redirect to login.
Backend: log all failed auth attempts, return JSON { success: false, message, ... }
Nginx: configure 401/403 for /db if auth fails.
Test all error flows with unit/integration tests.
```

---

## Prompt 10: Testing & CI

```
Add pytest-based unit tests for backend logic and API routes.
Write integration test for login → ask → feedback flow.
Add security test for admin RBAC and invalid tokens.
Set up GitHub Actions or similar for CI: lint, test, Docker build check.
```

---

## Prompt 11: Production Readiness

```
Lock down CORS in backend for prod.
Enable HTTPS in nginx/fly.io config.
Move all secrets and config to environment variables.
Document prod vs dev configuration, and how to rotate secrets.
```
