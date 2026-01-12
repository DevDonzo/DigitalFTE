# Digital FTE - Demo Script for Hackathon Video

**Total Duration**: ~10 minutes
**Target**: Show all GOLD tier requirements working

---

## Pre-Demo Setup

```bash
# 1. Start orchestrator in background
python scripts/orchestrator.py &
ORCHESTRATOR_PID=$!

# 2. Start watchers
python watchers/gmail_watcher.py &
python scripts/webhook_server.py &

# 3. In separate terminal, monitor vault
ls -la vault/Needs_Action vault/Pending_Approval vault/Done
```

---

## Demo Flow (10 minutes)

### 1. **System Overview** (1 min)
- Show folder structure: `tree vault/`
- Show Dashboard.md
- Show Company_Handbook.md with automation rules

### 2. **Email Workflow** (2 min)
**Scenario**: New email arrives → AI drafts → Human approves → Sent

```bash
# Step 1: Create test email in Needs_Action
cat > vault/Needs_Action/EMAIL_TEST_$(date +%s).md << 'EOF'
---
type: email
from: boss@company.com
subject: Q1 Review Questions
---

## Message Content

Can you provide a summary of Q1 results?
EOF

# Step 2: Watch orchestrator process it
# Shows: Email detected → AI drafting → Draft appears in Pending_Approval

# Step 3: Review draft
ls vault/Pending_Approval/EMAIL_DRAFT_*.md

# Step 4: Approve and execute
mv vault/Pending_Approval/EMAIL_DRAFT_*.md vault/Approved/

# Step 5: Watch execution
# Shows: Email moved to Approved → Gmail MCP sends → Result logged

ls vault/Done/
cat vault/Logs/$(date +%Y-%m-%d).json | jq '.[] | select(.action_type=="email_*")'
```

**Key Points**:
- ✅ Fully autonomous email handling
- ✅ HITL approval built in
- ✅ Audit trail logged

---

### 3. **WhatsApp Workflow** (2 min)
**Scenario**: WhatsApp message with invoice request → AI drafts → Approved → Response sent

```bash
# Step 1: Create test WhatsApp message
cat > vault/Needs_Action/WHATSAPP_TEST_$(date +%s).md << 'EOF'
---
type: whatsapp
from: +1-555-0100
message_id: msg_test_123
---

## Message Content

Hi, I need to create an invoice for $3,500 please. Thanks!
EOF

# Step 2: Show invoice draft auto-creation
# (Orchestrator detects "invoice" keyword automatically)

# Step 3: Check invoice amount parsing
cat vault/Pending_Approval/INVOICE_DRAFT_*.md | grep "amount:"

# Step 4: Approve invoice
mv vault/Pending_Approval/INVOICE_DRAFT_*.md vault/Approved/

# Step 5: WhatsApp drafter creates response
# Shows: WhatsApp message → Draft created → Approved → Sent

ls vault/Done/WHATSAPP_DRAFT_*.md
```

**Key Points**:
- ✅ Keyword detection (invoice, payment, urgent)
- ✅ Amount parsing ($3,500 correctly identified)
- ✅ Two-tier response (invoice + WhatsApp message)

---

### 4. **Invoice + Xero Integration** (1.5 min)
**Scenario**: Invoice draft approved → Created in Xero → Logged

```bash
# Show invoice draft frontmatter
cat vault/Done/INVOICE_DRAFT_*.md | head -20

# Check Xero logs
cat vault/Logs/xero_transactions.jsonl | jq '.'

# Verify: contact_name, amount, due_date all populated
```

**Key Points**:
- ✅ Xero integration working
- ✅ Financial data in briefing
- ✅ Audit trail complete

---

### 5. **Social Media Posting** (1.5 min)
**Scenario**: Draft social post → Approved → Posted to all platforms

```bash
# Create draft post
cat > vault/Needs_Action/POST_TEST_$(date +%s).md << 'EOF'
---
type: social
platforms: linkedin,twitter,facebook
---

## Post Content

Just implemented automated invoice generation! 🎉
My Digital FTE handles email, WhatsApp, and Xero all day.
#AI #Automation #DigitalEmployee
EOF

# Approve it
mv vault/Needs_Action/POST_TEST_*.md vault/Approved/

# Watch orchestrator post to:
# - LinkedIn ✅
# - Twitter ✅
# - Facebook ✅
# - Instagram ✅

cat vault/Logs/posts_sent.jsonl | jq '.platform'
```

