#!/bin/bash

# Create config_snapshot directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
SNAPSHOT_DIR="config_snapshot_${TIMESTAMP}"
mkdir -p "$SNAPSHOT_DIR"

# Copy .env files if they exist
cp .env* "$SNAPSHOT_DIR/" 2>/dev/null || true

# Copy service configs
cp nginx.conf "$SNAPSHOT_DIR/nginx.conf"
cp docker-compose.yml "$SNAPSHOT_DIR/docker-compose.yml"
cp fly.toml "$SNAPSHOT_DIR/fly.toml"

# Copy backend configs
cp backend/server/api/auth.py "$SNAPSHOT_DIR/auth.py"
cp backend/server/tests/test_nginx.conf "$SNAPSHOT_DIR/test_nginx.conf"

# Create a summary file
cat > "$SNAPSHOT_DIR/README.md" << EOF
# Config Snapshot ${TIMESTAMP}

This directory contains snapshots of all configuration files related to OAuth and routing setup.

## Files Included

- \`.env\` files (if they exist)
- \`nginx.conf\` - Nginx reverse proxy configuration
- \`docker-compose.yml\` - Docker Compose service definitions
- \`fly.toml\` - Fly.io deployment configuration
- \`auth.py\` - Backend OAuth authentication code
- \`test_nginx.conf\` - Test Nginx configuration

## Current OAuth Configuration

### Backend
- OAuth client ID: Set via GOOGLE_CLIENT_ID env var
- Admin emails: Set via ADMIN_EMAILS env var
- Token validation: Using Google OAuth2 token verification

### OAuth2 Proxy
- Provider: Google
- Redirect URL: http://localhost:3000/oauth2/callback
- Cookie settings: Secure=true, SameSite=lax
- Email domains: * (all allowed)
- Admin emails: Set via ADMIN_EMAILS env var

### Nginx
- Entry port: 3000
- Routes:
  - /oauth2/* -> OAuth2 Proxy
  - /admin/db-query/* -> OAuth2 Proxy
  - /admin/* -> Backend
  - /static/* -> OAuth2 Proxy
  - /* -> Frontend

### Docker Compose
- Services:
  - backend: Port 8000
  - frontend: Port 3000
  - oauth2-proxy: Port 4180
  - nginx: Port 3000
  - sqlite-web: Port 8081

### Fly.io
- Services:
  - Main app: Ports 80/443
  - OAuth2 Proxy: Port 4180
  - SQLite Web: Port 8081
EOF

echo "Config snapshot created in $SNAPSHOT_DIR"
