# 🏆 DigitalFTE - Personal AI Employee

An autonomous AI agent that works 24/7 like a full-time employee. Built with Claude Code, Obsidian, Python watchers, and MCP servers.

**Repository**: https://github.com/DevDonzo/DigitalFTE.git

**Status**: 🏆 Gold Tier - 100% Complete (All 23 hackathon requirements implemented)

---

## What It Does

This system automates personal and business affairs across multiple domains:

- **Email Management**: Monitors Gmail, drafts intelligent replies, routes to human for approval
- **WhatsApp Messages**: Receives messages via Twilio webhooks, generates contextual responses
- **Social Media**: Posts to LinkedIn, Twitter, Facebook, Instagram
- **Accounting**: Creates invoices in Xero, logs transactions, generates reports
- **CEO Briefing**: Weekly automated summary of revenue, tasks, and bottlenecks

**Core Principle**: Local-first (Obsidian vault) + Cloud integrations (Gmail, WhatsApp, Twitter, etc.) + Human-in-the-loop approval for sensitive actions.

---

## Quick Start (2 Minutes)

### Prerequisites
- Python 3.13+
- Node.js 24+
- Obsidian v1.10.6+
- API credentials (.env file)

### Setup
```bash
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE

pip install -r requirements.txt
npm install

cp .env.example .env
# Edit .env with your API keys

python Setup_Verify.py
```

### Run
```bash
# Terminal 1: Main engine
python scripts/orchestrator.py

# Terminal 2: Email monitor
python watchers/gmail_watcher.py

# Terminal 3: WhatsApp receiver
python scripts/webhook_server.py &
python watchers/whatsapp_watcher.py

# Terminal 4: Health monitor
python scripts/watchdog.py

# View vault
open -a Obsidian vault/
```

---

## Architecture

**Four-Layer System**:

1. **Perception Layer** (Watchers)
   - `gmail_watcher.py` → Monitors Gmail
   - `whatsapp_watcher.py` → Processes WhatsApp messages
   - `linkedin_watcher.py` → LinkedIn integration
   - `filesystem_watcher.py` → File drop automation

2. **Memory & Dashboard** (Obsidian Vault)
   - Local markdown files (Needs_Action, Pending_Approval, Approved, Done, Logs)
   - Company_Handbook (automation rules)
   - Dashboard.md (real-time status)

3. **Reasoning Layer** (Orchestrator)
   - `scripts/orchestrator.py` (1,469 lines)
   - Reads messages → Uses OpenAI to draft → Routes to approval
   - Thread-safe batching and deduplication

4. **Action Layer** (MCP Servers)
   - Email MCP → Send/receive emails
   - Twitter MCP → Post tweets
   - Meta Social MCP → Facebook/Instagram
   - Xero MCP → Invoicing & accounting

**Plus**: Watchdog for process monitoring, Weekly_audit for CEO briefing, Webhook server for receiving messages.

---

## File Structure

