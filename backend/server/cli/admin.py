#!/usr/bin/env python3
"""
CLI interface for admin management.
Provides commands for checking admin status, listing admins, adding/removing admins,
and resetting user quotas.
"""

import os
import sys
import argparse
import requests
from dotenv import load_dotenv
from typing import Dict
import webbrowser
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
import time

# Load environment variables
load_dotenv()

# Get Google OAuth credentials from environment
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
if not GOOGLE_CLIENT_ID:
    print("Error: GOOGLE_CLIENT_ID environment variable is required")
    sys.exit(1)

# API base URL
API_BASE_URL = "http://localhost:8000/api"

# OAuth configuration
OAUTH_REDIRECT_PORT = 8080
OAUTH_REDIRECT_URI = f"http://localhost:{OAUTH_REDIRECT_PORT}"
OAUTH_SCOPES = ["openid", "email", "profile"]

TOKEN_CACHE = None
TOKEN_FILE = os.path.expanduser("~/.metpol_admin_token.json")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handle OAuth callback and store the token."""

    token = None
    token_json = None

    def do_GET(self):
        """Handle GET request to the callback URL."""
        # Parse the authorization code from the URL
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if "code" in params:
            code = params["code"][0]
            # Exchange code for token
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "redirect_uri": OAUTH_REDIRECT_URI,
                    "grant_type": "authorization_code",
                },
            )
            if token_response.status_code == 200:
                token_json = token_response.json()
                OAuthCallbackHandler.token = token_json["id_token"]
                OAuthCallbackHandler.token_json = token_json
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"Authentication successful! You can close this window."
                )
            else:
                self.send_response(400)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                self.wfile.write(b"Authentication failed. Please try again.")
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"Authentication failed. Please try again.")


def load_token_from_file():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as f:
            data = json.load(f)
            # Check expiry
            if data.get("expires_at", 0) > time.time():
                return data["id_token"]
    return None


def save_token_to_file(token_json):
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_json, f)


def get_google_token() -> str:
    global TOKEN_CACHE
    if TOKEN_CACHE is not None:
        return TOKEN_CACHE

    # Try to load token from file
    token = load_token_from_file()
    if token:
        TOKEN_CACHE = token
        return TOKEN_CACHE

    # Start local server to receive OAuth callback
    server = HTTPServer(("localhost", OAUTH_REDIRECT_PORT), OAuthCallbackHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.daemon = True
    server_thread.start()

    # Construct OAuth URL
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={GOOGLE_CLIENT_ID}&"
        f"redirect_uri={OAUTH_REDIRECT_URI}&"
        "response_type=code&"
        f"scope={' '.join(OAUTH_SCOPES)}"
    )

    # Open browser for authentication
    print("Opening browser for Google authentication...")
    webbrowser.open(auth_url)

    # Wait for token
    while OAuthCallbackHandler.token is None:
        pass

    # Clean up
    server.shutdown()
    server.server_close()

    # Save token to file with expiry
    token_json = OAuthCallbackHandler.token_json
    expires_in = token_json.get("expires_in", 3600)
    token_json["expires_at"] = int(time.time()) + int(expires_in)
    save_token_to_file(token_json)
    TOKEN_CACHE = token_json["id_token"]
    return TOKEN_CACHE


def get_headers() -> Dict[str, str]:
    """Get headers with authentication token."""
    token = get_google_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def check_system_status() -> Dict:
    """
    Check system status including whether any admins exist.
    This is a public endpoint that doesn't require admin privileges.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=get_headers())
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error checking system status: {e}")
        return {"status": "error", "message": str(e)}


def check_admin_status() -> bool:
    """Check if the current user is an admin."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/list", headers=get_headers())
        return response.status_code == 200
    except requests.exceptions.RequestException as e:
        print(f"Error checking admin status: {e}")
        return False


def is_first_admin() -> bool:
    """Check if this is the first admin being added."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", headers=get_headers())
        if response.status_code == 200:
            data = response.json()
            return not data.get("system", {}).get("has_admins", False)
        return False
    except requests.exceptions.RequestException:
        return False


