# Credentials Setup Guide

**Status**: ✅ All code is complete and tested. Just add these 2 credentials to get running.

---

## Priority 1: Xero (Accounting) - HIGH PRIORITY

### Why it's needed
Enables autonomous invoicing and expense tracking in Xero accounting system.

### Steps to Get Credentials

**Step 1: Create Xero Account**
- Go to https://www.xero.com/signup/
- Create free organization
- Set up bank connections (optional but recommended)

**Step 2: Create OAuth App**
- Go to https://developer.xero.com/app/manage
- Click "New App"
- Fill in details:
  - App Name: `DigitalFTE`
  - Company: Your name
  - Redirect URIs: `http://localhost:8080/callback`
- Click "Create App"

**Step 3: Get Your Credentials**
- You'll see:
  - **Client ID** (copy this)
  - **Client Secret** (copy this)
  - **Tenant ID** (shown when you authorize)

**Step 4: Update .env**
```bash
# Open .env in your editor
nano .env

# Find these lines and update:
XERO_CLIENT_ID=your_client_id_here
XERO_CLIENT_SECRET=your_client_secret_here
XERO_TENANT_ID=your_tenant_id_here
XERO_REDIRECT_URI=http://localhost:8080/callback
```

### Test It
```bash
# Run orchestrator - it will use Xero for any payment/invoice actions
python scripts/orchestrator.py
```

---

## Priority 2: WhatsApp (Monitoring) - SECONDARY

### Why it's needed
Enables monitoring incoming WhatsApp messages for urgent keywords (invoice, payment, help, etc.)

### Steps to Get WhatsApp Access

**Step 1: Install Browser**
```bash
pip install playwright
playwright install chromium
```

**Step 2: Create Session**
```bash
# First run will open WhatsApp Web
python watchers/whatsapp_watcher.py

# In the browser that opens:
# 1. Scan QR code with your phone
# 2. Approve access on your phone
# 3. Browser will save session
```

**Step 3: Update .env**
```bash
nano .env

# Update this line (should be automatic):
WHATSAPP_SESSION_PATH=/Users/hparacha/.whatsapp_session

# Optional - customize keywords:
WHATSAPP_KEYWORDS=urgent,asap,invoice,payment,help
```

### Test It
```bash
# Run watcher - it will scan WhatsApp every 30 seconds
python watchers/whatsapp_watcher.py
```

---

## Optional: Other Credentials (Gmail Already Set Up)

### Twitter/X
- Get API keys: https://developer.twitter.com/en/portal/dashboard
- Add to `.env`:
```bash
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_BEARER_TOKEN=your_bearer_token
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_secret
```

### Facebook/Instagram
- Create app: https://developers.facebook.com/
- Get access token and page ID
- Add to `.env`:
```bash
FACEBOOK_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ACCOUNT_ID=your_account_id
META_PAGE_ID=your_page_id
META_ACCESS_TOKEN=your_token
```

### LinkedIn (Gmail ready, others optional)
- Get OAuth token: https://www.linkedin.com/developers/apps
- Add to `.env`:
```bash
LINKEDIN_ACCESS_TOKEN=your_token
```

---

## Quick Verification

After adding credentials, run:
```bash
# This will verify all your settings are correct
python Setup_Verify.py

# Should show: ✨ VERIFICATION SUMMARY ✨ ... Score: 100%
```

---

## Getting Help

If you get stuck:

1. **Xero authentication fails?**
   - Check Client ID/Secret are exactly correct
   - Verify redirect URI is `http://localhost:8080/callback`
   - Try creating new app if still stuck

2. **WhatsApp scan doesn't work?**
   - Make sure Playwright installed: `pip install playwright`
   - Run: `playwright install chromium`
   - Try again with fresh browser

3. **Watcher not picking up messages?**
   - Check `vault/Logs/` for error messages
   - Verify `.env` file has correct paths
   - Run `python Setup_Verify.py` to validate setup

---

## Timeline to Launch

**Step 1: Xero Setup** (5-10 minutes)
- Sign up, create app, copy credentials
- Update `.env`
- Test

**Step 2: WhatsApp Setup** (3-5 minutes)
- Install Playwright
- Run watcher to get session
- Update `.env`
- Test

**Total: 10-15 minutes to full automation! ⚡**

---

**Once done**:
```bash
# Everything is ready to go!
python scripts/orchestrator.py &
python watchers/gmail_watcher.py &
python scripts/watchdog.py &

# Your AI Employee is now running 24/7 🚀
```
