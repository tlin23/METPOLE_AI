# MetPol AI Split-Service Deployment: Implementation Blueprint

---

## 1. High-Level Project Plan

1. **Remove monolithic artifacts**
2. **Decouple frontend and backend deployment**
3. **Update API URLs and environment variables**
4. **Harden backend service (CORS, error handling, security)**
5. **Document and streamline sqlite-web admin workflow**
6. **Test and validate split deployment (locally and in staging/prod)**

---

## 2. Blueprint: Iterative Implementation Chunks

### 2.1. Remove Monolithic & Proxy Artifacts

#### Chunk A: Remove Nginx and Docker Compose for Production

- Remove any production Nginx configs
- Remove monolithic Docker Compose files and proxy code
- Ensure backend and frontend run independently

#### Chunk B: Clean Backend Startup

- Ensure backend only starts the API server and sqlite-web
- Remove any code that serves static frontend or attempts SPA routing

---

### 2.2. Decouple Frontend & Backend

#### Chunk C: Update API URLs and Environment Variables

- Update backend API URLs in the frontend (use `.env` and/or config)
- Remove assumptions of same-origin (localhost, etc.)
- Configure proper CORS settings in backend

#### Chunk D: Deployment Pipeline Separation

- Deploy backend to Fly.io (API only)
- Deploy frontend to Vercel (SPA only)
- Document the deployment process for both

---

### 2.3. Secure & Document sqlite-web Admin Workflow

#### Chunk E: Harden sqlite-web Access

- Ensure sqlite-web is not exposed to public internet (remove proxy routes)
- Add admin documentation for using `flyctl proxy` and `flyctl ssh console` for access

---

### 2.4. End-to-End Testing & CI

#### Chunk F: Comprehensive Testing

- Add/expand API endpoint unit and integration tests
- Add E2E tests for frontend-backend API interactions (mocked and staging)
- Test sqlite-web access via SSH/proxy

#### Chunk G: Final Docs & Developer Onboarding

- Document new architecture, environment, and dev/admin workflows
- Clean up README and deployment guides

---

## 3. Micro-Steps for Each Chunk

### Chunk A: Remove Nginx and Docker Compose for Production

#### 1. Identify and remove all Nginx config files related to API/frontend proxying.

#### 2. Remove `nginx.conf` and related references in Dockerfiles and project scripts.

#### 3. Remove or refactor `docker-compose.yml` to exclude Nginx, and ensure backend/frontend services run independently.

---

### Chunk B: Clean Backend Startup

#### 1. Audit backend entrypoints (e.g., `main.py`, `app.py`) for any SPA/static serving logic—remove if found.

#### 2. Ensure only FastAPI and sqlite-web run as services.

#### 3. Double-check that `/api/*`, `/admin/*` are the only publicly routable endpoints.

---

### Chunk C: Update API URLs and Environment Variables

#### 1. Update `.env.production` in `frontend/` to point to the Fly.io backend API URL.

#### 2. Refactor any frontend code that uses a hardcoded backend URL.

#### 3. Audit and update backend CORS settings to allow requests from Vercel deployment.

---

### Chunk D: Deployment Pipeline Separation

#### 1. Write clear deployment scripts/docs for backend (Fly.io) and frontend (Vercel) individually.

#### 2. Remove any shared build scripts; each should be fully self-contained.

#### 3. Test each deployment pipeline (push to main, auto-deploy, etc.).

---

### Chunk E: Harden sqlite-web Access

#### 1. Remove any Nginx or proxy config that exposes sqlite-web to the public.

#### 2. Add admin-only documentation for:

- Using `flyctl ssh console` for direct shell access
- Using `flyctl proxy 8081` for secure, local sqlite-web UI
- Example commands for both

---

### Chunk F: Comprehensive Testing

#### 1. Add/verify API tests (unit, integration) for all endpoints.

#### 2. Add E2E tests simulating frontend requests to backend.

#### 3. Manually test sqlite-web access via SSH tunnel.

#### 4. Add automated CI workflows to block merge on test failure.

---

### Chunk G: Final Docs & Developer Onboarding

#### 1. Update README to reflect split-architecture, dev, and admin setup.

#### 2. Provide usage and troubleshooting docs for both frontend and backend developers.

#### 3. Ensure deployment, rollback, and admin guides are clear.

---

## 4. Cursor/Code-Gen LLM Prompt Series

Below are implementation-ready, **step-by-step prompts** to drive each stage of the migration and refactor.
**Each step is self-contained and includes all context needed for incremental, testable progress.**

---

### **Prompt 1: Remove Monolithic Nginx and Docker Compose**

