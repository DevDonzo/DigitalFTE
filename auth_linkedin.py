#!/usr/bin/env python3
"""LinkedIn OAuth 2.0 Authentication"""
import os
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
from urllib.parse import urlparse

def load_env_file(path):
    if not os.path.exists(path):
        return
    with open(path, "r") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key and key not in os.environ:
                os.environ[key] = value.strip().strip('"').strip("'")

# Load .env if present so config can live there.
load_env_file(".env")

def require_env(name):
    value = os.getenv(name)
    if not value:
        print(f"Missing {name}. Set it in your environment or .env.")
    return value

# LinkedIn OAuth Config
CLIENT_ID = require_env("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = require_env("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8080/callback")
# OIDC + Share on LinkedIn
SCOPES = ["openid", "profile", "email", "w_member_social"]

# LinkedIn OAuth endpoints
AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

auth_code = None

class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global auth_code
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)

        if 'code' in params:
            auth_code = params['code'][0]
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"""
                <html><body style="font-family: Arial; text-align: center; padding: 50px;">
                <h1>LinkedIn Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>
            """)
        elif 'error' in params:
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            error = params.get('error_description', params.get('error', ['Unknown error']))[0]
            self.wfile.write(f"<html><body><h1>Error: {error}</h1></body></html>".encode())

    def log_message(self, format, *args):
        pass  # Suppress logging

def get_auth_url():
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "digitalfte_linkedin"
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

def exchange_code_for_token(code):
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=data)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Token exchange failed: {response.status_code}")
        print(response.text)
        return None

def save_token(token_data):
    token_path = os.path.expanduser("~/.linkedin_token.json")
    with open(token_path, 'w') as f:
        json.dump(token_data, f, indent=2)
    print(f"\nToken saved to: {token_path}")
    return token_path

def test_token(access_token):
    """Test the token by fetching OIDC profile"""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    # OpenID Connect userinfo endpoint
    response = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    if response.status_code == 200:
        return response.json()

    return None

def main():
    global auth_code

    print("=" * 50)
    print("LinkedIn OAuth 2.0 Authentication")
    print("=" * 50)

    if not CLIENT_ID or not CLIENT_SECRET:
        return None

    # Build auth URL
    auth_url = get_auth_url()

    print(f"\nOpening browser for LinkedIn authorization...")
    print(f"\nIf browser doesn't open, visit:\n{auth_url}\n")

    webbrowser.open(auth_url)

    # Start local server to catch callback
    redirect = urlparse(REDIRECT_URI)
    host = redirect.hostname or "localhost"
    port = redirect.port or 8080
    print(f"Waiting for authorization callback on {REDIRECT_URI} ...")
    server = HTTPServer((host, port), CallbackHandler)

    while auth_code is None:
        server.handle_request()

    print(f"\nReceived authorization code!")

    # Exchange code for token
    print("Exchanging code for access token...")
    token_data = exchange_code_for_token(auth_code)

    if token_data:
        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 0)

        print(f"\nAccess Token obtained!")
        print(f"  Expires in: {expires_in // 86400} days")

        # Test the token
        profile = test_token(access_token)
        if profile:
            name = profile.get("name", profile.get("localizedFirstName", "Unknown"))
            print(f"  Connected as: {name}")

        # Save token
        save_token(token_data)

        # Print for .env
        print("\n" + "=" * 50)
        print("Add this to your .env file:")
        print("=" * 50)
        print(f"\nLINKEDIN_ACCESS_TOKEN={access_token}")

        return access_token
    else:
        print("Failed to get access token")
        return None

if __name__ == "__main__":
    main()
