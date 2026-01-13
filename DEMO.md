# DigitalFTE - Demo & Running Guide

## Quick Start (2 minutes)

```bash
cd /Users/hparacha/DigitalFTE

# Terminal 1: Main Engine
python scripts/orchestrator.py

# Terminal 2: Email Monitor
python watchers/gmail_watcher.py

# Terminal 3: WhatsApp Webhook + Processing
python scripts/webhook_server.py &
python watchers/whatsapp_watcher.py

# Terminal 4: Health Monitor
python scripts/watchdog.py

# View the vault
open -a Obsidian vault/
```

---

## What Each Script Does

| Script | Location | What It Does | Interval |
|--------|----------|-------------|----------|
| **Orchestrator** | `scripts/orchestrator.py` | Main engine - reads messages, drafts, routes to approval | Real-time |
| **Gmail Watcher** | `watchers/gmail_watcher.py` | Monitors Gmail for unread+important emails | Every 20s |
| **WhatsApp Watcher** | `watchers/whatsapp_watcher.py` | Processes WhatsApp messages from webhook | Every 10s |
| **Webhook Server** | `scripts/webhook_server.py` | Receives WhatsApp messages from Twilio (port 8001) | Real-time |
| **Watchdog** | `scripts/watchdog.py` | Monitors processes, auto-restarts if dead | Every 60s |
| **Weekly Audit** | `scripts/weekly_audit.py` | Generates CEO briefing (Sunday 11 PM) | Weekly |

---

## Minimal Demo (30 seconds)

1. Start orchestrator: `python scripts/orchestrator.py`
2. Start Gmail watcher: `python watchers/gmail_watcher.py`
3. Send yourself a test email
4. Watch flow: `/Needs_Action/` → `/Pending_Approval/` → `/Done/`

---

## Full Demo (20 minutes)

### Setup
```bash
# Start all services (in separate terminals)
python scripts/orchestrator.py
python watchers/gmail_watcher.py
python scripts/webhook_server.py &
python watchers/whatsapp_watcher.py
python scripts/watchdog.py

# Open vault
open -a Obsidian vault/
```

### Show These Features

**1. Architecture (2 min)**
- Watchers → Vault → Orchestrator → MCP Servers
- File-based approval workflow
- HITL (Human-in-the-loop) safeguard

**2. Email Processing (5 min)**
- Send test email
- Show `/Needs_Action/EMAIL_*.md` appears in 2 seconds
- Show `/Pending_Approval/EMAIL_DRAFT_*.md` generated with AI
- Move to `/Approved/` → auto-executes and moves to `/Done/`
- Show audit log: `cat vault/Logs/2026-01-13.json | jq '.[] | select(.action_type=="email_send")'`

**3. WhatsApp Integration (5 min)**
- Send WhatsApp message with "invoice" keyword
- Show webhook receives it on port 8001
- Show file created in `/Needs_Action/`
- Same approval flow as email
- Show in `vault/Logs/whatsapp_sent.jsonl`

**4. CEO Briefing (3 min)**
- Show `vault/Briefings/2026-01-12_briefing.md` (auto-generated)
- Revenue tracking
- Completed tasks
- Bottleneck identification

**5. Error Recovery (3 min)**
- Kill orchestrator: `pkill -f orchestrator.py`
- Show watchdog restarts it within 60 seconds
- Check logs: `tail vault/Logs/watchdog_status.json`

**6. Gold Tier Features (2 min)**
- Show MCP servers: `ls -la mcp_servers/`
- Show Company_Handbook rules
- Show audit logs: `ls -lh vault/Logs/`

---

## What to Show Judges

### Compliance (5 min)
- ✅ Bronze Tier: Dashboard, Handbook, Watchers, Vault structure
- ✅ Silver Tier: Multiple watchers, LinkedIn posting, HITL, MCP server
- ✅ Gold Tier: Xero, Meta, Twitter, CEO briefing, Error recovery, Audit logging

Read: `HACKATHON_COMPLIANCE.md` (maps every feature to spec)

### Architecture (5 min)
Read: `ARCHITECTURE.md`
Show: Vault structure in Obsidian

### Innovation (5 min)
- File-based state machine (more resilient than databases)
- Multi-layer deduplication (prevents duplicate processing)
- Thread-safe batching (no race conditions)
- OpenAI drafting (context-aware responses)
- Local-first (privacy-focused)

---

## Key Files Structure

```
orchestrator.py     → Main engine (1,469 lines, reads/thinks/executes)
watchers/           → Email, WhatsApp, LinkedIn, FileSystem
mcp_servers/        → Email, Twitter, Meta Social, Xero
vault/              → Obsidian vault (local-first memory)
  ├── Needs_Action/     ← Input from watchers
  ├── Pending_Approval/ ← HITL review queue
  ├── Approved/         ← Ready to execute
  └── Done/             ← Completed tasks
```

---

## Scripts Reference

