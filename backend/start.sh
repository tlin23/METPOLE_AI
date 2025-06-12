#!/bin/bash

# Start sqlite-web in the background
sqlite_web --host 0.0.0.0 --port 8080 --read-only /app/backend/server/data/app.db &

# Start FastAPI
exec uvicorn backend.server.app:service --host 0.0.0.0 --port 8000
