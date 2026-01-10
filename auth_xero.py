"""Xero OAuth2 PKCE Authentication"""
import os
import json
import secrets
import hashlib
import base64
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs, urlparse
import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

CLIENT_ID = os.getenv('XERO_CLIENT_ID', '3409CAB7DD274BEFA59B3256F5BAE6F2')
REDIRECT_URI = os.getenv('XERO_REDIRECT_URI', 'http://localhost:8080/callback')
SCOPES = 'openid profile email accounting.transactions accounting.contacts accounting.settings offline_access'
TOKEN_FILE = os.path.expanduser('~/.xero_token.json')

# PKCE helpers
def generate_code_verifier():
    return secrets.token_urlsafe(64)[:128]

def generate_code_challenge(verifier):
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b'=').decode()

class OAuthHandler(BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        if '/callback' in self.path:
            query = parse_qs(urlparse(self.path).query)
            OAuthHandler.code = query.get('code', [None])[0]

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<h1>Success! You can close this window.</h1>')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Suppress logging

def authenticate():
    """Run OAuth2 PKCE flow"""
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Build authorization URL
    auth_params = {
        'response_type': 'code',
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPES,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256',
    }
    auth_url = f"https://login.xero.com/identity/connect/authorize?{urlencode(auth_params)}"

    print(f"\nOpening browser for Xero authorization...")
    print(f"If browser doesn't open, go to:\n{auth_url}\n")
    webbrowser.open(auth_url)

    # Start local server to catch callback
    server = HTTPServer(('localhost', 8080), OAuthHandler)
    print("Waiting for authorization...")

    while OAuthHandler.code is None:
        server.handle_request()

    code = OAuthHandler.code
    print(f"Got authorization code!")

    # Exchange code for tokens
    token_data = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'code_verifier': code_verifier,
    }

    response = requests.post(
        'https://identity.xero.com/connect/token',
        data=token_data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if response.status_code != 200:
        print(f"Error: {response.text}")
        return None

    tokens = response.json()

    # Get tenant ID
    connections = requests.get(
        'https://api.xero.com/connections',
        headers={'Authorization': f"Bearer {tokens['access_token']}"}
    ).json()

    if connections:
        tokens['tenant_id'] = connections[0]['tenantId']
        tokens['tenant_name'] = connections[0].get('tenantName', 'Unknown')
        print(f"\nConnected to: {tokens['tenant_name']}")
        print(f"Tenant ID: {tokens['tenant_id']}")

    # Save tokens
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

    print(f"\nTokens saved to: {TOKEN_FILE}")
    print("Xero authentication complete!")

    return tokens

def get_tokens():
    """Load saved tokens"""
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return json.load(f)
    return None

def refresh_token():
    """Refresh access token"""
    tokens = get_tokens()
    if not tokens or 'refresh_token' not in tokens:
        print("No refresh token available. Run auth first.")
        return None

    response = requests.post(
        'https://identity.xero.com/connect/token',
        data={
            'grant_type': 'refresh_token',
            'client_id': CLIENT_ID,
            'refresh_token': tokens['refresh_token'],
        },
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

    if response.status_code != 200:
        print(f"Refresh error: {response.text}")
        return None

    new_tokens = response.json()
    new_tokens['tenant_id'] = tokens.get('tenant_id')
    new_tokens['tenant_name'] = tokens.get('tenant_name')

    with open(TOKEN_FILE, 'w') as f:
        json.dump(new_tokens, f, indent=2)

    print("Token refreshed!")
    return new_tokens

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'refresh':
        refresh_token()
    else:
        authenticate()
