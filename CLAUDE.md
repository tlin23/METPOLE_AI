# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Metropole.AI is a RAG (Retrieval-Augmented Generation) chatbot application that answers questions about the Metropole building. The system combines document retrieval with OpenAI GPT models to provide accurate, source-backed answers.

**Tech Stack:**
- **Backend:** FastAPI (Python 3.11+), ChromaDB (vector store), LangChain (RAG orchestration), SQLite (user data)
- **Frontend:** React 19 + Vite, Styled Components, Google OAuth
- **Document Processing:** Unstructured.io, Sentence Transformers for embeddings
- **Deployment:** Fly.io (backend), Vercel (frontend)

## Common Development Commands

### Backend Development

```bash
# Start backend server with hot reload
make serve
# Or: uvicorn backend.server.app:service --reload --host 127.0.0.1 --port 8000

# Start production-like server (no reload)
make serve-prod

# Run all tests
make test

# Run only server tests with coverage
make test-server

# Run only data processing pipeline tests
make test-pipeline

# Linting and formatting
make lint
make format
```

### Frontend Development

```bash
# Start frontend dev server
cd frontend && npm run dev
# Or: make front

# Build frontend for production
cd frontend && npm run build

# Lint frontend
cd frontend && npm run lint
```

### Running Tests

```bash
# All tests
make test

# Server tests with coverage (minimum 90% required)
make test-server

# Pipeline tests
make test-pipeline
```

### Document Processing Pipeline

The pipeline has 4 stages: crawl → sort → parse → embed

```bash
# Full pipeline (production mode - uses prod/ directory)
make pip-prod-full

# Full pipeline (development mode - uses dev/ directory)
make pip-dev-full

# Individual steps
make crawl    # Crawl web content
make sort     # Organize crawled content
make parse    # Parse documents into chunks
make embed    # Generate embeddings and store in ChromaDB

# Fast development: parse + embed only (skips crawl/sort)
make pip-dev-fast

# Local development: sort + parse + embed (skips crawl)
make pip-dev-local
```

### Admin CLI

```bash
# Check admin status
make admin-status

# List all admin users
make admin-list

# Add/remove admin
make admin-add email=user@example.com
make admin-remove email=user@example.com

# Manage user quotas
make admin-reset-quota email=user@example.com
make admin-check-quota email=user@example.com
```

## Architecture

### Backend Structure

The backend is organized into distinct modules:

**`backend/server/`** - FastAPI application
- `app.py` - Main FastAPI application with CORS, exception handlers, and lifespan management
- `api/` - API routes split into:
  - `main/` - Core endpoints (`/ask`, `/feedback`, `/health`)
  - `admin/` - Admin-only endpoints (user management, analytics)
  - `auth.py` - Google OAuth token validation
  - `models/` - Pydantic request/response models
- `database/` - SQLite integration
  - `connection.py` - Database connection management (uses `METROPOLE_DB_PATH` env var)
  - `models/` - Database models (User, Session, Question, Answer, Feedback)
  - `schema.sql` - Database schema
- `retriever/` - RAG implementation
  - `ask.py` - Main `Retriever` class that queries ChromaDB and calls OpenAI
  - `models.py` - Data models for retrieved chunks
- `app_config.py` - Centralized configuration loading from environment variables

**`backend/data_processing/`** - Document processing pipeline
- `crawlers/` - Web and local file crawlers
- `parsers/` - Document parsers (HTML, PDF, DOCX)
- `embedder/` - Embedding generation using Sentence Transformers
- `pipeline/` - Pipeline orchestration and CLI
- `models/` - Shared data models (ContentChunk)

### Environment-Specific Paths

The system uses different directories for dev vs production:
- **Development:** `backend/data/dev/` (ChromaDB: `dev/chroma_db`)
- **Production:** `backend/data/prod/` (ChromaDB: `prod/chroma_db`)