def list_admins() -> None:
    """List all admin users."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/list", headers=get_headers())
        response.raise_for_status()
        admins = response.json()

        if not admins:
            print("No admin users found.")
            return

        print("\nCurrent admin users:")
        for admin in admins:
            print(f"- {admin['email']}")
    except requests.exceptions.RequestException as e:
        print(f"Error listing admins: {e}")


def add_admin(email: str) -> None:
    """Promote a user to admin status."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/add", params={"email": email}, headers=get_headers()
        )
        response.raise_for_status()
        user = response.json()
        print(f"Successfully promoted {user['email']} to admin")
    except requests.exceptions.RequestException as e:
        print(f"Error adding admin: {e}")


def remove_admin(email: str) -> None:
    """Remove admin status from a user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/remove",
            params={"email": email},
            headers=get_headers(),
        )
        response.raise_for_status()
        user = response.json()
        print(f"Successfully removed admin status from {user['email']}")
    except requests.exceptions.RequestException as e:
        print(f"Error removing admin: {e}")


def reset_user_quota(email: str) -> None:
    """Reset question quota for a user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/admin/reset-quota",
            params={"email": email},
            headers=get_headers(),
        )
        response.raise_for_status()
        user = response.json()
        print(f"Successfully reset quota for {user['email']}")
    except requests.exceptions.RequestException as e:
        print(f"Error resetting quota: {e}")


def check_user_quota(email: str) -> None:
    """Check question quota for a user."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/check-quota",
            params={"email": email},
            headers=get_headers(),
        )
        response.raise_for_status()
        data = response.json()
        print(f"\nQuota information for {data['email']}:")
        print(f"Questions used: {data['question_count']}/{data['max_quota']}")
        print(f"Quota remaining: {data['quota_remaining']}")
        print(f"Last reset: {data['last_reset']}")
    except requests.exceptions.RequestException as e:
        print(f"Error checking quota: {e}")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="Admin management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check system status
  python admin.py status

  # List all admins (requires admin privileges)
  python admin.py list

  # Add a new admin
  python admin.py add user@example.com

  # Remove an admin
  python admin.py remove admin@example.com

  # Reset user quota
  python admin.py reset-quota user@example.com

  # Check user quota
  python admin.py check-quota user@example.com
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status command (public)
    subparsers.add_parser("status", help="Check system status and admin privileges")

    # List command (admin only)
    subparsers.add_parser(
        "list", help="List all admin users (requires admin privileges)"
    )

    # Add admin command
    add_parser = subparsers.add_parser("add", help="Promote a user to admin")
    add_parser.add_argument("email", help="Email of the user to promote")

    # Remove admin command
    remove_parser = subparsers.add_parser(
        "remove", help="Remove admin status from a user"
    )
    remove_parser.add_argument("email", help="Email of the admin to demote")

    # Reset quota command
    reset_parser = subparsers.add_parser(
        "reset-quota", help="Reset question quota for a user"
    )
    reset_parser.add_argument("email", help="Email of the user whose quota to reset")

    # Check quota command
    check_parser = subparsers.add_parser(
        "check-quota", help="Check question quota for a user"
    )
    check_parser.add_argument("email", help="Email of the user whose quota to check")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Handle status command (public)
    if args.command == "status":
        system_status = check_system_status()
        is_admin = check_admin_status()
        print(f"System status: {system_status.get('status', 'unknown')}")
        print(f"Current user is admin: {is_admin}")
        if not is_admin and is_first_admin():
            print("\nNo admins found. You can add the first admin using:")
            print("python admin.py add your.email@example.com")
        return

    # Special case: Allow adding first admin without requiring admin privileges
    if args.command == "add" and is_first_admin():
        print("No admins found. Adding first admin...")
        add_admin(args.email)
        return

    # Check admin status for all other admin commands
    if not check_admin_status():
        print("Error: You must be an admin to use this command")
        sys.exit(1)

    # Execute the requested command
    if args.command == "list":
        list_admins()
    elif args.command == "add":
        add_admin(args.email)
    elif args.command == "remove":
        remove_admin(args.email)
    elif args.command == "reset-quota":
        reset_user_quota(args.email)
    elif args.command == "check-quota":
        check_user_quota(args.email)


if __name__ == "__main__":
    main()