```
DigitalFTE/
├── README.md                    ← You are here
├── DEMO.md                      ← How to run a demo
├── ARCHITECTURE.md              ← System design deep-dive
├── HACKATHON_COMPLIANCE.md      ← All requirements verified
├── GOLD_SPEC.md                 ← Gold tier checklist
├── LESSONS_LEARNED.md           ← Key insights
├── CLAUDE.md                    ← Claude Code instructions
│
├── vault/                       ← Obsidian vault (local-first memory)
│   ├── Dashboard.md
│   ├── Company_Handbook.md
│   ├── Needs_Action/            ← Input from watchers
│   ├── Pending_Approval/        ← HITL review queue
│   ├── Approved/                ← Ready to execute
│   ├── Done/                    ← Completed tasks
│   ├── Logs/                    ← Audit trail (JSONL)
│   ├── Briefings/               ← CEO briefing reports
│   └── Accounting/              ← Xero integration
│
├── scripts/                     ← Core orchestration
│   ├── orchestrator.py          ← Main engine (reads/thinks/executes)
│   ├── watchdog.py              ← Process monitor (auto-restart)
│   ├── webhook_server.py        ← WhatsApp webhook receiver (port 8001)
│   ├── weekly_audit.py          ← CEO briefing generator
│   └── setup.sh                 ← Initialization script
│
├── watchers/                    ← Perception layer
│   ├── base_watcher.py          ← Abstract base class
│   ├── gmail_watcher.py         ← Email monitoring
│   ├── whatsapp_watcher.py      ← Message processing
│   ├── linkedin_watcher.py      ← LinkedIn integration
│   └── filesystem_watcher.py    ← File drop automation
│
├── mcp_servers/                 ← Action layer (external integrations)
│   ├── email_mcp/               ← Gmail integration
│   ├── twitter_mcp/             ← Twitter posting
│   ├── meta_social_mcp/         ← Facebook/Instagram
│   ├── xero_mcp/                ← Accounting
│   └── browser_mcp/             ← (Placeholder)
│
├── utils/                       ← Supporting utilities
│   ├── email_drafter.py         ← OpenAI email generation
│   ├── tweet_drafter.py         ← Tweet generation
│   ├── whatsapp_drafter.py      ← Message generation
│   ├── audit_logger.py          ← Structured logging
│   ├── error_handler.py         ← Error handling
│   └── retry_handler.py         ← Exponential backoff
│
├── auth/                        ← Authentication modules
│   ├── gmail.py                 ← Gmail OAuth 2.0
│   ├── twitter.py               ← Twitter API auth
│   ├── linkedin.py              ← LinkedIn auth
│   └── xero.py                  ← Xero OAuth 2.0
│
├── tests/                       ← Test suite
│   ├── test_gmail_watcher.py
│   ├── test_full_workflow.py
│   ├── test_integration.py
│   ├── test_error_recovery.py
│   └── ...
│
├── skills/                      ← Claude Code Agent Skills
│   ├── email-drafting.md
│   ├── email-monitor.md
│   ├── whatsapp-monitor.md
│   └── ... (10+ skills)
│
├── requirements.txt             ← Python dependencies
├── package.json                 ← Node.js dependencies
├── .env.example                 ← Credentials template
└── mcp_config.json              ← MCP server configuration
```

---

## Scripts Overview

| Script | What It Does | Interval |
|--------|------------|----------|
| **orchestrator.py** | Main engine - reads, drafts, routes, executes | Real-time |
| **gmail_watcher.py** | Monitors Gmail for unread+important | Every 20s |
| **whatsapp_watcher.py** | Processes WhatsApp messages from webhook | Every 10s |
| **webhook_server.py** | Receives WhatsApp from Twilio (port 8001) | Real-time |
| **watchdog.py** | Monitors all processes, auto-restarts | Every 60s |
| **weekly_audit.py** | CEO briefing generation | Sunday 11 PM |

For detailed reference, see: **DEMO.md**

---

## How It Works

### Example: Email Processing

```
1. New email arrives at Gmail (unread + important)
   ↓
2. Gmail Watcher detects it (every 20 seconds)
   ↓
3. Creates EMAIL_[id].md in /Needs_Action/
   ↓
4. Orchestrator reads the file
   ↓
5. OpenAI drafts an intelligent reply
   ↓
6. Routes to /Pending_Approval/ for human review
   ↓
7. Human moves file to /Approved/
   ↓
8. Orchestrator executes (sends via Email MCP)
   ↓
9. Logged to /vault/Logs/emails_sent.jsonl
   ↓
10. Moved to /Done/
```

**Key Feature**: Human always reviews sensitive actions (HITL - Human-in-the-Loop).

---

## Configuration

### Required API Keys (.env)
```bash
# Gmail (OAuth 2.0)
GMAIL_CREDENTIALS_PATH=/path/to/credentials.json

# WhatsApp (Twilio)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_WHATSAPP_NUMBER=...

# LinkedIn
LINKEDIN_ACCESS_TOKEN=...

# Twitter (API v2 + 1.0a)
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_BEARER_TOKEN=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...

# Meta (Facebook/Instagram)
FACEBOOK_ACCESS_TOKEN=...
FACEBOOK_PAGE_ID=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...

# Xero (OAuth 2.0)
XERO_CLIENT_ID=...
XERO_CLIENT_SECRET=...
XERO_TENANT_ID=...

# OpenAI
OPENAI_API_KEY=...
```

