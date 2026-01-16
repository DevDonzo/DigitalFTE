#!/usr/bin/env python3
"""Authenticate Gmail with correct scopes - uses environment variables"""
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("🔐 Gmail Authentication")
print("=" * 70)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

token_path = Path.home() / '.gmail_token.json'

# Get credentials from environment
client_id = os.getenv('GMAIL_CLIENT_ID')
client_secret = os.getenv('GMAIL_CLIENT_SECRET')
project_id = os.getenv('GMAIL_PROJECT_ID', 'gmail-watcher')

print(f"\n📂 Using credentials from .env")
print(f"💾 Token will be saved to: {token_path}\n")

if not client_id or not client_secret:
    print("❌ GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET must be set in .env!")
    print("Get these from Google Cloud Console: https://console.cloud.google.com/")
    exit(1)

# Build OAuth config from env vars
client_config = {
    "installed": {
        "client_id": client_id,
        "project_id": project_id,
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": client_secret,
        "redirect_uris": ["http://localhost"]
    }
}

# Start OAuth flow
flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
creds = flow.run_local_server(port=0)

# Save token
with open(token_path, 'w') as f:
    f.write(creds.to_json())

print(f"\n✅ Authentication successful!")
print(f"✅ Token saved to: {token_path}")
print(f"\nYour system can now:")
print(f"  - Read emails (gmail.readonly)")
print(f"  - Send emails (gmail.send)")
