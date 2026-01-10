#!/usr/bin/env python3
"""Direct test of orchestrator email execution"""
import sys
from pathlib import Path

sys.path.insert(0, '/Users/hparacha/DigitalFTE')
from scripts.orchestrator import VaultHandler

print("=" * 70)
print("🤖 Direct Orchestrator Email Test")
print("=" * 70)

vault_path = '/Users/hparacha/DigitalFTE/vault'
handler = VaultHandler(vault_path)

# Find email in Approved
approved = Path(vault_path) / 'Approved'
email_files = list(approved.glob('*.md'))

if not email_files:
    print("❌ No email files in /Approved/")
    sys.exit(1)

email_file = email_files[0]
print(f"\n📧 Found: {email_file.name}")

# Read the file
content = email_file.read_text()
print(f"📄 File size: {len(content)} bytes\n")

# Execute the email action
print("🚀 Executing email action...")
try:
    handler._execute_email(email_file, content)
    print("✅ Email executed successfully!")

    # Check if it was logged
    sent_log = Path(vault_path) / 'Logs' / 'emails_sent.jsonl'
    if sent_log.exists():
        import json
        with open(sent_log) as f:
            lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                print(f"\n✅ Email sent to: {last['to']}")
                print(f"   Subject: {last['subject']}")
                print(f"   Message ID: {last['message_id']}")
                print(f"   Status: {last['status']}")

    # Now check if file moved
    if email_file.exists():
        print(f"\n⚠️  File still in /Approved/ (orchestrator should move it)")
        print(f"   Location: {email_file}")
    else:
        done = Path(vault_path) / 'Done' / email_file.name
        if done.exists():
            print(f"\n✅ File moved to /Done/")
        else:
            print(f"\n⚠️ File not found in /Done/")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