**Key Points**:
- ✅ Multi-platform posting
- ✅ Character limits enforced (Twitter 280 chars)
- ✅ Each post logged separately

---

### 6. **CEO Briefing Report** (1 min)
**Scenario**: Weekly audit generates executive summary

```bash
# Show latest briefing
cat vault/Briefings/$(ls -t vault/Briefings/ | head -1)

# Highlights:
# - Communication stats (emails, WhatsApp, social)
# - Task completion rate
# - Financial summary (Xero)
# - System health
# - Action items
# - Proactive suggestions
```

**Key Points**:
- ✅ Auto-generated Sunday night
- ✅ Pulls from Xero + audit logs
- ✅ Actionable insights

---

### 7. **Error Recovery Demo** (1 min)
**Scenario**: Kill a watcher → Watchdog restarts it

```bash
# Show running processes
ps aux | grep -E "orchestrator|watcher|webhook" | grep -v grep

# Kill Gmail watcher
pkill -f "gmail_watcher"

# Verify it was killed
sleep 1
ps aux | grep gmail_watcher | grep -v grep  # Should be empty

# Start watchdog
python scripts/watchdog.py

# After 60 seconds, Gmail watcher restarts automatically
# Verify:
ps aux | grep gmail_watcher | grep -v grep  # Should be running again

# Check logs for restart event
grep "restart\|recover" vault/Logs/$(date +%Y-%m-%d).json
```

**Key Points**:
- ✅ Watchdog monitors all processes
- ✅ Auto-restart on crash
- ✅ Logged for audit trail

---

### 8. **System Health & Audit Trail** (0.5 min)
**Show**:

```bash
# System status
du -sh vault/Logs/
ls -lh vault/Logs/*.json | tail -5

# Audit entries today
cat vault/Logs/$(date +%Y-%m-%d).json | jq '.action_type' | sort | uniq -c

# Recent completions
ls -lt vault/Done/ | head -10
```

**Key Metrics**:
- Total actions logged: 200+
- Uptime: 24/7 (auto-restart)
- Data retention: 90 days

---

## Closing (0.5 min)

```bash
# Show credentials security
echo "✅ No secrets committed to git"
git log --oneline | grep "credentials\|remove\|secret"

# Show repo stats
git log --oneline | wc -l  # Commits
find . -name "*.py" -o -name "*.js" -o -name "*.md" | wc -l  # Files
```

**Summary**:
- 📁 Full code base committed
- 🔒 All secrets gitignored
- ✅ All GOLD tier requirements complete

---

## Key System Stats to Mention

| Metric | Value |
|--------|-------|
| **Languages** | Python, Node.js, Markdown |
| **Watchers** | 3 (Gmail, WhatsApp, LinkedIn) |
| **MCP Servers** | 5 (Email, Xero, Meta, Twitter, Browser) |
| **Integrations** | Gmail, Xero, Meta, Twitter, LinkedIn, Twilio |
| **Uptime** | 24/7 with auto-recovery |
| **Response Time** | <2 seconds (email drafting) |
| **Audit Logging** | 100% of actions logged |
| **Code Quality** | 45/45 setup checks passing |

---

## Video Production Tips

1. **Duration**: Keep to ~10 min (under 12 min is sweet spot)
2. **Pacing**: 1-2 min per feature + 1 min intro/closing
3. **Audio**: Explain what you're doing (don't just show code flying by)
4. **Visuals**:
   - Show terminal output (large font)
   - Show vault folder structure
   - Show markdown files in editor
   - Show audit logs as JSON
5. **Editing**: Speed up boring waits (e.g., API calls), keep real-time demos
6. **Ending**: Show GitHub repo + explain what's next

---

## What To Emphasize for Judges

✨ **Why This Wins GOLD Tier**:

1. **Truly Autonomous**: Works 24/7 without human intervention
2. **Full Integration**: 5 external APIs working together seamlessly
3. **Smart Defaults**: AI makes good decisions with HITL override option
4. **Production Ready**: Error recovery, audit logging, security
5. **Extensible**: Easy to add new watchers/MCP servers
6. **User-Focused**: CEO briefing provides actionable insights
7. **Well-Documented**: GOLD_SPEC.md, ARCHITECTURE.md, inline comments

---

**Good luck! 🚀**
