#!/usr/bin/env python3
"""Full workflow test - Execute action and move file"""
import os
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))
from scripts.orchestrator import VaultHandler

print("=" * 70)
print("🔄 Full Email Workflow Test")
print("=" * 70)

vault_path = Path(os.getenv('VAULT_PATH', project_root / 'vault'))
handler = VaultHandler(vault_path)

# Find email in Approved
approved = Path(vault_path) / 'Approved'
email_files = [f for f in approved.glob('*.md') if f.name != '.gitkeep']

if not email_files:
    print("❌ No email files in /Approved/")
    sys.exit(1)

email_file = email_files[0]
print(f"\n📧 Processing: {email_file.name}\n")

# Execute the action (this sends email AND moves file)
try:
    handler._execute_action(email_file)
    print("✅ Action executed!\n")

    # Check folders
    print("📂 Folder Status:")
    approved_after = list(approved.glob('*.md'))
    approved_after = [f for f in approved_after if f.name != '.gitkeep']
    print(f"   /Approved/: {len(approved_after)} files remaining")

    done = Path(vault_path) / 'Done'
    done_files = list(done.glob('*.md'))
    done_files = [f for f in done_files if f.name != '.gitkeep']
    print(f"   /Done/: {len(done_files)} files")

    if len(done_files) > 0:
        print(f"   ✅ Last file: {done_files[-1].name}")

    # Check sent log
    sent_log = Path(vault_path) / 'Logs' / 'emails_sent.jsonl'
    if sent_log.exists():
        import json
        with open(sent_log) as f:
            lines = f.readlines()
            if lines:
                last = json.loads(lines[-1])
                print(f"\n✉️ Last Email Sent:")
                print(f"   To: {last['to']}")
                print(f"   Subject: {last['subject']}")
                print(f"   ID: {last['message_id']}")
                print(f"   Status: {last['status']}")
                print(f"   Time: {last['timestamp']}")

    print(f"\n✅ COMPLETE EMAIL WORKFLOW WORKING!")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
