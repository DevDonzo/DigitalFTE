#!/usr/bin/env python3
"""Test Orchestrator - Verify email sending works"""
import os
import sys
import time
import subprocess
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
vault = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
approved = vault / 'Approved'
done = vault / 'Done'

print("=" * 70)
print("🤖 Testing Orchestrator Email Execution")
print("=" * 70)

# Check if email exists in Approved
email_files = list(approved.glob('EMAIL_*.md'))
if not email_files:
    print("❌ No email files in /Approved/")
    sys.exit(1)

email_file = email_files[0]
print(f"📧 Found email: {email_file.name}")
print(f"   Current location: /Approved/{email_file.name}\n")

# Start orchestrator in background
print("🚀 Starting Orchestrator...")
process = subprocess.Popen(
    [sys.executable, 'scripts/orchestrator.py'],
    cwd=str(project_root),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True
)

# Wait for orchestrator to process
print("⏳ Waiting for orchestrator to process email...")
time.sleep(5)

# Check if email was moved to Done
done_files = list(done.glob('EMAIL_*.md'))

if done_files:
    print(f"\n✅ SUCCESS! Email moved to /Done/")
    print(f"   File: {done_files[0].name}\n")

    # Check sent emails log
    sent_log = vault / 'Logs' / 'emails_sent.jsonl'
    if sent_log.exists():
        with open(sent_log) as f:
            lines = f.readlines()
            if lines:
                import json
                last_sent = json.loads(lines[-1])
                print(f"📧 Email sent to: {last_sent.get('to')}")
                print(f"   Subject: {last_sent.get('subject')}")
                print(f"   Status: {last_sent.get('status')}")
                print(f"   Message ID: {last_sent.get('message_id')}\n")
else:
    print(f"❌ Email NOT moved to /Done/")
    print(f"   Still in: /Approved/{email_file.name}\n")

# Kill orchestrator
process.terminate()
process.wait(timeout=2)

print("=" * 70)
print("Test Complete!")
print("=" * 70)
