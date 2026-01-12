#!/usr/bin/env python3
"""Post a tweet using Twitter API v2 with OAuth 1.0a"""
import tweepy
from pathlib import Path

print("=" * 70)
print("🐦 Twitter Post")
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
API_KEY = env_vars.get('TWITTER_API_KEY')
API_SECRET = env_vars.get('TWITTER_API_SECRET')
BEARER_TOKEN = env_vars.get('TWITTER_BEARER_TOKEN')

if not all([API_KEY, API_SECRET, BEARER_TOKEN]):
    print("❌ Missing Twitter credentials in .env")
    exit(1)

print(f"✅ Credentials loaded\n")

# Get user-level tokens
ACCESS_TOKEN = env_vars.get('TWITTER_ACCESS_TOKEN')
ACCESS_TOKEN_SECRET = env_vars.get('TWITTER_ACCESS_TOKEN_SECRET')

if not all([ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
    print("❌ Missing Twitter user access tokens")
    exit(1)

print(f"✅ User access tokens loaded\n")

# Initialize Tweepy client with OAuth 1.0a User Context
client = tweepy.Client(
    consumer_key=API_KEY,
    consumer_secret=API_SECRET,
    access_token=ACCESS_TOKEN,
    access_token_secret=ACCESS_TOKEN_SECRET,
    wait_on_rate_limit=True
)

# Tweet text
tweet_text = "🚀 DigitalFTE System is Live! Autonomous AI employee managing emails, social media, and business operations. #AI #Automation #Innovation"

print(f"📝 Tweet: {tweet_text}\n")
print("📤 Posting to Twitter...\n")

try:
    # Create tweet
    response = client.create_tweet(text=tweet_text)

    print(f"✅ TWEET POSTED SUCCESSFULLY!")
    print(f"   Tweet ID: {response.data['id']}")
    print(f"   URL: https://twitter.com/i/web/status/{response.data['id']}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
