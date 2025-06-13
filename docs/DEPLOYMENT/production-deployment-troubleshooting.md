# Production Deployment Troubleshooting Guide

This guide documents common issues encountered during production deployment and their solutions. Use Ctrl+F to search for specific error messages or symptoms.

## Table of Contents

1. [Frontend Login Issues](#frontend-login-issues)
2. [Backend Health Check Failures](#backend-health-check-failures)
3. [SQLite Web Interface Issues](#sqlite-web-interface-issues)
4. [Nginx Reverse Proxy Issues](#nginx-reverse-proxy-issues)
5. [Debugging Commands](#debugging-commands)

---

## Frontend Login Issues

### Issue: Frontend redirects back to login page after successful Google authentication

**Symptoms:**

- User can click login and authenticate with Google successfully
- After authentication, user is redirected back to login page
- Browser developer tools show 404 error for `/api/admin/me`
- Error message: `{"detail":"Not Found"}`

**Root Cause:**
Backend code changes were made locally but never deployed to production. The production backend was running an older version without the `/api/admin/me` endpoint.

**Solution:**

```bash
# Deploy the latest backend code
flyctl deploy

# Verify deployment
flyctl status
curl -s https://metpol-ai.fly.dev/api/health
```

**Prevention:**
Always run `flyctl deploy` after making backend code changes, even if the app appears to be running on Fly.io.

---

## Backend Health Check Failures

### Issue: Deployment fails with health check timeout errors

**Symptoms:**

- `flyctl deploy` shows timeout errors
- `flyctl status` shows "1 critical" health check
- Logs show: "Health check on port 8080 has failed"
- API returns 404 or connection errors

**Root Cause 1: Wrong Health Check Path**
The health check was configured to check `/health` but the FastAPI app serves health at `/api/health`.

**Solution 1:**
Update `fly.toml` to use the correct health check path:

```toml
[[services.http_checks]]
  path = "/api/health"  # Not "/health"
```

**Root Cause 2: Missing Nginx Reverse Proxy**
The start script was running SQLite-web directly on port 8080 instead of nginx as a reverse proxy.

**Solution 2:**
Fix the architecture to use nginx as reverse proxy:

1. **Update `backend/start.sh`:**

```bash
#!/bin/bash
# Start sqlite-web on port 8081 (not 8080)
sqlite_web --host 127.0.0.1 --port 8081 --read-only /app/backend/server/data/app.db &

# Start FastAPI on port 8000
uvicorn backend.server.app:service --host 127.0.0.1 --port 8000 &

# Start nginx on port 8080 as reverse proxy
exec nginx -g "daemon off;"
```

2. **Update `backend/Dockerfile`:**

```dockerfile
# Install nginx
RUN apt-get update && apt-get install -y curl nginx && rm -rf /var/lib/apt/lists/*

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/.htpasswd /etc/nginx/.htpasswd
```

3. **Update `nginx/nginx.conf` upstream servers:**

```nginx
upstream backend {
    server 127.0.0.1:8000;  # Not "backend:8000"
}

upstream sqlite-web {
    server 127.0.0.1:8081;  # Not "sqlite-web:8081"
}
```

4. **Update `fly.toml` health check:**

```toml
[[services.http_checks]]
  path = "/health"  # Nginx serves this, not "/api/health"
```

---

## SQLite Web Interface Issues

### Issue: flyctl proxy connection fails with "connection reset"

**Symptoms:**

- `flyctl proxy 8081:8080 -a metpol-ai` shows "Proxying..." but then exits
- `curl http://localhost:8081` returns "Connection reset by peer"
- Browser shows "ERR_CONNECTION_RESET"

**Root Cause:**
Nginx was listening on `127.0.0.1:8080` instead of `0.0.0.0:8080`, preventing external connections.

**Solution:**
Update `nginx/nginx.conf`:

```nginx
server {
    listen 0.0.0.0:8080;  # Not just "listen 8080;"
    server_name localhost;
    # ... rest of config
}
```

**Alternative Solution (Recommended):**
Access SQLite-web directly via HTTPS instead of proxy:

- URL: `https://metpol-ai.fly.dev/db/`
- Credentials: `admin` / `metropole`
- More secure (HTTPS) and doesn't require proxy

### Issue: SQLite Web Interface loads but CSS/styling is broken

**Symptoms:**

- SQLite-web interface loads and shows content
- No styling, looks like plain HTML
- Database tables are visible but interface looks broken
- Browser developer tools show 404 errors for CSS/JS files

**Root Cause:**
SQLite-web's static assets (CSS, JS) are served from `/static/` paths, but nginx had no route for `/static/`.

**Solution:**
Add static asset routing to `nginx/nginx.conf`:

```nginx
# Static assets for sqlite-web (CSS, JS, etc.)
location /static/ {
    # HTTP Basic Auth protection
    auth_basic "Database Admin Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # Proxy to sqlite-web static assets
    proxy_pass http://sqlite-web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Cache static assets
    expires 1h;
    add_header Cache-Control "public, immutable";
}
```

### Issue: SQLite Web Interface navigation links don't work

**Symptoms:**

- Main SQLite-web interface loads with proper styling
- Clicking table links (answers, feedback, questions, etc.) shows "Frontend is deployed separately to Vercel"
- URLs like `https://metpol-ai.fly.dev/answers/` return 404

**Root Cause:**
SQLite-web generates links to `/answers/`, `/questions/`, etc., but nginx only had routes for `/db/` and `/api/`.

**Solution:**
Add routes for all SQLite-web endpoints to `nginx/nginx.conf`:

```nginx
# SQLite-web table and action routes
location ~ ^/(answers|feedback|questions|sessions|users|query)/ {
    # HTTP Basic Auth protection
    auth_basic "Database Admin Access";
    auth_basic_user_file /etc/nginx/.htpasswd;

    # Proxy to sqlite-web, keeping the full path
    proxy_pass http://sqlite-web;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    proxy_set_header X-Forwarded-Port $server_port;
}
```

---

## Nginx Reverse Proxy Issues

### Issue: Service architecture confusion

**Problem:**
Confusion about whether to run services directly or use nginx as reverse proxy.

**Solution:**
Use this architecture for production:

- **Port 8080**: Nginx (exposed to internet via Fly.io)
- **Port 8000**: FastAPI (internal only, accessed via nginx `/api/` routes)
- **Port 8081**: SQLite-web (internal only, accessed via nginx `/db/` routes)

**Nginx Configuration Pattern:**

```nginx
server {
    listen 0.0.0.0:8080;

    # API routes go to FastAPI
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        # ... proxy headers
    }

    # Database admin routes go to SQLite-web
    location /db/ {
        auth_basic "Database Admin Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081/;
        # ... proxy headers
    }

    # Static assets for SQLite-web
    location /static/ {
        auth_basic "Database Admin Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081;
        # ... proxy headers
    }

    # SQLite-web endpoints
    location ~ ^/(answers|feedback|questions|sessions|users|query)/ {
        auth_basic "Database Admin Access";
        auth_basic_user_file /etc/nginx/.htpasswd;
        proxy_pass http://127.0.0.1:8081;
        # ... proxy headers
    }

    # Health check for Fly.io
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
```

---

## Debugging Commands

### Check Deployment Status

```bash
# Check app status and health
flyctl status

# View recent logs
flyctl logs --app metpol-ai

# Check machine details
flyctl machine status <machine-id>
```

### Test Endpoints

```bash
# Test backend health
curl -s https://metpol-ai.fly.dev/api/health

# Test nginx health
curl -s https://metpol-ai.fly.dev/health

# Test admin endpoint (should return 401 without auth)
curl -s https://metpol-ai.fly.dev/api/admin/me

# Test SQLite-web with auth
curl -u admin:metropole -I https://metpol-ai.fly.dev/db/
```

### Debug Inside Production Container

```bash
# SSH into production container
flyctl ssh console -a metpol-ai

# Inside container - test services
curl -I http://127.0.0.1:8080/health     # nginx
curl -I http://127.0.0.1:8000/api/health # FastAPI
curl -I http://127.0.0.1:8081/           # SQLite-web

# Check nginx config
nginx -t

# View nginx logs
cat /var/log/nginx/error.log
cat /var/log/nginx/access.log
```

### Common Error Patterns

| Error Message                | Likely Cause                               | Solution                               |
| ---------------------------- | ------------------------------------------ | -------------------------------------- |
| `{"detail":"Not Found"}`     | Endpoint doesn't exist or wrong path       | Check if latest code is deployed       |
| `ERR_CONNECTION_RESET`       | Service not listening on correct interface | Change `127.0.0.1` to `0.0.0.0`        |
| `Health check failed`        | Wrong health check path or service down    | Verify health check path in `fly.toml` |
| `401 Authorization Required` | Missing HTTP Basic Auth                    | Add credentials for `/db/` routes      |
| CSS/styling broken           | Static assets not routed                   | Add `/static/` route to nginx          |
| Navigation links broken      | Missing routes for SQLite-web endpoints    | Add regex routes for table names       |

---

## Deployment Checklist

Before deploying, ensure:

- [ ] Latest code committed and ready
- [ ] `fly.toml` health check path is correct (`/health` for nginx)
- [ ] `nginx/nginx.conf` has all required routes
- [ ] `backend/start.sh` starts all services correctly
- [ ] Environment variables and secrets are set
- [ ] Run `flyctl deploy` and verify `flyctl status` shows all checks passing

After deploying, test:

- [ ] Frontend login and functionality
- [ ] Backend API endpoints
- [ ] SQLite-web interface accessibility and navigation
- [ ] All end-to-end user flows work correctly
