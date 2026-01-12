# Credentials Setup Guide

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
XERO_ACCESS_TOKEN=your_access_token_here
XERO_REDIRECT_URI=http://localhost:8080/callback
```

### Test It
```bash
# Run auth flow (saves token to ~/.xero_token.json)
python auth/xero.py

# Run orchestrator - it will use Xero for any payment/invoice actions
python scripts/orchestrator.py
```

---

## Priority 2: WhatsApp (Twilio Webhook) - SECONDARY

### Why it's needed
Enables monitoring incoming WhatsApp messages via Twilio and routing them into the vault.

### Steps to Get WhatsApp Access

**Step 1: Create a Twilio WhatsApp sender**
- Use a Twilio WhatsApp Sandbox or a dedicated WhatsApp-enabled number.
- Note your Account SID, Auth Token, and WhatsApp-enabled number.

**Step 2: Update .env**
```bash
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=+1234567890
```

**Step 3: Start the webhook server**
```bash
python scripts/webhook_server.py
```

**Step 4: Expose locally (ngrok example)**
```bash
ngrok http 8000
```

**Step 5: Set Twilio webhook URL**
- In Twilio Console, set the WhatsApp webhook to:
  `https://<your-ngrok-domain>/webhook`

### Test It
```bash
# Run the watcher to convert inbound messages into Needs_Action files
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

2. **WhatsApp webhook doesn't receive messages?**
   - Confirm your webhook URL is reachable from Twilio.
   - Check `scripts/webhook_server.py` logs for incoming requests.
   - Confirm Twilio is pointing to `/webhook` with POST.

3. **Watcher not picking up messages?**
   - Check `vault/Logs/` for error messages
   - Verify `.env` file has correct paths
   - Run `python Setup_Verify.py` to validate setup

---

## Next Steps

After credentials are configured:

```bash
# Start the system
python scripts/orchestrator.py &
python watchers/gmail_watcher.py &
python scripts/watchdog.py &
```

For production deployment, use launchd configuration in `AUTONOMY_GUIDE.md`.