### orchestrator.py
- **Size**: 1,469 lines
- **What**: Main coordination engine
- **Reads**: `/Needs_Action/`, `Company_Handbook.md`, `/Approved/`
- **Writes**: `/Pending_Approval/`, `/Done/`, logs
- **Integrations**: OpenAI (drafting), Email MCP, Twitter MCP, Meta MCP, Xero MCP
- **Thread-safe**: Yes (uses locks for deduplication)

### gmail_watcher.py
- **Interval**: 20 seconds
- **Queries**: Gmail for unread + important emails
- **Creates**: `EMAIL_[id].md` in `/Needs_Action/`
- **Auth**: OAuth 2.0 (credentials.json)
- **Features**: Deduplication, auto-marks as read, truncates to 5000 chars

### whatsapp_watcher.py
- **Interval**: 10 seconds
- **Input**: Messages in `.whatsapp_incoming.json` (from webhook)
- **Creates**: `WHATSAPP_[timestamp].md` in `/Needs_Action/`
- **Features**: Urgency classification, message deduplication
- **Sends via**: Twilio API (when approved)

### webhook_server.py
- **Port**: 8001
- **Purpose**: Receives WhatsApp webhooks from Twilio/Meta
- **Framework**: FastAPI
- **Endpoints**:
  - `GET /health` → status check
  - `POST /webhook` → receive messages
- **Output**: Queues to `.whatsapp_incoming.json`

### watchdog.py
- **Interval**: 60 seconds
- **Monitors**: Orchestrator, all watchers
- **Action**: Auto-restart if process exits non-zero
- **Logs**: `/vault/Logs/watchdog_status.json`

### weekly_audit.py
- **Trigger**: Sunday 11 PM (launchd scheduled)
- **Collects**: Email volume, WhatsApp messages, LinkedIn posts, completed tasks, Xero data
- **Generates**: `/vault/Briefings/YYYY-MM-DD_briefing.md` (CEO briefing)
- **Includes**: Revenue tracking, bottleneck analysis, cost suggestions

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Gmail API 403" | Run: `python auth/gmail.py` to re-authenticate |
| "Port 8001 in use" | Kill: `lsof -i :8001 \| grep python \| awk '{print $2}' \| xargs kill -9` |
| "Module not found" | Run: `pip install -r requirements.txt` |
| "No files in Needs_Action" | Check Gmail has unread+important emails, or re-authenticate |
| "Obsidian not syncing" | Make sure you opened `/Users/hparacha/DigitalFTE/vault/` |

---

## Verification Commands

```bash
# Check setup
python Setup_Verify.py

# View latest activity
tail -f vault/Logs/2026-01-13.json

# Query specific actions
cat vault/Logs/2026-01-13.json | jq '.[] | select(.action_type=="email_send")'

# Check process health
cat vault/Logs/watchdog_status.json | jq .

# Watch orchestrator live
tail -f scripts/orchestrator.out
```

---

## Key Architecture Patterns

**File-based State Machine**:
```
/Needs_Action/     Input (watcherscreate files here)
    ↓
Orchestrator reads + processes
    ↓
/Pending_Approval/ HITL review (human decides)
    ↓
Move to /Approved/ (human approves)
    ↓
Orchestrator executes via MCP
    ↓
/Done/              Completed & logged
```

**Why This Works**:
- ✅ Resumable (can restart any time without losing state)
- ✅ Human-readable (see everything in Obsidian)
- ✅ Transparent (all decisions logged in files)
- ✅ Resilient (no database needed, just files)

---

## Cost Comparison (Why This Matters)

| Metric | Human FTE | Digital FTE |
|--------|-----------|------------|
| Availability | 40 hrs/week | **168 hrs/week** |
| Cost | $4,000-8,000/mo | **$500-2,000/mo** |
| Tasks/year | ~2,000 | **~8,760** |
| Cost per task | ~$5.00 | **~$0.25** |
| **Savings** | — | **85-90%** |

---

## Real Use Cases Running

1. **Email Triage**: Reads important emails, drafts responses, logs conversations
2. **WhatsApp Manager**: Responds to business messages, routes to human when needed
3. **Social Media**: Posts LinkedIn updates, tweets, Facebook content
4. **Invoicing**: Creates invoices in Xero, logs transactions
5. **CEO Briefing**: Weekly audit of revenue, tasks, bottlenecks, suggestions

---

## Next Steps

1. **Run the demo** using commands at top of this file
2. **Read**: HACKATHON_COMPLIANCE.md (compliance verification)
3. **Read**: ARCHITECTURE.md (detailed system design)
4. **Check**: GOLD_SPEC.md (checklist of all requirements)
5. **Review**: LESSONS_LEARNED.md (implementation insights)

---

## Status

🏆 **GOLD TIER - 100% COMPLETE**

All 23 requirements from hackathonspecs.md implemented:
- ✅ 5/5 Bronze requirements
- ✅ 7/7 Silver requirements
- ✅ 11/11 Gold requirements

Ready for demo & submission.
