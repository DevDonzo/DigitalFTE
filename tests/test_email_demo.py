#!/usr/bin/env python3
"""Email System Demo - Shows how email integration works"""
import json
from pathlib import Path
from datetime import datetime

# Demo: Simulate what the Email MCP server does

print("=" * 60)
print("📧 DigitalFTE Email System Demo")
print("=" * 60)

print("\n🔧 Email MCP Server Capabilities:\n")

# Tool 1: Send Email
print("1️⃣  send_email")
print("   Sends an email via Gmail API")
demo_send = {
    "to": "recipient@company.com",
    "subject": "Action Required: Invoice #12345",
    "body": "Please approve this invoice for processing...",
    "cc": ["finance@company.com"],
}
print(f"   Example: {json.dumps(demo_send, indent=6)}\n")

# Tool 2: Get Emails
print("2️⃣  get_emails")
print("   Reads emails matching Gmail query")
demo_get = {
    "query": "is:unread from:boss@company.com",
    "limit": 10,
    "fields": ["id", "subject", "from", "body"]
}
print(f"   Example: {json.dumps(demo_get, indent=6)}\n")

# Tool 3: Mark Read
print("3️⃣  mark_read")
print("   Marks an email as read")
print("   Example: message_id='18c9a9f8b9c2d4e1'\n")

# Tool 4: Add Label
print("4️⃣  add_label")
print("   Adds a Gmail label to an email")
print("   Example: message_id='18c9a9f8b9c2d4e1', label='Action Required'\n")

# Workflow demo
print("=" * 60)
print("📋 Typical Email Workflow:")
print("=" * 60)

workflow = """
Step 1: Gmail Watcher Monitors
  └─> Runs every 120 seconds
  └─> Checks for unread + important emails
  └─> Detects new emails from boss, clients, etc.

Step 2: Create Action File
  └─> Creates file in /Needs_Action: EMAIL_{message_id}.md
  └─> Example content:
      ---
      type: email
      from: boss@company.com
      subject: Invoice approval needed
      status: pending
      ---

      Please review invoice #12345
      Amount: $50,000

      Actions:
      - [ ] Reply
      - [ ] Forward
      - [ ] Archive

Step 3: Human Reviews
  └─> You check /Needs_Action/EMAIL_*.md files
  └─> Decide: Approve, Reject, or Forward

Step 4: Email MCP Server Executes
  └─> If you reply with action → send_email() called
  └─> Email sent back to original sender
  └─> Action logged to /Done/EMAIL_*.md

Step 5: Audit Log
  └─> All emails logged in /Logs/audit_YYYYMMDD.json
  └─> 90-day retention for compliance
"""

print(workflow)

print("=" * 60)
print("🎯 What You Can Do Now:")
print("=" * 60)
print("""
1. Gmail watcher reads your inbox automatically
2. Important emails appear as action files in /Needs_Action
3. You edit files to approve/reply
4. Email MCP executes send_email to reply
5. Everything logged for audit

✅ System is ready to go!
""")

# Create a demo action file
demo_action = f"""---
type: email
from: demo@example.com
subject: Demo Email Action
received: {datetime.now().isoformat()}
priority: high
status: pending
---

## Subject
Demo Email Action

## Preview
This is a demonstration of how emails are processed.

## Actions
- [ ] Reply with approval
- [ ] Forward to team
- [ ] Archive
"""

project_root = Path(__file__).resolve().parents[1]
inbox_path = project_root / "vault" / "Needs_Action"
demo_file = inbox_path / "EMAIL_DEMO_001.md"
demo_file.write_text(demo_action)

print(f"📝 Created demo action file: {demo_file}")
print(f"   Check {inbox_path}/ to see how email actions look\n")
