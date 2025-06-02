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
from typing import Dict, Optional
import webbrowser
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.parse
import time
from tabulate import tabulate

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
        user = response.json()
        print(f"\nQuota for {user['email']}:")
        print(f"Questions asked today: {user['question_count']}")
        print(f"Last reset: {user['last_question_reset']}")
    except requests.exceptions.RequestException as e:
        print(f"Error checking quota: {e}")


def list_messages(
    limit: int = 100,
    offset: int = 0,
    user: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    json_output: bool = False,
) -> None:
    """List Q&A pairs with optional filtering."""
    try:
        params = {
            "limit": limit,
            "offset": offset,
        }
        if user:
            params["user_id"] = user
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = requests.get(
            f"{API_BASE_URL}/admin/messages",
            params=params,
            headers=get_headers(),
        )
        response.raise_for_status()
        messages = response.json()

        if json_output:
            print(json.dumps(messages, indent=2))
        else:
            if not messages:
                print("No messages found.")
                return

            table_data = []
            for msg in messages:
                table_data.append(
                    [
                        msg["question_timestamp"],
                        msg["user_email"],
                        (
                            msg["question"][:50] + "..."
                            if len(msg["question"]) > 50
                            else msg["question"]
                        ),
                        (
                            msg["answer"][:50] + "..."
                            if len(msg["answer"]) > 50
                            else msg["answer"]
                        ),
                        f"{msg['response_time']:.2f}s",
                    ]
                )
            print(
                tabulate(
                    table_data,
                    headers=[
                        "Timestamp",
                        "User",
                        "Question",
                        "Answer",
                        "Response Time",
                    ],
                    tablefmt="grid",
                )
            )
    except requests.exceptions.RequestException as e:
        print(f"Error listing messages: {e}")


def search_messages(
    text: str,
    fuzzy: bool = False,
    limit: int = 100,
    offset: int = 0,
    user: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    json_output: bool = False,
) -> None:
    """Search Q&A pairs by text with optional filtering."""
    try:
        params = {
            "text": text,
            "fuzzy": fuzzy,
            "limit": limit,
            "offset": offset,
        }
        if user:
            params["user_id"] = user
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = requests.get(
            f"{API_BASE_URL}/admin/messages/search",
            params=params,
            headers=get_headers(),
        )
        response.raise_for_status()
        messages = response.json()

        if json_output:
            print(json.dumps(messages, indent=2))
        else:
            if not messages:
                print("No messages found.")
                return

            table_data = []
            for msg in messages:
                table_data.append(
                    [
                        msg["question_timestamp"],
                        msg["user_email"],
                        (
                            msg["question"][:50] + "..."
                            if len(msg["question"]) > 50
                            else msg["question"]
                        ),
                        (
                            msg["answer"][:50] + "..."
                            if len(msg["answer"]) > 50
                            else msg["answer"]
                        ),
                        f"{msg['response_time']:.2f}s",
                    ]
                )
            print(
                tabulate(
                    table_data,
                    headers=[
                        "Timestamp",
                        "User",
                        "Question",
                        "Answer",
                        "Response Time",
                    ],
                    tablefmt="grid",
                )
            )
    except requests.exceptions.RequestException as e:
        print(f"Error searching messages: {e}")


