# Backend Dockerfile
FROM python:3.11-slim

# Set workdir to project root so `backend` is importable
WORKDIR /app

# Install curl for health checks and nginx for reverse proxy
RUN apt-get update && apt-get install -y curl nginx && rm -rf /var/lib/apt/lists/*

# Copy only backend code and root-level requirements
COPY backend backend
COPY backend/requirements.txt .

# Install backend dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy nginx configuration
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY nginx/.htpasswd /etc/nginx/.htpasswd

# Create nginx log directory
RUN mkdir -p /var/log/nginx

# Expose ports
EXPOSE 8000 8080 8081

# Create startup script
COPY backend/start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]
