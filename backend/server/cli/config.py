"""
Configuration settings for the admin CLI tool.

This module centralizes all environment variables and configuration settings used by the admin CLI.
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google OAuth credentials
GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")

# API configuration
API_BASE_URL: str = "http://localhost:8000/api"
# API_BASE_URL: str = "https://metpol-ai.fly.dev/api"

# OAuth configuration
OAUTH_REDIRECT_PORT: int = 8080
OAUTH_REDIRECT_URI: str = f"http://localhost:{OAUTH_REDIRECT_PORT}"
OAUTH_SCOPES: list[str] = ["openid", "email", "profile"]

# Token configuration
TOKEN_FILE: str = os.path.expanduser("~/.metpol_admin_token.json")
