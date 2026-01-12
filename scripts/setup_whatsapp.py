#!/usr/bin/env python3
"""WhatsApp Setup - Twilio webhook configuration helper"""
import os

print("=" * 60)
print("WhatsApp (Twilio) Setup")
print("=" * 60)
print("\nThis project uses Twilio WhatsApp + webhook ingestion.")
print("No Playwright or WhatsApp Web automation is required.\n")

required = {
    "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
    "TWILIO_AUTH_TOKEN": os.getenv("TWILIO_AUTH_TOKEN"),
    "TWILIO_WHATSAPP_NUMBER": os.getenv("TWILIO_WHATSAPP_NUMBER")
}

missing = [k for k, v in required.items() if not v]
if missing:
    print("Missing environment variables:")
    for key in missing:
        print(f"  - {key}")
else:
    print("Twilio credentials detected.")

print("\nNext steps:")
print("1) Start webhook server:")
print("   python scripts/webhook_server.py")
print("2) Expose locally (ngrok example):")
print("   ngrok http 8000")
print("3) In Twilio Console, set the WhatsApp webhook URL:")
print("   https://<your-ngrok-domain>/webhook")
print("4) Run the watcher to convert inbound messages into Needs_Action:")
print("   python watchers/whatsapp_watcher.py")
print("\nDone.")
print("=" * 60)