def search_users(
    query: str,
    fuzzy: bool = False,
    limit: int = 100,
    offset: int = 0,
    json_output: bool = False,
) -> None:
    """Search users by email or name."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/admin/users/search",
            params={
                "query": query,
                "fuzzy": fuzzy,
                "limit": limit,
                "offset": offset,
            },
            headers=get_headers(),
        )
        response.raise_for_status()
        users = response.json()

        if json_output:
            print(json.dumps(users, indent=2))
        else:
            if not users:
                print("No users found.")
                return

            table_data = []
            for user in users:
                table_data.append(
                    [
                        user["email"],
                        user["is_admin"],
                        user["question_count"],
                        user["message_count"],
                        user["last_question_reset"],
                    ]
                )
            print(
                tabulate(
                    table_data,
                    headers=[
                        "Email",
                        "Admin",
                        "Questions Today",
                        "Total Messages",
                        "Last Reset",
                    ],
                    tablefmt="grid",
                )
            )
    except requests.exceptions.RequestException as e:
        print(f"Error searching users: {e}")


def get_stats(
    since: Optional[str] = None,
    until: Optional[str] = None,
    limit: int = 10,
    json_output: bool = False,
) -> None:
    """Get message statistics."""
    try:
        params = {
            "limit": limit,
        }
        if since:
            params["since"] = since
        if until:
            params["until"] = until

        response = requests.get(
            f"{API_BASE_URL}/admin/stats",
            params=params,
            headers=get_headers(),
        )
        response.raise_for_status()
        stats = response.json()

        if json_output:
            print(json.dumps(stats, indent=2))
        else:
            # Top questions
            print("\nTop Questions:")
            if stats["top_questions"]:
                table_data = [
                    [q["question"], q["count"]] for q in stats["top_questions"]
                ]
                print(
                    tabulate(table_data, headers=["Question", "Count"], tablefmt="grid")
                )
            else:
                print("No questions found.")

            # Top answers
            print("\nTop Answers:")
            if stats["top_answers"]:
                table_data = [[a["answer"], a["count"]] for a in stats["top_answers"]]
                print(
                    tabulate(table_data, headers=["Answer", "Count"], tablefmt="grid")
                )
            else:
                print("No answers found.")

            # Top chunks
            print("\nTop Retrieved Chunks:")
            if stats["top_chunks"]:
                table_data = [
                    [c["chunk_text"], c["count"]] for c in stats["top_chunks"]
                ]
                print(tabulate(table_data, headers=["Chunk", "Count"], tablefmt="grid"))
            else:
                print("No chunks found.")

            # Top users
            print("\nTop Users by Questions:")
            if stats["top_users"]:
                table_data = [
                    [u["email"], u["question_count"]] for u in stats["top_users"]
                ]
                print(
                    tabulate(
                        table_data, headers=["User", "Question Count"], tablefmt="grid"
                    )
                )
            else:
                print("No users found.")
    except requests.exceptions.RequestException as e:
        print(f"Error getting stats: {e}")


def dump_db():
    """Dump the database tables as JSON (admin only, if enabled)."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/dump-db", headers=get_headers())
        response.raise_for_status()
        print(json.dumps(response.json(), indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Error dumping DB: {e}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Admin CLI for Metropole")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Check status command
    status_parser = subparsers.add_parser("status", help="Check system status")
    status_parser.add_argument(
        "--admin", action="store_true", help="Check admin status"
    )

    # List admins command
    subparsers.add_parser("list", help="List all admin users")

    # Add admin command
    add_parser = subparsers.add_parser("add", help="Add a new admin user")
    add_parser.add_argument("email", help="Email of the user to promote")

    # Remove admin command
    remove_parser = subparsers.add_parser("remove", help="Remove admin status")
    remove_parser.add_argument("email", help="Email of the user to demote")

    # Reset quota command
    quota_parser = subparsers.add_parser("quota", help="Manage user quotas")
    quota_subparsers = quota_parser.add_subparsers(
        dest="quota_command", help="Quota command"
    )

    reset_quota_parser = quota_subparsers.add_parser("reset", help="Reset user quota")
    reset_quota_parser.add_argument("email", help="Email of the user")

    check_quota_parser = quota_subparsers.add_parser("check", help="Check user quota")
    check_quota_parser.add_argument("email", help="Email of the user")

    # Messages command
    messages_parser = subparsers.add_parser("messages", help="Manage messages")
    messages_subparsers = messages_parser.add_subparsers(
        dest="messages_command", help="Messages command"
    )

    # List messages command
    list_messages_parser = messages_subparsers.add_parser("list", help="List messages")
    list_messages_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of messages to return"
    )
    list_messages_parser.add_argument(
        "--offset", type=int, default=0, help="Offset for pagination"
    )
    list_messages_parser.add_argument("--user", help="Filter by user ID")
    list_messages_parser.add_argument(
        "--since", help="Filter by start date (YYYY-MM-DD)"
    )
    list_messages_parser.add_argument("--until", help="Filter by end date (YYYY-MM-DD)")
    list_messages_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # Search messages command
    search_messages_parser = messages_subparsers.add_parser(
        "search", help="Search messages"
    )
    search_messages_parser.add_argument(
        "--text", required=True, help="Text to search for"
    )
    search_messages_parser.add_argument(
        "--fuzzy", action="store_true", help="Use fuzzy search"
    )
    search_messages_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of messages to return"
    )
    search_messages_parser.add_argument(
        "--offset", type=int, default=0, help="Offset for pagination"
    )
    search_messages_parser.add_argument("--user", help="Filter by user ID")
    search_messages_parser.add_argument(
        "--since", help="Filter by start date (YYYY-MM-DD)"
    )
    search_messages_parser.add_argument(
        "--until", help="Filter by end date (YYYY-MM-DD)"
    )
    search_messages_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # Users command
    users_parser = subparsers.add_parser("users", help="Manage users")
    users_subparsers = users_parser.add_subparsers(
        dest="users_command", help="Users command"
    )

    # Search users command
    search_users_parser = users_subparsers.add_parser("search", help="Search users")
    search_users_parser.add_argument("--query", required=True, help="Search query")
    search_users_parser.add_argument(
        "--fuzzy", action="store_true", help="Use fuzzy search"
    )
    search_users_parser.add_argument(
        "--limit", type=int, default=100, help="Maximum number of users to return"
    )
    search_users_parser.add_argument(
        "--offset", type=int, default=0, help="Offset for pagination"
    )
    search_users_parser.add_argument(
        "--json", action="store_true", help="Output as JSON"
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="View statistics")
    stats_parser.add_argument("--since", help="Filter by start date (YYYY-MM-DD)")
    stats_parser.add_argument("--until", help="Filter by end date (YYYY-MM-DD)")
    stats_parser.add_argument(
        "--limit", type=int, default=10, help="Maximum number of items to return"
    )
    stats_parser.add_argument("--json", action="store_true", help="Output as JSON")

    # Dump DB command
    subparsers.add_parser("dump-db", help="Dump the database (admin only, if enabled)")

    args = parser.parse_args()

    if args.command == "status":
        if args.admin:
            if check_admin_status():
                print("You are an admin.")
            else:
                print("You are not an admin.")
        else:
            status = check_system_status()
            print(f"System status: {status['status']}")
            if status["system"]["has_admins"]:
                print(f"Number of admins: {status['system']['admin_count']}")
            else:
                print("No admins exist yet.")

    elif args.command == "list":
        list_admins()

    elif args.command == "add":
        add_admin(args.email)

    elif args.command == "remove":
        remove_admin(args.email)

    elif args.command == "quota":
        if args.quota_command == "reset":
            reset_user_quota(args.email)
        elif args.quota_command == "check":
            check_user_quota(args.email)
        else:
            quota_parser.print_help()

    elif args.command == "messages":
        if args.messages_command == "list":
            list_messages(
                limit=args.limit,
                offset=args.offset,
                user=args.user,
                since=args.since,
                until=args.until,
                json_output=args.json,
            )
        elif args.messages_command == "search":
            search_messages(
                text=args.text,
                fuzzy=args.fuzzy,
                limit=args.limit,
                offset=args.offset,
                user=args.user,
                since=args.since,
                until=args.until,
                json_output=args.json,
            )
        else:
            messages_parser.print_help()

    elif args.command == "users":
        if args.users_command == "search":
            search_users(
                query=args.query,
                fuzzy=args.fuzzy,
                limit=args.limit,
                offset=args.offset,
                json_output=args.json,
            )
        else:
            users_parser.print_help()

    elif args.command == "stats":
        get_stats(
            since=args.since,
            until=args.until,
            limit=args.limit,
            json_output=args.json,
        )

    elif args.command == "dump-db":
        dump_db()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
