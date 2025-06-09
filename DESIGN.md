# OAuth Flexible Routing & Config Design Specification

## Overview

This document specifies a robust, environment-agnostic OAuth routing and configuration strategy for your full-stack application. The design ensures local development, Docker Compose, and cloud deployment (Fly.io) use the same code and routing logic, with all differences driven by environment variables or config files. This guarantees fast iteration, reliable local testing, and seamless deployment.

---

## 1. Objectives

- **Unify OAuth configuration across all environments** (local, Docker Compose, cloud) via environment variables or config files.
- **Standardize redirect URIs** such that local and Docker use the same callback paths whenever possible.
- **Minimize code branching**: All differences handled in configuration, not code logic.
- **Enable rapid local development** with a stack that mirrors Docker/cloud as closely as possible.
- **Ensure confidence in cloud deployment** by having identical auth logic tested locally and in Docker Compose.

---

## 2. Architecture Choices

### 2.1 Stack

- **Frontend** (React or similar)
- **Backend** (FastAPI or similar)
- **OAuth2 Proxy** (e.g., for Google sign-in)
- **Nginx** (reverse proxy & SPA fallback)
- **Docker Compose** for integrated local/cloud stack

### 2.2 Routing & Network

- All external traffic (local, Docker, or cloud) enters through Nginx (port 3000).
- Nginx proxies requests to frontend (React), backend (API), and OAuth2 Proxy as appropriate.
- All OAuth redirects and callbacks route through Nginx at predictable endpoints (e.g., `/oauth2/callback`).
- Internal service names are never exposed to the browser/client—only Nginx-facing ports are exposed (mapped to localhost or cloud domain).

---

## 3. Environment & Config Management

### 3.1 Environment Variables (Sample Keys)

