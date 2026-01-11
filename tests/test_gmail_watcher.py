#!/usr/bin/env python3
"""Test Gmail Watcher - Simple test runner"""
import sys
import os
from pathlib import Path

# Add watchers to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'watchers'))

# Now import
from watchers.gmail_watcher import GmailWatcher

print("=" * 70)
print("📧 Gmail Watcher Test - Email Monitoring")
print("=" * 70)

vault_path = str(project_root / 'vault')
creds_path = str(project_root / 'credentials.json')

print(f"\n🔐 Using credentials: {creds_path}")
print(f"📁 Vault path: {vault_path}")

if not Path(creds_path).exists():
    print(f"\n❌ ERROR: {creds_path} not found!")
    sys.exit(1)

print("✅ Credentials found")
print("\n" + "=" * 70)
print("Starting Gmail Watcher - Monitoring your inbox...")
print("=" * 70)
print("""
📋 What to do:
  1. This will authenticate with Gmail (browser will open first time)
  2. Approve the authentication
  3. Watcher will monitor your inbox every 120 seconds
  4. WHILE THIS RUNS: Send yourself an email with 'urgent' in subject
  5. Star the email as IMPORTANT in Gmail
  6. Wait for the watcher to detect it
  7. Press Ctrl+C to stop

🎯 Expected result:
  A new file will appear in /vault/Inbox/EMAIL_*.md
  with your email details ready for action
""")

input("\nPress ENTER to start...")

try:
    watcher = GmailWatcher(vault_path, creds_path)
    watcher.run()
except KeyboardInterrupt:
    print("\n\n⏸️  Watcher stopped\n")

    # Check if any emails were found
    inbox = Path(vault_path) / 'Inbox'
    email_files = [f for f in inbox.glob('EMAIL_*.md') if f.stat().st_mtime > 0]

    print("=" * 70)
    print("📊 Results:")
    print("=" * 70)

    if email_files:
        print(f"✅ Found {len(email_files)} email action files:\n")
        for f in sorted(email_files, key=lambda x: x.stat().st_mtime, reverse=True):
            print(f"   📄 {f.name}")
            with open(f) as file:
                content = file.read()
                # Show first few lines
                lines = content.split('\n')[:8]
                for line in lines:
                    if line.strip():
                        print(f"      {line}")
            print()
    else:
        print("⏳ No emails found yet\n")
        print("📝 Tips:")
        print("   1. Make sure email has 'urgent' or similar in subject")
        print("   2. Star the email as IMPORTANT in Gmail")
        print("   3. Run test again - watcher checks every 120 seconds")

    print("=" * 70)
