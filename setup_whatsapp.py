#!/usr/bin/env python3
"""WhatsApp Setup - Scan QR code to authenticate"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import time

SESSION_PATH = Path.home() / '.whatsapp_session'

print("=" * 50)
print("WhatsApp Web Setup")
print("=" * 50)
print(f"\nSession will be saved to: {SESSION_PATH}")
print("\n1. A browser window will open")
print("2. Scan the QR code with your phone")
print("3. Wait for WhatsApp to load")
print("4. Press Enter in this terminal when ready")
print("=" * 50)

with sync_playwright() as p:
    # Launch browser with persistent context (saves session)
    # Using Firefox because WhatsApp blocks Playwright's Chromium
    browser = p.firefox.launch_persistent_context(
        str(SESSION_PATH),
        headless=False,  # Show browser so user can scan QR
        viewport={'width': 1280, 'height': 800}
    )

    page = browser.pages[0] if browser.pages else browser.new_page()
    page.goto('https://web.whatsapp.com')

    print("\n>>> Browser opened. Scan the QR code with your phone.")
    print(">>> After WhatsApp loads, press Enter here to save session...")

    input("\nPress Enter when WhatsApp is loaded...")

    # Give it a moment to save cookies
    time.sleep(2)

    browser.close()

print("\n" + "=" * 50)
print("Session saved!")
print("You can now run the WhatsApp watcher:")
print("  python3 watchers/whatsapp_watcher.py")
print("=" * 50)
