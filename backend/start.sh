#!/bin/bash

# Start sqlite-web in the background on port 8081 (not 8080)
sqlite_web --host 127.0.0.1 --port 8081 --read-only /app/backend/server/data/app.db &

# Start FastAPI in the background on port 8000
uvicorn backend.server.app:service --host 127.0.0.1 --port 8000 &

# Start nginx on port 8080 as the reverse proxy
exec nginx -g "daemon off;"
