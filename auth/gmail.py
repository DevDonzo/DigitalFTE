#!/usr/bin/env python3
"""Authenticate Gmail with correct scopes"""
import os
from pathlib import Path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

print("=" * 70)
print("🔐 Gmail Authentication")
print("=" * 70)

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]

project_root = Path(__file__).resolve().parents[1]
creds_path = Path(os.getenv('GMAIL_CREDENTIALS_PATH', project_root / 'credentials.json'))
token_path = Path.home() / '.gmail_token.json'

print(f"\n📂 Credentials file: {creds_path}")
print(f"💾 Token will be saved to: {token_path}\n")

if not creds_path.exists():
    print(f"❌ {creds_path} not found!")
    exit(1)

# Start OAuth flow
flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
creds = flow.run_local_server(port=0)

# Save token
with open(token_path, 'w') as f:
    f.write(creds.to_json())

print(f"\n✅ Authentication successful!")
print(f"✅ Token saved to: {token_path}")
print(f"\nYour system can now:")
print(f"  - Read emails (gmail.readonly)")
print(f"  - Send emails (gmail.send)")
