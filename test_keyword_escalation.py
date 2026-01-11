#!/usr/bin/env python3
"""Test keyword-based urgency classification for WhatsApp messages"""

import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

# Test the classify_urgency function
from webhook_server import classify_urgency

print("=" * 70)
print("🧪 KEYWORD ESCALATION TEST")
print("=" * 70)

test_cases = [
    # URGENT messages
    ("Help! The server is down!", "URGENT"),
    ("URGENT: Can you call me ASAP?", "URGENT"),
    ("Emergency - need immediate assistance", "URGENT"),
    ("Critical problem - app is broken", "URGENT"),
    ("The system is down and clients can't access it", "URGENT"),

    # BUSINESS messages
    ("What's your pricing for a Django project?", "BUSINESS"),
    ("Can you send me an invoice?", "BUSINESS"),
    ("I need a quote for your services", "BUSINESS"),
    ("Let's discuss the payment terms", "BUSINESS"),
    ("What's the cost for this feature?", "BUSINESS"),

    # INFO messages
    ("Thanks for the update!", "INFO"),
    ("Sounds good to me", "INFO"),
    ("Yes, I agree with that", "INFO"),
    ("Perfect, that works", "INFO"),
    ("Ok, see you then", "INFO"),

    # NORMAL messages (no keywords)
    ("How's your day going?", "NORMAL"),
    ("Can you review this document?", "NORMAL"),
    ("When is our meeting?", "NORMAL"),
    ("I sent you the files", "NORMAL"),
]

print("\n📊 Test Results:\n")

passed = 0
failed = 0

for message, expected_urgency in test_cases:
    result = classify_urgency(message)
    status = "✅" if result == expected_urgency else "❌"

    if result == expected_urgency:
        passed += 1
    else:
        failed += 1

    print(f"{status} {result:10} | Expected: {expected_urgency:10} | \"{message[:45]}...\"")

print("\n" + "=" * 70)
print(f"📈 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 70)

if failed == 0:
    print("✅ All keyword classification tests passed!")
    sys.exit(0)
else:
    print("❌ Some tests failed")
    sys.exit(1)
