# Digital FTE - Personal AI Employee

An autonomous AI agent that works 24/7 like a full-time employee. Built with Claude Code, Obsidian, Python watchers, and MCP servers.

## Quick Start

### Prerequisites
- Python 3.13+
- Node.js 24+
- Claude Code (Pro subscription or free with Gemini)
- Obsidian v1.10.6+

### Installation

```bash
# Clone repo
git clone <repo-url>
cd DigitalFTE

# Install dependencies
npm install
pip install -r requirements.txt

# Copy .env template and fill in credentials
cp .env.example .env
# Edit .env with your API keys

# Verify setup
python scripts/setup_verify.py
```

### Start the System

```bash
# Start orchestrator (main coordination engine)
python scripts/orchestrator.py

# In another terminal, start watchers
python watchers/gmail_watcher.py
python watchers/whatsapp_watcher.py

# Monitor with watchdog
python scripts/watchdog.py
```

## Architecture

```
┌─────────────────────────────────────────┐
│       EXTERNAL SOURCES                   │
│  Gmail │ WhatsApp │ Xero │ Social Media  │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│     PERCEPTION LAYER (Watchers)         │
│  Gmail, WhatsApp, LinkedIn, FileSystem   │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   OBSIDIAN VAULT (Memory)                │
│  /Inbox → /Plans → /Pending_Approval →   │
│  /Approved → /Done (with Logs)           │
└────────┬────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│   REASONING LAYER (Claude Code)         │
│  Read → Think → Plan → Write → Request   │
└────────┬────────────────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  HITL        │ │ MCP SERVERS  │ │ EXTERNAL     │
│  Approval    │ │ Email, Xero, │ │ ACTIONS      │
│  Folders     │ │ Social, etc  │ │ Send emails, │
│              │ │              │ │ post social, │
│              │ │              │ │ log payments │
└──────────────┘ └──────────────┘ └──────────────┘
```

## Folder Structure

- `vault/` - Obsidian vault (your AI's memory)
  - `Inbox/` - Watcher input
  - `Plans/` - Claude reasoning
  - `Pending_Approval/` - Awaiting human decision
  - `Approved/` - Ready for execution
  - `Done/` - Completed actions
  - `Logs/` - Audit trail

- `watchers/` - Perception layer (Gmail, WhatsApp, etc)
- `scripts/` - Orchestration (orchestrator.py, watchdog.py, weekly_audit.py)
- `mcp_servers/` - Action handlers (email, xero, social media)
- `utils/` - Shared utilities (audit_logger.py, retry_handler.py)
- `skills/` - Claude Code Agent Skills definitions
- `tests/` - Unit and integration tests

## Configuration

Edit `vault/Company_Handbook.md` to define:
- Automation rules (what Claude can do without approval)
- Payment thresholds
- Social media posting rules
- Escalation thresholds

## Tiers

- **Bronze** (8-12 hrs): Basic vault + Gmail watcher + Claude reads/writes
- **Silver** (20-30 hrs): Multiple watchers + LinkedIn posting + HITL approval
- **Gold** (40+ hrs): Full cross-domain + Xero + CEO briefing system

Current target: **GOLD**

## Status

- ✅ Phase 2 Scaffolding complete (folders & templates)
- ⏳ Phase 3-12 in progress

See `vault/Dashboard.md` for real-time progress.

## Documentation

- `GOLD_SPEC.md` - Complete technical specification
- `ARCHITECTURE.md` - System design & decisions
- `vault/Company_Handbook.md` - Automation rules
- `vault/Logs/audit_rules.md` - Logging & retention policy

## Next Steps

1. Set up external accounts (Xero, Meta, Twitter)
2. Implement watcher scripts (Gmail API, WhatsApp, LinkedIn)
3. Configure MCP servers
4. Create orchestration logic
5. Build CEO briefing system
6. Write tests
7. Create demo video

## Security

- **Never commit** `.env` file (add to .gitignore)
- Store credentials in `.env` only
- Use environment variables for all secrets
- Rotate API keys monthly
- Review audit logs weekly

## Support

- GitHub Issues: Report bugs
- Discussions: Ask questions
- Wednesday Research Meetings: Community support & demos

---

**Status**: Phase 2 Complete - Scaffolding Done
**Next Demo**: Wednesday, January 15, 2026
