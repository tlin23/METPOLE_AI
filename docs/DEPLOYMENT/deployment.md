# Deployment Guide

This guide covers both local development and production deployment for MetPol AI.

## Local Development

### Prerequisites

1. Install required tools:

   ```bash
   # Install Node.js (for frontend)
   brew install node@20

   # Install Python 3.11 (for backend)
   brew install python@3.11
   ```

2. Set up environment variables:

   ```bash
   # Backend (.env in root directory)
   OPENAI_API_KEY=your_openai_key
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   ADMIN_EMAILS=your_admin_email
   PRODUCTION=false
   ENABLE_DB_DUMP=True
   MAX_QUESTIONS_PER_DAY=50
   MAX_QUESTIONS_PER_DAY_ADMIN=300

   # Frontend (.env in frontend directory)
   VITE_BACKEND_URL=http://localhost:8000
   VITE_FRONTEND_URL=http://localhost:3000
   VITE_OAUTH_CLIENT_ID=your_google_client_id
   VITE_OAUTH_REDIRECT_URI=http://localhost:3000/oauth2/callback
   ```

### Running Locally

1. Start the backend and SQLite web interface:

   ```bash
   # From project root
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   sqlite_web --host 0.0.0.0 --port 8080 backend/server/data/app.db
   uvicorn backend.server.app:service --host 0.0.0.0 --port 8000
   ```

2. Start the frontend:

   ```bash
   # From project root
   cd frontend
   npm install
   npm run dev
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - SQLite Web (admin only): http://localhost:8080

## Production Deployment

### Backend (Fly.io)

1. Install Fly.io CLI:

   ```bash
   brew install flyctl
   ```

2. Log in to Fly.io:

   ```bash
   flyctl auth login
   ```

3. Deploy the backend:

   ```bash
   # From project root
   cd backend
   flyctl deploy
   ```

4. Set up secrets:

   ```bash
   flyctl secrets set OPENAI_API_KEY=your_openai_key
   flyctl secrets set GOOGLE_CLIENT_ID=your_google_client_id
   flyctl secrets set GOOGLE_CLIENT_SECRET=your_google_client_secret
   flyctl secrets set ADMIN_EMAILS=your_admin_email
   ```

5. Verify deployment:
   ```bash
   flyctl status
   flyctl logs
   ```

### Frontend (Vercel)

1. Install Vercel CLI:

   ```bash
   npm install -g vercel
   ```

2. Log in to Vercel:

   ```bash
   vercel login
   ```

3. Deploy the frontend:

   ```bash
   # From project root
   cd frontend
   vercel
   ```

4. Set up environment variables in Vercel dashboard:
   - VITE_BACKEND_URL=https://metpol-ai.fly.dev
   - VITE_FRONTEND_URL=https://metpole-ai.vercel.app
   - VITE_OAUTH_CLIENT_ID=your_google_client_id
   - VITE_OAUTH_REDIRECT_URI=https://metpole-ai.vercel.app/oauth2/callback

Note: The frontend is automatically deployed to Vercel when changes are pushed to the main branch.

## Accessing Admin Features

1. SQLite Web Interface:

   ```bash
   # Create secure tunnel
   flyctl proxy 8081:8080 -a metpol-ai

   # Access in browser
   http://localhost:8081
   ```

2. Direct Database Access:

   ```bash
   # Connect to server
   flyctl ssh console -a metpol-ai

   # Access SQLite
   sqlite3 /app/backend/server/data/app.db
   ```

## Troubleshooting

### Backend Issues

1. Check logs:

   ```bash
   flyctl logs -a metpol-ai
   ```

2. Restart service:
   ```bash
   flyctl restart -a metpol-ai
   ```

### Frontend Issues

1. Check deployment status:

   ```bash
   vercel ls
   ```

2. View deployment logs:
   ```bash
   vercel logs
   ```

### Database Issues

1. Check database connection:

   ```bash
   flyctl ssh console -a metpol-ai
   sqlite3 /app/backend/server/data/app.db ".tables"
   ```

2. Backup database:
   ```bash
   flyctl ssh sftp get /app/backend/server/data/app.db ./backup.db
   ```
