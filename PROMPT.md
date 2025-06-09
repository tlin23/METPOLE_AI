# OAuth Config Refactor: Step-by-Step Implementation Blueprint

## Purpose

This blueprint will guide a developer (or codegen LLM) through incrementally refactoring and standardizing OAuth routing and config for local, Docker, and cloud environments. All steps are designed to be testable, atomic, and safe, with a focus on early validation.

---

## High-Level Project Phases

1. **Config Audit & Baseline Tests** DONE
2. **Env Variable Refactor (Code & Infra)**
3. **Nginx & OAuth2 Proxy Env Templating**
4. **Frontend/Backend Config Standardization**
5. **Unified `.env` Management**
6. **Manual & Automated End-to-End Testing**
7. **Documentation & Cleanup**

Each phase is split into small, iterative chunks below.

---

## Phase 1: Config Audit & Baseline Tests

### Step 1.1: Audit Existing OAuth & Routing Config

- Locate all hardcoded OAuth client IDs, secrets, redirect URIs, CORS origins, and URLs in backend, frontend, Nginx, and OAuth2 Proxy configs.
- List every spot where a setting is hardcoded or not set via env/config file.
- Document current redirect URIs registered with Google OAuth.

### Step 1.2: Write Baseline Tests for Auth Flow

- Implement (or expand) integration tests that cover:

  - Login button triggers OAuth flow.
  - OAuth callback endpoint is reachable and returns correct result.
  - API returns correct error for unauthorized access.
  - Nginx and proxy routes behave as expected for protected and unprotected routes.

### Step 1.3: Snapshot Current `.env` and Service Configs

- Save copies of current `.env` files, Nginx config, Docker Compose config, OAuth2 Proxy config for comparison.

---

## Phase 2: Env Variable Refactor (Code & Infra)

### Step 2.1: Replace All Hardcoded Config with Env Vars in Backend

- Refactor backend code to source all sensitive or environment-specific settings from env vars (with sensible defaults for dev, but fail fast for missing prod values).
- Keys: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_REDIRECT_URI`, `FRONTEND_URL`, `BACKEND_URL`, `ALLOWED_CORS_ORIGINS`.

### Step 2.2: Replace All Hardcoded Config with Env Vars in Frontend

- Refactor frontend config to accept base URL, OAuth endpoints, etc, from env or build-time vars (`VITE_*` or similar).

### Step 2.3: Identify All Nginx & OAuth2 Proxy Static Settings

- Document all static hostnames/ports in `nginx.conf` and `oauth2-proxy` configs.

---

## Phase 3: Nginx & OAuth2 Proxy Env Templating

### Step 3.1: Template Nginx Config for Env-driven Routing

- Modify `nginx.conf` to interpolate proxy targets (backend, frontend, oauth2-proxy) using environment variables or Compose `env_file`.
- Use `envsubst` or Docker Compose templating if needed.

### Step 3.2: Template OAuth2 Proxy Config for Env-driven Settings

- Ensure client ID, secret, redirect URIs, and backend/frontend targets are all settable via env.

### Step 3.3: Docker Compose: Pass Env Vars to All Services

- Use Docker Compose `env_file`/`environment` blocks to inject correct variables into backend, frontend, nginx, and oauth2-proxy.
- Confirm that `docker-compose up` and local startup both work with the new pattern.

---

## Phase 4: Frontend/Backend Config Standardization

### Step 4.1: Standardize Callback URIs & Ports

- Ensure all services use the same public callback (e.g., `http://localhost:3000/oauth2/callback`) for both local and Docker Compose, with only the domain/port changing for production/cloud.
- Register all needed callback URIs in the Google OAuth console (local, Docker, cloud).

### Step 4.2: Standardize Service Health & Error Handling

- Add health check endpoints to backend and OAuth2 Proxy.
- Make sure bad callback/cors errors are logged and surfaced in all environments.

### Step 4.3: Validate CORS/Origin Config

- Test that frontend can access backend API only from allowed origins, in each environment.
- Write tests that verify CORS errors are returned for disallowed origins.

---

## Phase 5: Unified `.env` Management

### Step 5.1: Create/Update `.env.example` Template

- List all necessary env vars for each service and environment in a single, canonical `.env.example`.

### Step 5.2: Update Docker Compose for Unified `.env` Usage

