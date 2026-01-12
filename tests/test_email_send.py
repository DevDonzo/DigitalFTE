#!/usr/bin/env python3
"""Test email sending directly"""
import os
import sys
from pathlib import Path

# Add to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'scripts'))

from scripts.orchestrator import VaultHandler

print("=" * 70)
print("🧪 Direct Email Send Test")
print("=" * 70)

vault_path = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
handler = VaultHandler(vault_path)

print(f"\n🔐 Gmail Service Status:")
if handler.gmail_service:
    print("   ✅ Gmail service initialized")
else:
    print("   ❌ Gmail service NOT initialized")
    print("\n💡 Possible issues:")
    print("   1. Gmail token expired or missing")
    print("   2. Token has 'gmail.readonly' scope but needs 'gmail.send'")
    print("   3. Need to re-authenticate")
    sys.exit(1)

# Test sending an email
print(f"\n📧 Testing email send...")
try:
    handler._call_email_mcp(
        to='parachaham@gmail.com',
        subject='Test Email from Orchestrator',
        body='This is a test email from the orchestrator. If you see this, the email system is working!'
    )
    print("   ✅ Email sent successfully!")

    # Check log
    sent_log = Path(vault_path) / 'Logs' / 'emails_sent.jsonl'
    if sent_log.exists():
        import json
        with open(sent_log) as f:
            last_line = f.readlines()[-1]
            result = json.loads(last_line)
            print(f"\n📊 Email details:")
            print(f"   To: {result['to']}")
            print(f"   Subject: {result['subject']}")
            print(f"   Status: {result['status']}")
            print(f"   Message ID: {result.get('message_id', 'unknown')}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
