#!/usr/bin/env python3
"""Test posting to Facebook/Instagram via Meta Graph API"""
import json
import requests
from pathlib import Path

print("=" * 70)
print("📱 Meta (Facebook/Instagram) Post Test")
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
PAGE_ID = env_vars.get('META_PAGE_ID')
ACCESS_TOKEN = env_vars.get('META_ACCESS_TOKEN')

if not all([PAGE_ID, ACCESS_TOKEN]):
    print("❌ Missing Meta credentials in .env")
    exit(1)

print(f"\n✅ Credentials loaded")
print(f"   Page ID: {PAGE_ID}")
print(f"   Token: {ACCESS_TOKEN[:30]}...\n")

# Facebook Graph API endpoint
url = f"https://graph.instagram.com/{PAGE_ID}/feed"

# Post text
message = "🚀 DigitalFTE: Autonomous AI System Live! Managing emails, business operations, and social media. #AI #Automation"

# Payload
params = {
    'message': message,
    'access_token': ACCESS_TOKEN
}

print(f"📝 Post: {message}\n")
print("📤 Posting to Facebook...\n")

try:
    response = requests.post(url, params=params)
    result = response.json()

    print(f"Status Code: {response.status_code}\n")

    if response.status_code == 200:
        print(f"✅ POSTED TO FACEBOOK SUCCESSFULLY!")
        print(f"   Post ID: {result.get('id')}")
        if 'id' in result:
            print(f"   URL: https://facebook.com/{result['id']}")

    elif 'error' in result:
        error = result['error']
        print(f"❌ Error: {error.get('message')}")
        print(f"   Type: {error.get('type')}")
    else:
        print(f"Response: {json.dumps(result, indent=2)}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