- Ensure all Compose services read from the same or environment-specific `.env` files.

### Step 5.3: Automate `.env` Validation

- Add a CI step or dev script that checks `.env` files for missing or extra keys versus `.env.example`.

---

## Phase 6: Manual & Automated End-to-End Testing

### Step 6.1: Manual Testing Matrix

- For each environment (local, Docker, cloud):

  - Run the full login/auth flow.
  - Confirm protected API access.
  - Simulate misconfigured env and verify error reporting.

### Step 6.2: Automated Auth Flow Tests

- Use Playwright/Cypress or similar to script the login, callback, and protected resource access flow in all environments.
- Write regression tests for key error paths (missing env, CORS failure, bad redirect).

### Step 6.3: Integration Smoke Test for Nginx & OAuth2 Proxy

- Build a simple script or test to hit `/oauth2/callback` and `/admin/` routes via Nginx in Docker Compose and verify expected response codes and redirects.

---

## Phase 7: Documentation & Cleanup

### Step 7.1: Update README / Quickstart

- Add instructions for:

  - Local startup (`make serve`, etc.)
  - Docker Compose startup and env setup
  - Registering/updating Google OAuth redirect URIs
  - Troubleshooting common auth/routing errors

### Step 7.2: Remove Legacy/Unused Config

- Clean up obsolete redirects, unused env vars, and old Nginx or Compose configs.

### Step 7.3: Final Security & Code Review

- Audit that secrets/config are not committed and that sensitive settings are only passed via env.
- Review Dockerfiles/Compose for best practices.

---

# LLM Code Generation Prompts (Chunked)

---

## Prompt 1: Audit & Baseline

```text
You are refactoring a full-stack app to use env-based OAuth config. Locate all hardcoded OAuth config (client ID, secret, redirect URI, CORS origins) in backend, frontend, nginx, and oauth2-proxy. List their locations and current values. Output a table summarizing the findings.
```

## Prompt 2: Replace Backend Hardcoding

```text
Refactor the backend (FastAPI) codebase to source all OAuth client IDs, secrets, redirect URIs, and CORS origins from environment variables. Add default values only for dev, and fail fast in prod if missing. Write a test to confirm these settings are loaded at app startup.
```

## Prompt 3: Replace Frontend Hardcoding

```text
Update frontend config/build (e.g., React Vite or Create React App) to read all OAuth, backend URL, and CORS-related settings from environment variables or build-time config. Provide a test page or component to display current env config for validation.
```

## Prompt 4: Nginx & OAuth2 Proxy Templating

```text
Modify nginx.conf and oauth2-proxy config so that all hostnames, ports, client IDs/secrets, and callback URIs are driven by environment variables or Compose env_file. Use envsubst or Docker Compose templating. Add a script to validate that all required envs are present at container startup.
```

## Prompt 5: Docker Compose Env Injection

```text
Update docker-compose.yml so all services (backend, frontend, nginx, oauth2-proxy) receive their config via unified .env files. Validate that both local and Docker Compose startup inject the same environment variables, and that ports/hostnames match expected values.
```

## Prompt 6: Callback URI & Registration

```text
Standardize all OAuth callback and redirect URIs so that local and Docker Compose both use http://localhost:3000/oauth2/callback, and production uses https://<your-app>.fly.dev/oauth2/callback. Output a checklist for updating Google OAuth with all URIs in use.
```

## Prompt 7: Health, CORS, and Error Handling

```text
Add/verify health check endpoints on backend and oauth2-proxy. Ensure all CORS and OAuth callback errors are logged (with env context) and returned clearly to users. Write integration tests for auth errors and CORS errors in all environments.
```

## Prompt 8: Unified .env Management

```text
Create a .env.example listing all env variables needed for backend, frontend, nginx, and oauth2-proxy. Add a validation script or CI job to check real .env files match the example. Write a test to verify config loading fails if required variables are missing.
```

## Prompt 9: Manual/E2E Testing and Docs

```text
Write manual test instructions and e2e test cases (Cypress/Playwright) for the full login/auth flow in local, Docker Compose, and cloud. Update the README to describe local and Docker Compose setup, Google OAuth registration, troubleshooting, and expected login behaviors.
```

---

# END OF BLUEPRINT & PROMPTS
