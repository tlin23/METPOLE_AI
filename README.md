# Metropole.AI

An AI-powered chatbot application that answers questions about the Metropole building using RAG (Retrieval-Augmented Generation) technology.

## Overview

Metropole.AI is a full-stack application that combines document retrieval with large language models to provide accurate, source-backed answers to user questions about building information, maintenance, rules, and more.

### Key Features

- **AI-Powered Q&A**: Natural language question answering using OpenAI GPT models
- **Source Citations**: Displays source documents for answer transparency
- **Google OAuth Authentication**: Secure login with Google accounts
- **Admin Dashboard**: User management, analytics, and system controls
- **Rate Limiting**: Configurable daily question limits per user
- **Feedback System**: Users can provide feedback on answer quality
- **Document Processing Pipeline**: Automated crawling, parsing, and embedding of various document formats

## Architecture

### Tech Stack

**Frontend**
- React 19 with Vite
- Styled Components for styling
- Google OAuth integration
- Axios for API communication

**Backend**
- FastAPI (Python)
- OpenAI API for LLM responses
- LangChain for RAG orchestration
- ChromaDB for vector storage
- Sentence Transformers for embeddings
- SQLite for user data and analytics

**Document Processing**
- Unstructured.io for document parsing
- Support for PDF, DOCX, PPTX, XLSX, images (OCR)
- Web crawling capabilities
- Automated embedding pipeline

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- OpenAI API key
- Google OAuth credentials

### Environment Setup

1. Copy the environment template:
   ```bash
   cp env.example .env
   ```

2. Configure required environment variables in `.env`:
   ```bash
   # OpenAI
   OPENAI_API_KEY=sk-your-openai-api-key

   # Google OAuth
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret

   # Admin Access
   ADMIN_EMAILS=admin@example.com

   # Rate Limits
   MAX_QUESTIONS_PER_DAY=50
   MAX_QUESTIONS_PER_DAY_ADMIN=300
   ```

3. Configure frontend environment:
   ```bash
   cd frontend
   cp .env.example .env
   ```

   Update `frontend/.env`:
   ```bash
   VITE_BACKEND_URL=http://localhost:8000
   VITE_FRONTEND_URL=http://localhost:3000
   VITE_OAUTH_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   VITE_OAUTH_REDIRECT_URI=http://localhost:3000/oauth2/callback
   ```

### Local Development

#### Backend

```bash
# Install dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the server
uvicorn backend.server.app:service --host 0.0.0.0 --port 8000 --reload
```

Or use the Makefile:
```bash
make serve
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

Or use the Makefile:
```bash
make front
```

#### Access the Application

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Document Processing Pipeline

The application includes a complete pipeline for processing and embedding documents:

```bash
# Crawl web content
make crawl

# Sort and organize content
make sort

# Parse documents
make parse

# Generate embeddings
make embed

# Or run the full pipeline
make pip-prod-full
```

## Deployment

### Production Deployment

The application is designed to deploy to:
- **Backend**: Fly.io
- **Frontend**: Vercel

See [docs/DEPLOYMENT/deployment.md](docs/DEPLOYMENT/deployment.md) for detailed deployment instructions.

### Docker Deployment

```bash
docker-compose up -d
```

## Admin Features

### Admin CLI

Manage users and quotas via CLI:

```bash
# Check admin status
make admin-status

# List all admins
make admin-list

# Add admin
make admin-add email=user@example.com

# Reset user quota
make admin-reset-quota email=user@example.com

# Check user quota
make admin-check-quota email=user@example.com
```

### SQLite Web Interface

For local development:
```bash
sqlite_web --host 0.0.0.0 --port 8080 backend/server/data/app.db
```

For production (via Fly.io proxy):
```bash
flyctl proxy 8081:8080 -a metpol-ai
# Access at http://localhost:8081
```

## Development

### Code Quality

```bash
# Run linting
make lint

# Format code
make format

# Run tests
make test
```

### Testing

The project includes:
- **Unit tests**: For individual components
- **Integration tests**: For API endpoints
- **E2E tests**: For complete user flows

See [docs/TESTS](docs/TESTS) for testing documentation.

## Project Structure

```
METPOL_AI/
├── backend/
│   ├── server/              # FastAPI application
│   │   ├── api/            # API routes
│   │   ├── database/       # Database models & connection
│   │   └── cli/            # Admin CLI tools
│   ├── data_processing/     # Document processing pipeline
│   │   ├── crawlers/       # Web crawlers
│   │   ├── parsers/        # Document parsers
│   │   ├── embedder/       # Embedding generation
│   │   └── pipeline/       # Pipeline orchestration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   └── App.jsx
│   └── package.json
├── docs/                    # Documentation
├── scripts/                 # Utility scripts
├── docker-compose.yml
├── Makefile
└── env.example
```

## API Documentation

Once the backend is running, interactive API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

### Rate Limiting

Configure daily question limits in `.env`:
```bash
MAX_QUESTIONS_PER_DAY=50         # Regular users
MAX_QUESTIONS_PER_DAY_ADMIN=300  # Admin users
```

### CORS

Configure allowed origins for production:
```bash
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com
```

### Database

The application uses SQLite for simplicity. The database stores:
- User accounts and authentication
- Question/answer sessions
- User feedback
- Analytics and usage tracking

## Troubleshooting

### Common Issues

1. **OAuth Login Fails**
   - Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
   - Check authorized redirect URIs in Google Cloud Console

2. **OpenAI API Errors**
   - Verify `OPENAI_API_KEY` is valid
   - Check API quota and billing

3. **Database Issues**
   - Ensure database path is writable
   - Check `METROPOLE_DB_PATH` environment variable

For more troubleshooting tips, see [docs/DEPLOYMENT/deployment.md](docs/DEPLOYMENT/deployment.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

This project is proprietary software for Metropole building management.

## Support

For issues or questions, please contact the development team or create an issue in the repository.