The environment is determined by:
- `PRODUCTION=true` environment variable for production mode
- Pipeline CLI `--production` flag

### Key Components

**RAG Pipeline Flow:**
1. User asks question → `/api/ask` endpoint
2. Validates OAuth token → checks user quota
3. Creates session and question record
4. `Retriever.query()` searches ChromaDB using cosine similarity
5. `Retriever.generate_answer()` constructs prompt with retrieved chunks
6. OpenAI GPT-3.5-turbo generates answer
7. Stores answer, updates quota, returns response with sources

**Document Processing Flow:**
1. **Crawl:** WebCrawler downloads HTML/files from allowed domains
2. **Sort:** LocalCrawler organizes files by type (`.html`, `.pdf`, `.docx`)
3. **Parse:** Parser converts documents to `ContentChunk` objects with metadata
4. **Embed:** Generates embeddings using Sentence Transformers, stores in ChromaDB

**Authentication & Authorization:**
- Google OAuth for login (frontend uses `@react-oauth/google`)
- Backend validates Google tokens via `validate_token` dependency
- Admin status determined by email in `ADMIN_EMAILS` env var
- Rate limiting: Different quotas for users vs admins

**Database Schema:**
- `users` - User profiles (email, name, picture, admin status)
- `sessions` - User sessions (start/end times)
- `questions` - Questions asked by users
- `answers` - Generated answers with retrieved chunks and metadata
- `feedback` - User feedback on answers (like/dislike, suggestions)

### ChromaDB Collection

The system uses a single collection named `"metropole"` with:
- Sentence Transformer embeddings
- Metadata: `document_title`, `document_name`, `section`, `chunk_id`, `url`, `file_path`
- Cosine similarity for retrieval

### Important Configuration

**Required Environment Variables:**
- `OPENAI_API_KEY` - OpenAI API key
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - Google OAuth credentials
- `ADMIN_EMAILS` - Comma-separated list of admin emails
- `METROPOLE_DB_PATH` - Absolute path to SQLite database
- `MAX_QUESTIONS_PER_DAY` / `MAX_QUESTIONS_PER_DAY_ADMIN` - Rate limits

**Optional Environment Variables:**
- `PRODUCTION` - Set to "true" for production mode
- `LOG_LEVEL` - Logging level (default: INFO)
- `CORS_ALLOWED_ORIGINS` - Comma-separated CORS origins
- `INDEX_DIR` - Override ChromaDB path

## Testing

The project has comprehensive test coverage:

**Server Tests (`backend/server/tests/`):**
- `unit/` - Unit tests for models
- `integration/` - API endpoint tests, OAuth flow tests, error handling
- `security/` - Security tests (SQL injection, XSS, etc.)
- `load/` - Load testing
- `factories/` - Test data factories

**Pipeline Tests (`backend/data_processing/tests/`):**
- `crawlers/` - Crawler tests
- `parsers/` - Parser tests
- `embedder/` - Embedding tests
- `pipeline/` - Orchestration tests

**Test Requirements:**
- Minimum 90% coverage for server tests (`make test-server`)
- All tests must pass before deployment

## Development Workflow

1. **Local Development:**
   - Copy `env.example` to `.env` and configure
   - Copy `frontend/.env.example` to `frontend/.env`
   - Run `make serve` for backend, `make front` for frontend
   - Access frontend at http://localhost:3000
   - Access API docs at http://localhost:8000/docs

2. **Document Updates:**
   - Place files in `backend/data/dev/local_input_source/`
   - Run `make pip-dev-local` to process and embed

3. **Testing Changes:**
   - Run `make test` before committing
   - Run `make lint` and `make format` for code quality

4. **Production Deployment:**
   - Backend: `flyctl deploy` from project root (uses `backend/Dockerfile`)
   - Frontend: Push to main branch (Vercel auto-deploys via GitHub Actions)
   - See `docs/DEPLOYMENT/deployment.md` for details

