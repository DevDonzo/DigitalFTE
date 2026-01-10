#!/usr/bin/env python3
"""Standalone email sender - No dependencies, just send the email"""
import base64
import json
from email.mime.text import MIMEText
from pathlib import Path
from datetime import datetime

# Gmail API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

print("=" * 70)
print("📧 Email Send - Standalone Test")
print("=" * 70)

# Get Gmail credentials
token_file = Path.home() / '.gmail_token.json'
if not token_file.exists():
    print("❌ Gmail token not found!")
    print("   Need to re-authenticate with correct scopes")
    print("   Run: python3 test_gmail_watcher.py")
    exit(1)

print(f"\n🔐 Loading Gmail credentials...")
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send'
]
creds = Credentials.from_authorized_user_file(token_file, SCOPES)

# Refresh if needed
if creds.expired and creds.refresh_token:
    creds.refresh(Request())

# Build Gmail service
gmail = build('gmail', 'v1', credentials=creds)
print("✅ Gmail service ready")

# Create email
print(f"\n📝 Creating email...")
to = 'parachaham@gmail.com'
subject = 'Test: Email System Works!'
body = '''Thank you for the reminder. I've reviewed invoice P29414 and am processing the payment immediately. The outstanding balance will be settled within 24 hours. I'll send you a confirmation once the transaction is complete.'''

message = MIMEText(body)
message['to'] = to
message['subject'] = subject

# Send
print(f"📤 Sending to: {to}")
try:
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    result = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()

    print(f"✅ Email sent!")
    print(f"   Message ID: {result['id']}")

    # Log it
    vault = Path('/Users/hparacha/DigitalFTE/vault')
    sent_file = vault / 'Logs' / 'emails_sent.jsonl'
    sent_file.parent.mkdir(parents=True, exist_ok=True)

    log_entry = {
        'to': to,
        'subject': subject,
        'body': body[:100] + '...',
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'message_id': result['id'],
        'status': 'sent'
    }

    with open(sent_file, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    print(f"\n✅ WORKING! Email sent successfully via Gmail API")
    print(f"✅ Logged to: {sent_file}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
