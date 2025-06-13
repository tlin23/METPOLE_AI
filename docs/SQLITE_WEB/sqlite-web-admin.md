# SQLite Web Admin Access

This document describes how to securely access the SQLite Web interface for database administration.

## Security Overview

The SQLite Web interface is not exposed to the public internet. Instead, it is only accessible through secure methods:

1. SSH tunnel using `flyctl proxy`
2. Direct shell access using `flyctl ssh console`

## Access Methods

### Method 1: Using flyctl proxy (Recommended)

This method creates a secure tunnel to access the SQLite Web interface through your local browser.

1. Install the Fly.io CLI if you haven't already:

   ```bash
   # macOS
   brew install flyctl
   ```

2. Log in to Fly.io:

   ```bash
   flyctl auth login
   ```

3. Create a secure tunnel to the SQLite Web interface:

   ```bash
   flyctl proxy 8081:8080 -a metpol-ai
   ```

4. Access the interface in your browser:
   ```
   http://localhost:8081
   ```

### Method 2: Using flyctl ssh console

This method gives you direct shell access to the server.

1. Connect to the server:

   ```bash
   flyctl ssh console -a metpol-ai
   ```

2. Once connected, you can use SQLite commands directly:
   ```bash
   sqlite3 /app/backend/server/data/app.db
   ```

## Security Notes

- The SQLite Web interface is only accessible through secure tunnels
- No direct public internet access is allowed
- All access requires Fly.io authentication
- The database is in read-only mode to prevent accidental modifications

## Troubleshooting

If you encounter issues:

1. Verify you're logged into Fly.io:

   ```bash
   flyctl auth whoami
   ```

2. Check if the proxy is running:

   ```bash
   flyctl status -a metpol-ai
   ```

3. Ensure port 8081 is not in use locally:
   ```bash
   lsof -i :8081
   ```

## Best Practices

1. Always use `flyctl proxy` for database administration
2. Never expose the SQLite Web interface to the public internet
3. Keep your Fly.io credentials secure
4. Use read-only mode when possible
5. Export data rather than modifying it directly
