# Google Gemini API Setup for DigitalFTE

**Email Drafting Engine**: Google Gemini 2.0 Flash

Your DigitalFTE system now uses **Google Gemini** to intelligently draft email responses!

---

## Getting Your Gemini API Key (2 minutes)

### Step 1: Go to Google AI Studio
Visit: https://aistudio.google.com/apikey

### Step 2: Create API Key
- Click "Create API Key"
- Select "Create API key in new project"
- Copy the API key (looks like: `AIzaSyD...`)

### Step 3: Add to DigitalFTE
```bash
# Open .env file
nano .env

# Find this line:
GOOGLE_API_KEY=your_gemini_api_key_here

# Replace with your actual key:
GOOGLE_API_KEY=AIzaSyD...

# Save and exit (Ctrl+X, then Y, then Enter)
```

### Step 4: Test It
```bash
python utils/email_drafter.py vault/Inbox/TEST_EMAIL_001.md
```

If successful, you'll see:
```
✓ Google Gemini initialized (gemini-2.0-flash)
✓ Draft generated via Google Gemini API
```

---

## Install the SDK

The system automatically installs the Gemini SDK, but you can manually install it:

```bash
pip install google-genai
```

---

## How It Works

When an email arrives in your inbox:

1. **Gmail Watcher** detects it
   - Creates: `vault/Inbox/EMAIL_*.md`

2. **Orchestrator** triggers Email Drafter
   - Detects email type

3. **Gemini API** generates response
   - Reads email content
   - Checks your Company_Handbook.md rules
   - Drafts professional, contextual reply
   - Includes reasoning explanation

4. **Draft created** in `vault/Pending_Approval/`
   - Shows original email
   - Shows Gemini's analysis
   - Shows proposed response
   - Shows auto-approve status

5. **Human reviews** (5-30 seconds)
   - For known contacts: Just move file to `/Approved/`
   - For new contacts: Review, optionally edit, then move to `/Approved/`

6. **Email sent**
   - Via Gmail API
   - Includes AI disclosure
   - Logged to audit trail

---

## Gemini Model Used

**Model**: `gemini-2.0-flash`
- Latest and fastest Gemini model
- ~1-2 second response time
- High quality reasoning
- Best for email drafting

---

## Features

✅ **Intelligent Classification**
- Understands email intent (inquiry, complaint, invoice, meeting, etc.)
- Applies business rules from Company_Handbook.md
- Auto-approval for known contacts
- Requires approval for sensitive emails

✅ **Context-Aware Responses**
- Reads entire email
- Understands tone and intent
- Generates appropriate professional response
- Matches your business voice

✅ **Safety & Compliance**
- Every email includes AI disclosure
- Confidence scoring (0-1)
- Complete audit trail
- Human review required for approvals

✅ **Speed**
- Drafts generated in 1-2 seconds
- Fallback to templates if API fails
- System continues operating even if API unavailable

---

## Pricing

Google Gemini API has a **free tier**:
- 15 API calls per minute
- Limited to Gemini 1.5 Flash and Gemini 2.0 Flash models
- Perfect for email drafting

For production use with higher volume, see: https://ai.google.dev/pricing

---

## Troubleshooting

### Issue: "GOOGLE_API_KEY not set"
**Fix**:
```bash
export GOOGLE_API_KEY="AIzaSyD..."
echo 'export GOOGLE_API_KEY="AIzaSyD..."' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "google-genai not installed"
**Fix**:
```bash
pip install google-genai
```

### Issue: Gemini returns errors
**Note**: Falls back to template responses automatically
- System still works
- Uses professional template response
- You'll see warning in logs

### Issue: API quota exceeded
**Fix**: Wait until next minute (15 calls/min limit on free tier)

---

## Example: Email from Boss

```
Email: "Can you confirm attendance at Q1 review meeting tomorrow?"
From: boss@company.com

Gemini's Analysis:
├─ Type: meeting_request
├─ Sender: Known contact (boss)
├─ Auto-approve: YES
└─ Confidence: 95%

Gemini's Draft:
"Hi,

Thank you for the reminder. I confirm my attendance for the quarterly
review meeting tomorrow at 2 PM in the main conference room.

Looking forward to discussing Q4 results and Q1 planning.

Best regards"

Status: Ready for approval (takes 5 seconds)
```

---

## Alternative: Use Claude Instead

If you prefer Claude (Anthropic API):
1. Get API key from https://console.anthropic.com/
2. Update `.env`: `ANTHROPIC_API_KEY=sk-ant-...`
3. The system will automatically use Claude instead

Both work seamlessly with DigitalFTE!

---

## Documentation

- **This file**: `GEMINI_SETUP.md` - Setup instructions
- **Full system docs**: `CLAUDE_EMAIL_DRAFTING_SYSTEM.md` (same system, now with Gemini)
- **Architecture**: `ARCHITECTURE.md`
- **Complete guide**: `COMPLETE_SUMMARY.txt`

---

## Next Steps

1. ✅ Get Gemini API key (2 min)
2. ✅ Add to .env (1 min)
3. ✅ Test it (optional, <1 min)
4. ✅ Launch system

```bash
export GOOGLE_API_KEY="your_key_here"
python scripts/orchestrator.py &
python watchers/gmail_watcher.py &
```

Your AI Employee now has intelligent email reasoning! 🚀