```text
**Task:**
Remove all Nginx and Docker Compose configs and dependencies from the repository for production deployments.

**Context:**
- Nginx and Docker Compose were previously used for monolithic/local orchestration and API/frontend proxying.
- In split deployment, these are no longer required.

**Instructions:**
- Delete any `nginx.conf`, `nginx.conf.template`, or similar files from the root or backend directories.
- Remove Nginx-related sections from `docker-compose.yml` and ensure only backend and frontend services are defined (if Docker Compose is still used for local dev).
- Update backend and frontend Dockerfiles to remove any references to Nginx.
- Remove all references to Nginx and monolithic proxying from documentation and README.
- Commit all changes and run all tests to ensure nothing is broken.
```

---

### **Prompt 2: Audit and Clean Backend Startup (No SPA/Static Serving)**

```text
**Task:**
Ensure the backend does NOT attempt to serve the frontend app, static files, or act as a proxy for frontend routes.

**Context:**
- All frontend assets are served by Vercel; backend is API-only.
- Remove any FastAPI static route handlers or fallback logic serving frontend builds.

**Instructions:**
- Search backend entrypoints (`main.py`, `app.py`, `server/`) for any code serving static files or the frontend build.
- Remove these routes and confirm `/api/*`, `/admin/*`, and sqlite-web remain the only active endpoints.
- Add a test to ensure 404 is returned for non-existent routes.
- Commit changes and ensure all API and auth tests pass.
```

---

### **Prompt 3: Update Frontend API URL and CORS**

```text
**Task:**
Point the frontend to the production backend API URL, and configure backend CORS appropriately.

**Context:**
- Frontend and backend now live on separate domains.
- API requests must use the full Fly.io backend URL.

**Instructions:**
- Update `frontend/.env.production` to set the backend URL (e.g., `VITE_BACKEND_URL=https://metpol-ai.fly.dev`).
- Refactor all frontend API calls to use this environment variable.
- In backend (FastAPI), add or update CORS middleware to allow requests from your Vercel frontend domain.
- Add or update tests to verify CORS headers are present.
- Commit and test.
```

---

### **Prompt 4: Document and Test Backend sqlite-web Admin Access**

```text
**Task:**
Document the secure workflow for accessing sqlite-web, and ensure it is never exposed to the public internet.

**Context:**
- Only admins/developers should access sqlite-web via SSH/proxy.

**Instructions:**
- Remove any proxy or public exposure of sqlite-web in configs.
- Add documentation for using:
    - `flyctl ssh console -a <app-name>`
    - `flyctl proxy 8081`
    - `http://localhost:8081` for access
- Add a test/verification step to confirm sqlite-web is not accessible publicly.
- Commit and document.
```

---

### **Prompt 5: Split Deployment Pipelines**

```text
**Task:**
Establish independent deployment pipelines for backend (Fly.io) and frontend (Vercel).

**Context:**
- Each service must be independently deployable and updateable.

**Instructions:**
- Write or update deployment scripts and documentation for backend (Fly.io) and frontend (Vercel).
- Remove any pipeline steps that build or deploy both together.
- Verify that pushing to main triggers the appropriate deploy for each.
- Commit and test deployment to both staging and production.
```

---

### **Prompt 6: Comprehensive Testing**

```text
**Task:**
Add and verify test coverage for API endpoints, auth, and E2E integration (frontend-backend).

**Context:**
- Ensure system is robust and all changes are validated.

**Instructions:**
- Write/expand unit and integration tests for all backend endpoints, including error and edge cases.
- Add or update E2E tests simulating frontend requests to backend.
- Ensure sqlite-web is only accessible via secure methods.
- Add CI checks to block deployment on failure.
- Document how to run all tests locally and in CI.
- Commit and validate.
```

---

### **Prompt 7: Final Documentation and Developer Onboarding**

```text
**Task:**
Update documentation to reflect the new split architecture and workflows.

**Context:**
- New contributors and admins should be able to onboard quickly.

**Instructions:**
- Update README, setup guides, and admin docs to:
    - Explain the split-service model
    - Detail deployment for both frontend and backend
    - Provide usage and troubleshooting for both developers and admins
    - Include steps for secure sqlite-web access
- Remove outdated documentation for monolithic deployment.
- Commit all doc changes.
```

---

## 5. Final Checklist

- [ ] All monolithic/proxy configs removed
- [ ] Backend and frontend cleanly separated
- [ ] Secure, documented sqlite-web admin workflow
- [ ] Robust testing and CI/CD
- [ ] Up-to-date documentation

---

**This blueprint and prompt set ensures incremental, safe, and test-driven progress from monolith to robust split-service architecture.**
