# Phase 5: External Account Setup

**Status**: READY
**Time Estimate**: 1-2 hours

---

## 1. Gmail API Setup

Go to https://console.cloud.google.com/:
1. Create new project "DigitalFTE"
2. Enable Gmail API
3. Create OAuth credentials (Desktop app)
4. Download credentials.json
5. Set GMAIL_CREDENTIALS_PATH=path/to/credentials.json in .env

Test: python watchers/gmail_watcher.py

---

## 2. Xero Account Setup

Go to https://www.xero.com/signup/:
1. Create free account
2. Register OAuth app at developer.xero.com
3. Get Client ID, Secret, Tenant ID
4. Set in .env: XERO_CLIENT_ID, XERO_CLIENT_SECRET, XERO_TENANT_ID

Test: python mcp_servers/xero_mcp/test.py (when implemented)

---

## 3. Meta Business Setup

Go to https://business.facebook.com/:
1. Create Facebook Page
2. Create Instagram Professional Account
3. Go to https://developers.facebook.com/
4. Register app, get access tokens
5. Set FACEBOOK_ACCESS_TOKEN, INSTAGRAM_BUSINESS_ACCOUNT_ID in .env

Test: curl command to post test image

---

## 4. Twitter/X Setup

Go to https://developer.twitter.com/:
1. Apply for developer account
2. Create app, get API keys
3. Set TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_BEARER_TOKEN in .env

Test: python3 -c "import tweepy; tweepy.Client(bearer_token=TOKEN).create_tweet(text='Test')"

---

## 5. WhatsApp Setup

Run: python watchers/whatsapp_watcher.py
Then: Scan QR code with phone

Test: Send message with "urgent" keyword, check vault/Inbox/

---

## 6. LinkedIn Setup (Optional)

Get access token from LinkedIn Developers
Set LINKEDIN_ACCESS_TOKEN in .env

Test: python watchers/linkedin_watcher.py

---

## Verification

After all setups:

python watchers/gmail_watcher.py &
python watchers/filesystem_watcher.py &
python scripts/orchestrator.py &

Check vault/Inbox/ for new files
Check vault/Logs/ for audit trail
Run: python scripts/weekly_audit.py
Check vault/Briefings/ for generated briefing

---

Ready for Phase 6: Testing & Polish