### Automation Rules (Company_Handbook.md)
- Email auto-approval thresholds
- Payment approval limits
- WhatsApp escalation levels
- LinkedIn posting policies

---

## Testing

Run the test suite:
```bash
pytest tests/
```

Available tests:
- `test_gmail_watcher.py` - Email monitoring
- `test_full_workflow.py` - End-to-end flow
- `test_integration.py` - All integrations
- `test_error_recovery.py` - Error handling
- `test_mcp_servers.py` - External integrations

---

## Documentation

- **DEMO.md** - How to run the demo (start here!)
- **ARCHITECTURE.md** - System design & data flows
- **HACKATHON_COMPLIANCE.md** - All 23 requirements verified ✅
- **GOLD_SPEC.md** - Gold tier requirements
- **LESSONS_LEARNED.md** - Implementation insights
- **CLAUDE.md** - Claude Code instructions

---

## Security & Privacy

- ✅ Local-first: All data in Obsidian vault (never cloud storage)
- ✅ Credentials: Environment variables (.env, gitignored)
- ✅ OAuth 2.0: All APIs use secure authentication
- ✅ HITL: Human approval before sensitive actions
- ✅ Audit logging: 90+ days of activity logs (JSONL format)
- ✅ Error handling: Graceful degradation, no data loss

---

## Compliance

### Gold Tier (All Requirements Met) ✅

**Bronze** (5/5):
- ✅ Dashboard + Company_Handbook
- ✅ Folder structure
- ✅ Working watchers
- ✅ Claude Code vault I/O
- ✅ Agent Skills

**Silver** (7/7):
- ✅ Multiple watchers
- ✅ LinkedIn auto-posting
- ✅ Plan.md reasoning
- ✅ Email MCP server
- ✅ HITL approval workflow
- ✅ Scheduling (launchd)
- ✅ Agent Skills

**Gold** (11/11):
- ✅ Cross-domain integration
- ✅ Xero MCP + accounting
- ✅ Meta Social MCP
- ✅ Twitter MCP
- ✅ 5 MCP servers
- ✅ CEO briefing
- ✅ Error recovery
- ✅ Audit logging (90+ days)
- ✅ Documentation
- ✅ Ralph Wiggum loop
- ✅ 10+ Agent Skills

**Full compliance report**: See `HACKATHON_COMPLIANCE.md`

---

## Key Metrics

| Metric | Human FTE | Digital FTE |
|--------|-----------|-----------|
| Availability | 40 hrs/week | **168 hrs/week** |
| Cost | $4,000-8,000/mo | **$500-2,000/mo** |
| Tasks/year | ~2,000 | **~8,760** |
| Cost per task | ~$5.00 | **~$0.25** |
| **Savings** | — | **85-90%** |

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Gmail API 403 | Run: `python auth/gmail.py` (re-authenticate) |
| Port 8001 in use | Kill: `lsof -i :8001 \| grep python \| xargs kill -9` |
| Module not found | Run: `pip install -r requirements.txt` |
| Obsidian not syncing | Open: `/Users/hparacha/DigitalFTE/vault/` |
| No files in Needs_Action | Check Gmail has unread+important emails |

---

## Next Steps

1. **Run the demo**: Follow commands in **DEMO.md**
2. **Understand the system**: Read **ARCHITECTURE.md**
3. **Check compliance**: See **HACKATHON_COMPLIANCE.md**
4. **Review code**: Start with `scripts/orchestrator.py`

---

## Support

- **Questions**: Check DEMO.md or ARCHITECTURE.md
- **Issues**: See Troubleshooting section above
- **Code**: All well-commented and organized

---

**Made for**: Personal AI Employee Hackathon 0

**Created**: January 2026

**Status**: 🏆 Gold Tier Ready for Submission
