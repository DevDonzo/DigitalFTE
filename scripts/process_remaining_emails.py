#!/usr/bin/env python3
"""Process all remaining emails in Approved"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from scripts.orchestrator import VaultHandler

vault_path = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
handler = VaultHandler(vault_path)
approved = Path(vault_path) / 'Approved'

# Find all emails
emails = [f for f in approved.glob('*.md') if f.name != '.gitkeep' and 'EMAIL' in f.name]

print(f"Found {len(emails)} email(s) to process\n")

for email_file in emails:
    print(f"Processing: {email_file.name}")
    try:
        handler._execute_action(email_file)
        print(f"  ✅ Sent and moved to /Done/\n")
    except Exception as e:
        print(f"  ❌ Error: {e}\n")

# Show final status
done = Path(vault_path) / 'Done'
done_files = [f for f in done.glob('*.md') if 'EMAIL' in f.name]

print("=" * 70)
print(f"✅ FINAL STATUS: {len(done_files)} emails processed")
print("=" * 70)

# Show sent emails log
sent_log = Path(vault_path) / 'Logs' / 'emails_sent.jsonl'
if sent_log.exists():
    import json
    with open(sent_log) as f:
        lines = f.readlines()
        print(f"\n📧 Total emails sent: {len(lines)}")
        if lines:
            print("\n📋 Recent emails:")
            for line in lines[-3:]:
                data = json.loads(line)
                print(f"   • {data['subject']} → {data['to']}")
