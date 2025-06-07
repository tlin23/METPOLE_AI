# Step-by-Step Blueprint: Admin SQL Query UI with sqlite-web

---

## 1. High-Level Blueprint

**Goal:**
Expose a secure, read-only SQL web UI (sqlite-web) for `app.db`, accessible only to admins, at `/admin/db-query`.

### High-Level Steps

1. **Preparation** DONE

   - Review `app.db` schema and ensure no sensitive data.
   - Choose deployment method for sqlite-web (Docker, systemd, etc.).

2. **Deploy sqlite-web** DONE

   - Start sqlite-web in read-only mode.
   - Bind to `localhost` or a private/internal port.

3. **Set up Authentication/Authorization** DONE

   - Integrate Google OAuth for admin access.
   - Enforce that only admins can access `/admin/db-query`.

4. **Proxy Integration**

   - Configure reverse proxy (Nginx, FastAPI, or oauth2-proxy) to expose sqlite-web at `/admin/db-query`.
   - Ensure requests are only forwarded if user is authenticated (and authorized, if desired).

5. **Frontend Integration**

   - Add a “DB Query” link to admin menu/route, visible only to admins.
   - Route to `/admin/db-query` (open in new tab or iframe).

6. **Testing & Validation**

   - Test access flow, query execution, limits, and error handling.
   - Test security (no unauthorized access, no writes possible).

---

## 2. Iterative Chunk Breakdown

### Step 1: Preparation

- \[1.1] Audit app.db schema for sensitive data (optional, but good practice).
- \[1.2] Document the absolute path to app.db.

### Step 2: sqlite-web Deployment

- \[2.1] Install sqlite-web.
- \[2.2] Launch sqlite-web in read-only mode, bound to `localhost:8080`, pointed at app.db.
- \[2.3] Verify sqlite-web is accessible from the server only.

### Step 3: Authentication/Authorization

- \[3.1] Set up Google OAuth proxy (oauth2-proxy) to protect sqlite-web.
- \[3.2] Configure allowed emails (admin allowlist) in oauth2-proxy.
- \[3.3] (Optional) Integrate an additional backend check for is_admin (if strict enforcement is desired).

### Step 4: Proxy Integration

- \[4.1] Configure Nginx (or FastAPI) to reverse proxy `/admin/db-query` to `localhost:8080`.
- \[4.2] Test proxying—ensure unauthenticated users are blocked.

### Step 5: Frontend Integration

- \[5.1] Add “DB Query” link/route in frontend, visible only to admins.
- \[5.2] Route opens `/admin/db-query` in new tab or iframe.

### Step 6: Testing & Validation

- \[6.1] Manual test: only admins can access.
- \[6.2] Manual test: SELECT queries work, writes are blocked, export works.
- \[6.3] Security test: try direct access, non-admin access, and boundary queries.

---

## 3. Small, Atomic Steps

### 1. Preparation

- **1.1.1:** List all tables and columns in app.db.
- **1.1.2:** Check for PII or secrets; report findings.
- **1.2.1:** Record the absolute path to app.db for deployment config.

### 2. sqlite-web Deployment

- **2.1.1:** Add sqlite-web to your deployment scripts or Dockerfile.
- **2.2.1:** Write a startup command for sqlite-web in read-only mode.
- **2.2.2:** Test sqlite-web via curl/localhost.
- **2.3.1:** Ensure firewall restricts direct access to sqlite-web.

### 3. Authentication/Authorization

- **3.1.1:** Deploy oauth2-proxy on your server.
- **3.1.2:** Configure Google OAuth credentials.
- **3.2.1:** Add admin email allowlist to oauth2-proxy.
- **3.3.1:** (Optional) Write a minimal FastAPI route to check is_admin before proxying.

### 4. Proxy Integration

- **4.1.1:** Update Nginx config: route `/admin/db-query` to localhost:8080.
- **4.2.1:** Reload Nginx, confirm routing works.
- **4.2.2:** Attempt access as unauthenticated user (should fail).
- **4.2.3:** Attempt access as admin (should succeed).

### 5. Frontend Integration

- **5.1.1:** Add a new menu entry “DB Query” in admin UI components.
- **5.1.2:** Hide/show based on is_admin flag.
- **5.2.1:** On click, open `/admin/db-query` in new tab (safer than iframe).
- **5.2.2:** Document usage for admins.

### 6. Testing & Validation

- **6.1.1:** Log in as admin; verify access to sqlite-web.
- **6.1.2:** Log in as non-admin; verify access is blocked.
- **6.2.1:** Run sample SELECT queries; export results as CSV/JSON.
- **6.2.2:** Attempt INSERT/UPDATE; verify failure.
- **6.3.1:** Attempt to bypass auth; ensure failure.
- **6.3.2:** Verify 500-row query limit.

---

## 4. Code Generation LLM Prompts

Each section below is ready to use as a prompt for a code-generation LLM (e.g., Cursor, GPT-4o, etc.).
Each is marked as a code block (`text`).

---

### Prompt 1: Install and Configure sqlite-web

```text
Install sqlite-web in our server environment (via pip or Docker as appropriate).
Write a script or Docker Compose entry to run sqlite-web in read-only mode, pointing to our app.db (absolute path: /path/to/app.db).
Make sure it only listens on localhost:8080.
Test that you can access the UI from localhost via a browser, but it is not accessible from external IPs.
```

---

### Prompt 2: Deploy and Configure oauth2-proxy

```text
Set up oauth2-proxy on the server to protect sqlite-web with Google OAuth.
- Use our Google OAuth credentials.
- Configure allowed emails to match our admin list.
- Route oauth2-proxy to forward authenticated traffic to sqlite-web at localhost:8080.
Test the login flow end-to-end (unauthenticated, non-admin, and admin user cases).
```

---

### Prompt 3: (Optional) Backend is_admin Check Proxy

```text
Implement a minimal FastAPI route at /admin/db-query-proxy.
This route should:
- Require Google OAuth authentication (reuse existing middleware).
- Query the users table to check is_admin for the current user.
- If admin, proxy the request to sqlite-web at localhost:8080.
- If not admin, return 403 Forbidden.
Update Nginx or the frontend to use /admin/db-query-proxy as the sqlite-web access endpoint.
```

---

### Prompt 4: Nginx Reverse Proxy Config

```text
Update the Nginx config to reverse proxy all requests to /admin/db-query to localhost:8080 (sqlite-web).
- Ensure it is only accessible via HTTPS.
- Confirm that only authenticated/admin users can access.
- Test with curl and browser.
```

---

### Prompt 5: Frontend Admin Menu Integration

```text
Add a new menu entry called “DB Query” to the admin navigation in the frontend.
- Only display the menu item if the logged-in user has is_admin=true.
- When clicked, open /admin/db-query in a new browser tab.
Write basic Cypress or Playwright tests to confirm the menu item only appears for admins.
```

---

### Prompt 6: Security and Validation Testing

```text
Perform manual and automated tests to confirm:
- Only authenticated admins can access the DB Query UI.
- Non-admins and unauthenticated users are blocked at every layer.
- SELECT queries work, but INSERT/UPDATE/DELETE are blocked.
- Query results are capped at 500 rows per page.
- Export to CSV and JSON works.
- Direct access to sqlite-web (localhost:8080) is firewalled from outside.
Document all test results and any necessary fixes.
```

---

### Prompt 7: Documentation

```text
Write a section in the admin documentation explaining:
- What the DB Query tool is for
- How to access it
- Limits (read-only, 500 row cap)
- Who to contact for access or questions
- Troubleshooting common issues (login, query errors)
```
