#!/usr/bin/env python3
"""Test posting a tweet via Twitter API v2"""
import os
import json
import requests
from datetime import datetime
from pathlib import Path
import re

print("=" * 70)
print("🐦 Twitter Post Test")
print("=" * 70)

# Load .env file
project_root = Path(__file__).resolve().parents[1]
env_path = project_root / '.env'
env_vars = {}
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, val = line.strip().split('=', 1)
                env_vars[key] = val

# Get credentials
BEARER_TOKEN = env_vars.get('TWITTER_BEARER_TOKEN')
if not BEARER_TOKEN:
    print("❌ TWITTER_BEARER_TOKEN not found in .env")
    exit(1)

print(f"\n🔐 Bearer token loaded: {BEARER_TOKEN[:20]}...\n")

# Twitter API v2 endpoint
url = "https://api.twitter.com/2/tweets"

# Tweet text
tweet_text = "🚀 DigitalFTE System is Live! Autonomous AI employee managing emails, social media, and business operations. #AI #Automation #Innovation"

print(f"📝 Tweet: {tweet_text}\n")

# Headers
headers = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "Content-Type": "application/json",
}

# Payload
payload = {
    "text": tweet_text
}

print("📤 Posting to Twitter...\n")

try:
    response = requests.post(url, json=payload, headers=headers)

    print(f"Status Code: {response.status_code}")
    result = response.json()

    if response.status_code == 201:
        print(f"\n✅ TWEET POSTED SUCCESSFULLY!")
        print(f"   Tweet ID: {result['data']['id']}")
        print(f"   URL: https://twitter.com/i/web/status/{result['data']['id']}")
        print(f"   Time: {datetime.now().isoformat()}")

    elif "errors" in result:
        print(f"\n⚠️ Error: {result['errors'][0]['message']}")
    else:
        print(f"\nResponse: {json.dumps(result, indent=2)}")

except Exception as e:
    print(f"❌ Error: {e}")
    exit(1)
