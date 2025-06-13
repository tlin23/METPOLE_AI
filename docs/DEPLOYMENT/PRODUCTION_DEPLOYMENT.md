# Production Deployment Guide

This guide covers deploying MetPol AI to production with proper security, environment management, and secrets handling.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Environment Configuration](#environment-configuration)
3. [Production Deployment](#production-deployment)
4. [Secrets Management](#secrets-management)
5. [Security Checklist](#security-checklist)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

## Architecture Overview

### Production Architecture

```
Internet -> Fly.io (HTTPS) -> Nginx Proxy -> FastAPI Backend
                                       -> SQLite-web (internal only)

Frontend: Vercel (separate deployment)
Database: SQLite + ChromaDB (Fly.io persistent volume)
```

### Key Components

- **Frontend**: React/Vite deployed on Vercel (`https://metpole-ai.vercel.app`)
- **Backend**: FastAPI + Nginx reverse proxy on Fly.io
- **Database**: SQLite with SQLite-web admin (internal access only)
- **Vector Store**: ChromaDB for embeddings
- **Authentication**: Google OAuth (frontend) + JWT validation (backend)

## Environment Configuration

### Development vs Production

| Setting                | Development                | Production                    |
| ---------------------- | -------------------------- | ----------------------------- |
| `PRODUCTION`           | `false`                    | `true`                        |
| `LOG_LEVEL`            | `DEBUG` or `INFO`          | `INFO` or `WARNING`           |
| `CORS_ALLOWED_ORIGINS` | Multiple localhost origins | Strict production domain only |
| Database Admin         | HTTP Basic Auth            | Fly.io internal proxy only    |
| HTTPS                  | Optional                   | Enforced                      |
| Secrets                | `.env` file                | Fly.io secrets                |

### Required Environment Variables

#### Core Application

- `PRODUCTION`: Set to `true` for production
- `LOG_LEVEL`: `INFO` recommended for production
- `METROPOLE_DB_PATH`: `/data/app.db` (persistent volume)
- `INDEX_DIR`: `/data/chroma_db` (persistent volume)

#### Authentication & Security

- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- `ADMIN_EMAILS`: Comma-separated admin email addresses
- `CORS_ALLOWED_ORIGINS`: Allowed frontend origins

#### API Services

- `OPENAI_API_KEY`: OpenAI API key for AI functionality

#### Rate Limiting

- `MAX_QUESTIONS_PER_DAY`: Regular user daily limit (default: 50)
- `MAX_QUESTIONS_PER_DAY_ADMIN`: Admin user daily limit (default: 300)

#### Database Admin Security

- `DB_ADMIN_USERNAME`: Username for database admin interface
- `DB_ADMIN_PASSWORD`: Strong password for database admin interface

## Production Deployment

### 1. Fly.io Setup

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login to Fly.io
flyctl auth login

# Launch application (from project root)
flyctl launch

# Deploy
flyctl deploy
```

### 2. Set Production Secrets

```bash
# Required secrets for production
flyctl secrets set \
  OPENAI_API_KEY=sk-your-actual-openai-key \
  GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com \
  GOOGLE_CLIENT_SECRET=your-google-client-secret \
  ADMIN_EMAILS=admin@yourdomain.com,admin2@yourdomain.com \
  DB_ADMIN_USERNAME=admin \
  DB_ADMIN_PASSWORD=your-secure-password-here

# Verify secrets are set
flyctl secrets list
```

### 3. Configure Custom Domain (Optional)

```bash
# Add custom domain
flyctl certs add yourdomain.com

# Check certificate status
flyctl certs show yourdomain.com
```

### 4. Database Admin Access

The database admin interface is **not publicly accessible** in production for security.

**Access via Fly.io proxy:**

```bash
# Create secure tunnel to database admin
flyctl proxy 8081:8081

# Access at http://localhost:8081 (with basic auth)
# Username/Password: from DB_ADMIN_USERNAME/DB_ADMIN_PASSWORD secrets
```

## Secrets Management

### Setting Secrets

```bash
# Set individual secrets
flyctl secrets set SECRET_NAME=value

# Set multiple secrets at once
flyctl secrets set \
  SECRET1=value1 \
  SECRET2=value2 \
  SECRET3=value3
```

### Viewing Secrets

```bash
# List all secret names (values are hidden)
flyctl secrets list

# Get specific secret (if needed for debugging)
flyctl secrets get SECRET_NAME
```

### Rotating Secrets

#### Google OAuth Credentials

1. Generate new credentials in Google Cloud Console
2. Update secrets:
   ```bash
   flyctl secrets set \
     GOOGLE_CLIENT_ID=new-client-id \
     GOOGLE_CLIENT_SECRET=new-client-secret
   ```
3. Deploy to apply changes:
   ```bash
   flyctl deploy
   ```

#### OpenAI API Key

1. Generate new API key in OpenAI dashboard
2. Update secret:
   ```bash
   flyctl secrets set OPENAI_API_KEY=sk-new-api-key
   ```
3. Deploy to apply changes

#### Database Admin Password

1. Generate strong new password
2. Update secret:
   ```bash
   flyctl secrets set DB_ADMIN_PASSWORD=new-secure-password
   ```
3. Recreate `.htpasswd` file in nginx directory:
   ```bash
   htpasswd -c nginx/.htpasswd admin
   ```
4. Deploy with new password

### Emergency Secret Rotation

If secrets are compromised:

1. **Immediately revoke** compromised credentials at their source
2. **Generate new credentials**
3. **Update Fly.io secrets** with emergency priority
4. **Deploy immediately**:
   ```bash
   flyctl deploy --strategy immediate
   ```

## Security Checklist

### Pre-Deployment Security

- [ ] All secrets set via Fly.io secrets (not in code)
- [ ] `PRODUCTION=true` in production environment
- [ ] CORS origins restricted to production domain only
- [ ] Strong `DB_ADMIN_PASSWORD` set
- [ ] Admin emails list reviewed and updated
- [ ] HTTPS force-redirect enabled in Fly.io configuration

### Post-Deployment Security

- [ ] Database admin accessible only via Fly.io proxy
- [ ] SSL certificate valid and auto-renewing
- [ ] Application health checks passing
- [ ] Log monitoring configured
- [ ] Rate limiting working properly
- [ ] Google OAuth working correctly
- [ ] Admin access controls verified

### Regular Security Maintenance

- [ ] Review admin email list monthly
- [ ] Rotate API keys quarterly
- [ ] Update dependencies regularly
- [ ] Monitor security logs
- [ ] Test backup and recovery procedures

## Monitoring & Maintenance

### Application Monitoring

```bash
# View application logs
flyctl logs

# View application status
flyctl status

# View application metrics
flyctl metrics
```

### Database Backup

```bash
# Create database backup via proxy
flyctl proxy 8081:8081 &
curl -u admin:password http://localhost:8081/export > backup.sql
kill %1  # Stop proxy
```

### Health Checks

The application includes several health check endpoints:

- `GET /health` - Nginx health check
- `GET /api/health` - Backend API health check

### Performance Monitoring

Monitor these key metrics:

- **Response times**: API endpoints should respond < 2s
- **Error rates**: Should be < 1% under normal load
- **Database size**: Monitor SQLite file growth
- **Memory usage**: Should stay under 800MB
- **Rate limiting**: Monitor quota usage by users

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs for startup errors
flyctl logs --tail

# Verify all required secrets are set
flyctl secrets list

# Check deployment status
flyctl status
```

#### 2. CORS Errors from Frontend

- Verify `CORS_ALLOWED_ORIGINS` includes your frontend domain
- Check that frontend is sending proper `Authorization` header
- Verify Google OAuth configuration

#### 3. Database Admin Access Issues

```bash
# Verify proxy is working
flyctl proxy 8081:8081

# Check basic auth credentials
flyctl secrets get DB_ADMIN_USERNAME
flyctl secrets get DB_ADMIN_PASSWORD

# Verify nginx configuration
flyctl ssh console
cat /etc/nginx/nginx.conf
```

#### 4. Google OAuth Failures

- Verify `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are correct
- Check that redirect URLs in Google Console match your frontend domain
- Verify token validation in backend logs

### Emergency Procedures

#### Application Rollback

```bash
# List recent deployments
flyctl releases

# Rollback to previous version
flyctl releases rollback [version-number]
```

#### Database Recovery

```bash
# Access machine directly
flyctl ssh console

# Check database integrity
sqlite3 /data/app.db "PRAGMA integrity_check;"

# Restore from backup (if needed)
sqlite3 /data/app.db < backup.sql
```

### Support Contacts

- **Infrastructure**: Fly.io support
- **Frontend**: Vercel support
- **OAuth**: Google Cloud support
- **AI Services**: OpenAI support

---

## Quick Reference Commands

```bash
# Deploy application
flyctl deploy

# View logs
flyctl logs --tail

# Access database admin
flyctl proxy 8081:8081

# Set production secret
flyctl secrets set SECRET_NAME=value

# Emergency rollback
flyctl releases rollback

# Check application status
flyctl status
```
