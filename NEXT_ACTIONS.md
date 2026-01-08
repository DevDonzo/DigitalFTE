# Next Actions - Phase 5 Account Setup

**Priority**: URGENT (Unblocks Phase 6-12)
**Timeline**: 1-2 hours
**Blocking**: All external integrations

---

## Action Items (In Order)

### 1. Gmail API (Priority 1 - Email Foundation)

**Why**: Gmail watcher is already coded and waiting

**Steps**:
```
1. Go to https://console.cloud.google.com/
2. Create project "DigitalFTE"
3. Search "Gmail API" → Enable
4. Credentials → Create OAuth (Desktop app)
5. Download JSON file
6. Save to: /Users/hparacha/DigitalFTE/credentials.json
7. Update .env: GMAIL_CREDENTIALS_PATH=/Users/hparacha/DigitalFTE/credentials.json
8. Test: python watchers/gmail_watcher.py
   - Browser will open
   - Click "Allow"
   - Should create vault/Inbox/EMAIL_*.md files
```

**Time**: ~15 minutes
**Blockers**: None

---

### 2. Xero Account (Priority 2 - Accounting)

**Why**: CEO briefing + accounting integration depends on this

**Steps**:
```
1. Go to https://www.xero.com/signup/
2. Create free account
3. Confirm email, create organization
4. Link bank account (can use test account)
5. Go to https://developer.xero.com/
6. Create new app
7. Name: "DigitalFTE"
8. Redirect URI: http://localhost:8080/callback
9. Save credentials to .env:
   XERO_CLIENT_ID=your_id
   XERO_CLIENT_SECRET=your_secret
   XERO_REDIRECT_URI=http://localhost:8080/callback
```

**Time**: ~20 minutes
**Blockers**: None (Xero approval sometimes takes time, but you'll get access immediately)

---

### 3. Meta Business Account (Priority 3 - Social)

**Why**: Post to Facebook/Instagram

**Steps**:
```
1. Go to https://business.facebook.com/
2. Log in or create account
3. Create Business Account
4. Create Facebook Page (for your business)
5. Create Instagram Professional Account
6. Go to https://developers.facebook.com/
7. Create app (type: Business)
8. Add products: Facebook Login + Instagram Basic Display
9. Tools → Graph API Explorer
10. Generate access token → Save as FACEBOOK_ACCESS_TOKEN
11. Get Instagram Account ID from Business Settings
12. Save to .env:
    FACEBOOK_ACCESS_TOKEN=token
    INSTAGRAM_BUSINESS_ACCOUNT_ID=id
```

**Time**: ~15 minutes
**Blockers**: Meta can take 24h to approve new business accounts (you might get access immediately)

---

### 4. Twitter/X Developer Account (Priority 4 - Social)

**Why**: Post tweets programmatically

**Steps**:
```
1. Go to https://developer.twitter.com/
2. Click "Create account" or login
3. Apply for developer access
4. Select use case
5. Twitter may ask questions (approval usually instant, sometimes 24h)
6. Once approved:
7. Go to Projects & Apps → Create App
8. Name: "DigitalFTE"
9. Keys & tokens → Copy:
   - API Key
   - API Secret Key
   - Bearer Token
10. Save to .env:
    TWITTER_API_KEY=key
    TWITTER_API_SECRET=secret
    TWITTER_BEARER_TOKEN=token
```

**Time**: ~10 minutes + approval time
**Blockers**: Twitter approval can take 24-48 hours (apply now even if not urgent)

---

### 5. WhatsApp Web Session (Priority 5 - Messaging)

**Why**: Monitor WhatsApp for keywords

**Steps**:
```
1. Run: python watchers/whatsapp_watcher.py
2. Browser window opens showing QR code
3. Open WhatsApp on phone
4. Settings → Linked Devices → Link Device
5. Scan QR code with phone camera
6. Browser will authenticate
7. Session saved locally
8. Test: Send message with "urgent" keyword
   Check: vault/Inbox/WHATSAPP_*.md created
```

**Time**: ~5 minutes
**Blockers**: Need WhatsApp on phone, need active device

---

### 6. LinkedIn Developer Account (Optional - Silver+)

**Why**: Post to LinkedIn automatically

**Steps**:
```
1. Go to https://www.linkedin.com/developers/
2. Create app
3. Get credentials
4. Save: LINKEDIN_ACCESS_TOKEN to .env
5. Implement: watchers/linkedin_watcher.py (stub ready)
6. Test
```

**Time**: ~15 minutes
**Blockers**: None (can skip for MVP)

---

## Verification Checklist

After completing account setup:

```bash
# 1. Check .env has all credentials
grep -E "GMAIL|XERO|FACEBOOK|TWITTER|LINKEDIN|WHATSAPP" .env

# 2. Test Gmail watcher
python watchers/gmail_watcher.py &
sleep 5
ls -la vault/Inbox/EMAIL_*.md
# Should see files created

# 3. Test FileSystem watcher
python watchers/filesystem_watcher.py &
cp /path/to/testfile.txt ~/Downloads/
ls -la vault/Inbox/FILE_*.md
# Should see files created

# 4. Test CEO Briefing
python scripts/weekly_audit.py
ls -la vault/Briefings/
# Should see briefing generated

# 5. Run orchestrator
python scripts/orchestrator.py &
# Should see: "Orchestrator started"

# 6. Check logs
cat vault/Logs/*.json | head -n 5
# Should see audit entries
```

---

## Timeline

- **Gmail**: 15 min
- **Xero**: 20 min
- **Meta**: 15 min
- **Twitter**: 10 min + approval (apply now)
- **WhatsApp**: 5 min
- **LinkedIn**: Optional

**Total Active Time**: ~65 minutes
**Waiting Time**: ~24-48 hours for Twitter/LinkedIn approval

---

## After Completion

1. ✅ Test each watcher individually
2. ✅ Test full orchestrator workflow
3. ✅ Check vault/Logs/ for audit trail
4. ✅ Generate first CEO briefing
5. ✅ Move to Phase 6: Testing & Polish

---

## Stuck?

| Error | Fix |
|-------|-----|
| "credentials.json not found" | Download from Google Cloud Console |
| "OAuth error 400" | Check redirect URI matches exactly |
| "403 Forbidden" | Check permissions in Meta/Twitter settings |
| "WhatsApp QR doesn't work" | Try different browser, clear cookies |
| "Xero API 401" | Refresh credentials, check Client ID/Secret |
| "Rate limit 429" | Wait 15 minutes, reduce check_interval |

---

## Expected Outcome

After Phase 5:
- ✅ All 6 external systems connected
- ✅ All watchers actively monitoring
- ✅ Orchestrator coordinating everything
- ✅ CEO briefing generating automatically
- ✅ Audit logs recording all actions
- ✅ HITL workflow functioning
- ✅ Ready for Phase 6 testing

---

**Status**: Phase 4-5 COMPLETE
**Next Action**: Follow steps above in order
**Estimated Time**: 1-2 hours + waiting time
**Blocker**: Twitter approval (apply now)

