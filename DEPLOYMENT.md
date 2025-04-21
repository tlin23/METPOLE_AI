# Deployment Guide for MetPol AI

This guide provides instructions for deploying the MetPol AI application to cloud services.

## Overview

The application consists of two main components:
1. **Backend API**: A FastAPI application that handles crawling, embedding, and retrieving information
2. **Frontend**: A React application that provides a user interface for interacting with the API

## Deployment Options

### Option 1: Render.com (Recommended)

#### Prerequisites
- A Render.com account
- Git repository with the application code
- OpenAI API key

#### Deployment Steps

1. **Push your code to a Git repository** (GitHub, GitLab, etc.)

2. **Connect your repository to Render**:
   - Log in to your Render dashboard
   - Click "New" and select "Blueprint"
   - Connect your Git repository
   - Render will automatically detect the `render.yaml` file and create the services

3. **Configure environment variables**:
   - After the services are created, go to each service's dashboard
   - For the backend service, add your OpenAI API key in the environment variables section

4. **Deploy the services**:
   - Render will automatically deploy both services
   - The backend will be available at: https://metpol-ai-backend.onrender.com
   - The frontend will be available at: https://metpol-ai-frontend.onrender.com

### Option 2: Fly.io for Backend + Render for Frontend

#### Prerequisites
- A Fly.io account
- A Render.com account
- Fly CLI installed locally
- Git repository with the application code
- OpenAI API key

#### Deployment Steps

1. **Deploy the backend to Fly.io**:
   ```bash
   # Login to Fly
   fly auth login

   # Create a volume for persistent data
   fly volumes create metpol_data --size 10

   # Deploy the application
   fly deploy

   # Set the OpenAI API key
   fly secrets set OPENAI_API_KEY=your_openai_api_key
   fly secrets set SECRET_KEY=your_secret_key
   ```

2. **Deploy the frontend to Render**:
   - Log in to your Render dashboard
   - Click "New" and select "Web Service"
   - Connect your Git repository
   - Select the frontend directory
   - Set the environment variable `BACKEND_API_URL` to your Fly.io backend URL (e.g., https://metpol-ai-backend.fly.dev)
   - Deploy the service

## Testing the Deployment

After deployment, you should test the following functionality:

1. **Basic connectivity**: Ensure the frontend can connect to the backend
2. **Crawling**: Test the crawling functionality by using the `/api/crawl` endpoint
3. **Querying**: Test querying for information using the chat interface
4. **Source display**: Verify that source information is correctly displayed
5. **Feedback logging**: Test the feedback submission functionality

## Troubleshooting

### Common Issues

1. **CORS errors**: If the frontend cannot connect to the backend, check that CORS is properly configured
2. **Missing environment variables**: Ensure all required environment variables are set
3. **Database connectivity**: Check that the ChromaDB is properly initialized and accessible
4. **API rate limits**: Be aware of OpenAI API rate limits that may affect the application

### Logs

- **Render**: Access logs from the Render dashboard for each service
- **Fly.io**: Use `fly logs` to view backend logs

## Maintenance

### Updating the Application

1. Push changes to your Git repository
2. Render and Fly.io will automatically detect changes and redeploy

### Scaling

- **Render**: Adjust the service plan and number of instances in the dashboard
- **Fly.io**: Use `fly scale` to adjust the number and size of instances