## CI/CD Pipeline

### GitHub Actions Workflows

**`.github/workflows/ci.yml`** - Runs on every push to main/develop:
- Backend tests with 80% minimum coverage
- Frontend linting and build
- Docker build tests
- Security scanning

**`.github/workflows/deploy-vercel.yml`** - Runs on push to main when frontend changes:
- Automatically deploys frontend to Vercel production
- Triggered by changes to `frontend/**` or workflow files

### Required GitHub Secrets

Configure these in your GitHub repository settings (Settings → Secrets and variables → Actions):

**For CI Pipeline:**
- `VITE_OAUTH_CLIENT_ID` - Google OAuth client ID for frontend builds (optional, uses fallback in CI)

**For Vercel Deployment:**
- `VERCEL_TOKEN` - Vercel API token (get from Vercel account settings)
- `VERCEL_ORG_ID` - Vercel organization ID (found in `.vercel/project.json` as `orgId`)
- `VERCEL_PROJECT_ID` - Vercel project ID (found in `.vercel/project.json` as `projectId`)

### Setting Up Vercel Auto-Deploy

1. **Get Vercel credentials:**
   ```bash
   # Already configured in .vercel/project.json:
   # - orgId: team_GC5wrA4rl9ubFJrX1PUJV0eq
   # - projectId: prj_FIKCsLEqf5VUsAX2k6kITVclFkfu
   ```

2. **Create Vercel API token:**
   - Go to https://vercel.com/account/tokens
   - Create a new token with deployment permissions
   - Add it as `VERCEL_TOKEN` secret in GitHub

3. **Add secrets to GitHub:**
   ```bash
   # In GitHub repository: Settings → Secrets → Actions
   # Add these three secrets:
   VERCEL_TOKEN=<your-vercel-token>
   VERCEL_ORG_ID=team_GC5wrA4rl9ubFJrX1PUJV0eq
   VERCEL_PROJECT_ID=prj_FIKCsLEqf5VUsAX2k6kITVclFkfu
   ```

4. **Configure Vercel environment variables:**
   - In Vercel dashboard, set production environment variables:
     - `VITE_OAUTH_CLIENT_ID`
     - `VITE_BACKEND_URL`
     - `VITE_FRONTEND_URL`
     - `VITE_OAUTH_REDIRECT_URI`

### Deployment Flow

**On push to main:**
1. CI pipeline runs all tests
2. If tests pass and frontend files changed → Vercel deployment workflow triggers
3. Vercel builds and deploys frontend automatically
4. Backend must be deployed manually via `flyctl deploy`

**Manual deployment (if needed):**
```bash
# Frontend (if automatic deployment fails)
cd frontend
vercel --prod

# Backend (always manual)
flyctl deploy
```

## Important Notes

- **Database Path:** Always use absolute paths for `METROPOLE_DB_PATH`
- **ChromaDB:** Collection is named `"metropole"` - don't rename without migration
- **OAuth:** Ensure redirect URIs match in Google Cloud Console
- **Rate Limits:** Quotas reset at midnight UTC
- **Logging:** Uses custom logger from `backend/logger/logging_config.py`
- **Error Handling:** All API errors return structured JSON responses
- **CORS:** Production uses strict origins from `CORS_ALLOWED_ORIGINS`

## Module Import Paths

When working in the backend, use absolute imports from `backend.` namespace:
```python
from backend.server.database.models import User
from backend.server.retriever.ask import Retriever
from backend.data_processing.models.content_chunk import ContentChunk
```

## Running Individual Test Files

```bash
# Run a specific test file
PYTHONPATH=backend ./backend/venv/bin/python -m pytest backend/server/tests/integration/test_main_routes.py -v

# Run with coverage
PYTHONPATH=backend ./backend/venv/bin/python -m pytest backend/server/tests/ --cov=backend.server --cov-report=term-missing
```
