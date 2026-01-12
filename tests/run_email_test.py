#!/usr/bin/env python3
"""Email Watcher Test - Step by step instructions"""
import subprocess
import sys
from pathlib import Path

print("=" * 70)
print("📧 DigitalFTE Email Watcher Test")
print("=" * 70)

print("""
STEP 1: Start the Gmail Watcher
  └─> This will ask you to authenticate via browser (first time only)
  └─> After that, it monitors your inbox every 120 seconds

STEP 2: Send Yourself an Email
  └─> Open Gmail in browser
  └─> Send an email TO YOURSELF with subject containing: "test" or "urgent"
  └─> Make sure it's marked as IMPORTANT (star it)

STEP 3: Check /Needs_Action/
  └─> Look for EMAIL_*.md files created by the watcher
  └─> These are your action items

Let's start!
""")

input("Press ENTER to start Gmail Watcher authentication...")

project_root = Path(__file__).resolve().parents[1]
vault_path = str(project_root / 'vault')
creds_path = str(project_root / 'credentials.json')

print(f"\n🔐 Using credentials from: {creds_path}")
print(f"📁 Vault path: {vault_path}\n")

# Check credentials exist
if not Path(creds_path).exists():
    print("❌ credentials.json not found!")
    print(f"   Expected: {creds_path}")
    sys.exit(1)

print("✅ Credentials found\n")
print("=" * 70)
print("Starting Gmail Watcher...")
print("=" * 70)
print()

# Run the Gmail watcher from watchers directory to fix imports
import os
project_root = Path(__file__).parent
try:
    subprocess.run(
        [sys.executable, '-c', f"""
import sys
sys.path.insert(0, '{project_root}')
sys.path.insert(0, '{project_root / 'watchers'}')
from gmail_watcher import GmailWatcher

watcher = GmailWatcher('{vault_path}', '{creds_path}')
watcher.run()
"""],
        env={{
            **os.environ,
            'VAULT_PATH': vault_path,
            'GMAIL_CREDENTIALS_PATH': creds_path
        }}
    )
except KeyboardInterrupt:
    print("\n\n⏸️  Gmail Watcher stopped (Ctrl+C)")
    print("\n" + "=" * 70)
    print("Check your /Needs_Action/ folder!")
    print("=" * 70)

    inbox = Path(vault_path) / 'Needs_Action'
    email_files = list(inbox.glob('EMAIL_*.md'))

    if email_files:
        print(f"\n✅ Found {len(email_files)} email action files:\n")
        for f in email_files:
            print(f"   📄 {f.name}")
            print(f"      Path: {f}\n")
    else:
        print("\n⏳ No emails found yet. Try:")
        print("   1. Send yourself an email with 'urgent' in subject")
        print("   2. Star it as IMPORTANT")
        print("   3. Run this script again")
        print("   4. Wait ~2 minutes for watcher to detect it\n")