| Variable             | Purpose                            | Example (Local/Docker)                                                         | Example (Cloud/Fly.io)                                                         |
| -------------------- | ---------------------------------- | ------------------------------------------------------------------------------ | ------------------------------------------------------------------------------ |
| OAUTH_CLIENT_ID      | Google OAuth client ID             | abc123-local.apps.googleusercontent.com                                        | xyz456-flyio.apps.googleusercontent.com                                        |
| OAUTH_CLIENT_SECRET  | Google OAuth client secret         | \*\*\*                                                                         | \*\*\*                                                                         |
| OAUTH_REDIRECT_URI   | OAuth callback URI                 | [http://localhost:3000/oauth2/callback](http://localhost:3000/oauth2/callback) | [https://myapp.fly.dev/oauth2/callback](https://myapp.fly.dev/oauth2/callback) |
| BASE_URL             | App public base URL                | [http://localhost:3000](http://localhost:3000)                                 | [https://myapp.fly.dev](https://myapp.fly.dev)                                 |
| ALLOWED_CORS_ORIGINS | Comma-separated allowed origins    | [http://localhost:3000](http://localhost:3000)                                 | [https://myapp.fly.dev](https://myapp.fly.dev)                                 |
| FRONTEND_URL         | Used in backend for CORS/callbacks | [http://localhost:3000](http://localhost:3000)                                 | [https://myapp.fly.dev](https://myapp.fly.dev)                                 |
| BACKEND_URL          | API base URL                       | [http://localhost:8000](http://localhost:8000)                                 | [https://myapp.fly.dev/api](https://myapp.fly.dev/api)                         |
| OAUTH2_PROXY_URL     | OAuth2 Proxy URL                   | [http://localhost:4180](http://localhost:4180)                                 | [http://oauth2-proxy:4180](http://oauth2-proxy:4180)                           |
| ...                  |                                    |                                                                                |                                                                                |

- Each environment (.env.local, .env.docker, .env.flyio) sets these values appropriately.
- Use Docker Compose `env_file` to load the right env file for each environment.

### 3.2 Nginx & OAuth2 Proxy Config

- Template Nginx and OAuth2 Proxy config files to use environment variables.
- Optionally, use [envsubst](https://github.com/a8m/envsubst) for variable interpolation if templating is needed.
- Service hostnames in Nginx always point to Docker service names in Compose, and to localhost when running locally (with ports matching frontend/backend/OAuth2 proxy ports).

### 3.3 Google OAuth Redirect URIs

- Register all possible redirect URIs with Google:

  - `http://localhost:3000/oauth2/callback` (local/dev, Docker Compose)
  - `https://myapp.fly.dev/oauth2/callback` (cloud)

- Use the _same_ callback URI in both local and Docker when possible (always use `localhost:3000` as the entrypoint in both scenarios).
- Minimize the number of redirects for clarity.

---

## 4. Data Handling Details

- OAuth tokens and user session info are passed securely via HTTP cookies (with `Secure` flag in prod/cloud).
- Callback endpoints are only exposed via Nginx (not direct container ports), reducing attack surface.
- CORS policies are set from environment variables, with production using strict settings and local allowing localhost origins.
- All sensitive data is never committed—only stored in local `.env` files or cloud secret managers.

---

## 5. Error Handling Strategies

- All config loads have default fallbacks and raise meaningful errors if a required variable is missing (fail fast, log clearly).
- Nginx returns 502/503 for misrouted traffic; backend logs and alerts on OAuth callback errors.
- Frontend and backend handle auth errors gracefully, prompting users to re-authenticate or report config errors.
- On bad OAuth redirect/callback, log the incoming request, error, and environment config for easy debugging.
- In dev/local, verbose error logs are enabled; in prod/cloud, sensitive error info is only logged (not shown to users).

---

## 6. Testing Plan

### 6.1 Manual Testing Matrix

| Test Scenario                       | Local (`make`/npm) | Docker Compose | Fly.io |
| ----------------------------------- | :----------------: | :------------: | :----: |
| Login flow (Google)                 |         ✔️         |       ✔️       |   ✔️   |
| Auth callback redirect              |         ✔️         |       ✔️       |   ✔️   |
| Access protected backend API        |         ✔️         |       ✔️       |   ✔️   |
| Session persistence                 |         ✔️         |       ✔️       |   ✔️   |
| CORS/Origin errors                  |         ✔️         |       ✔️       |   ✔️   |
| Nginx proxying to all services      |         ✔️         |       ✔️       |   ✔️   |
| OAuth2 Proxy works as reverse-proxy |         ✔️         |       ✔️       |   ✔️   |

### 6.2 Automated Tests

- Add backend tests for endpoints requiring auth (mock OAuth for fast test runs).
- Add e2e (Cypress/Playwright) tests for login, auth callback, and CORS failure handling.
- Add integration tests for Nginx/OAuth2 Proxy (smoke test in Docker Compose: login and access protected resource).
- Add CI/CD check that `.env.example` is in sync with deployed config keys.

### 6.3 Troubleshooting Checklist

- If OAuth callback fails, verify:

  - The requested redirect URI is present in Google OAuth console
  - The env file matches the current environment
  - The Docker Compose and Nginx configs are using the intended `.env` file
  - All services are running on the expected ports/hostnames

- Use logs from backend, OAuth2 Proxy, and Nginx to isolate routing errors.

---

## 7. Deliverables

- Standardized `.env.example` file listing all required env vars for every environment.
- Updated Nginx and OAuth2 Proxy config templates with env-driven values.
- Readme/quickstart describing how to:

  - Run locally (no Docker, just backend/frontend)
  - Run via Docker Compose
  - Deploy to Fly.io
  - Register/update Google OAuth redirect URIs

- Test suite covering local and Docker Compose login/callback flow.

---

## 8. Implementation Notes

- Use `make` or npm scripts for fast local startup, and `docker-compose` for production-like integration tests.
- Keep service ports and callback paths _identical_ in local and Docker Compose when possible (always use `localhost:3000` for local and Compose, with port mapping if needed).
- Regularly audit and prune unused redirect URIs from Google OAuth console for security and maintainability.
- Document how to rotate OAuth client secrets and update configs in all environments.

---

## 9. References

- [Twelve-Factor App Config Best Practices](https://12factor.net/config)
- [Docker Compose env_file docs](https://docs.docker.com/compose/environment-variables/env-file/)
- [Google OAuth Redirect URIs Guide](https://developers.google.com/identity/protocols/oauth2)
- [OAuth2 Proxy Configuration](https://oauth2-proxy.github.io/oauth2-proxy/docs/configuration/overview/)

---

# END OF SPEC
