# DigitalFTE
<!-- this PR was created by layla for integration test -->

DigitalFTE is a local-first AI operations system for inbox triage, approvals, social drafting, finance workflows, and weekly briefings.

🏆 **Built at a 48-hour hackathon** — what started as a weekend project to automate my overflowing inbox turned into a full autonomous agent system.

## What Changed

This repo now includes a real local control center:

- a polished browser UI for queue review, approvals, setup readiness, and recent activity
- one-click generation of briefings and vault dashboard refreshes
- quick capture so you can create new work items without hand-editing markdown
- repaired startup scripts and compatibility wrappers so the repo launches coherently

---

## What It Does

- **📧 Email** - Monitors Gmail, drafts replies in your voice, you approve before sending
- **💬 WhatsApp** - Receives messages, generates contextual responses
- **📱 Social Media** - Auto-posts to LinkedIn, Twitter, Facebook, Instagram
- **💰 Accounting** - Creates invoices & bills in Odoo, generates P&L reports
- **📊 Weekly Briefing** - Automated summary of revenue, tasks, and metrics

---

## ✍️ It Learns How You Write

This is the magic. DigitalFTE doesn't send generic AI-sounding messages — it learns YOUR voice.

**How it works:**

1. Create `/vault/EmailStyle.md` with your writing personality:
```markdown
# My Writing Style

## Tone
Casual but professional. I use "Hey" not "Dear". Short sentences.

## Phrases I Use
- "Let me know if that works"
- "Happy to jump on a call"
- "Cheers" (not "Best regards")

## Things I Never Say
- Corporate jargon
- "I hope this email finds you well"
```

2. The AI reads this before drafting ANY message — emails, WhatsApp, tweets, LinkedIn posts
3. Every response sounds like you actually wrote it

**Works across all channels:**
- 📧 Email replies match your professional tone
- 💬 WhatsApp messages match your casual texting style
- 🐦 Tweets capture your social media voice
- 💼 LinkedIn posts maintain your industry presence

You can create separate style guides for each channel, or use one unified voice.

---

## Quick Start

```bash
# install python deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# configure credentials as needed
cp .env.example .env

# start the local stack
./start_all.sh
```

Then open:

- Control Center: `http://127.0.0.1:8282`
- Odoo UI: `http://localhost:8069` if Docker is available
- Vault dashboard: [vault/Dashboard.md](./vault/Dashboard.md)

Stop everything with:

```bash
./stop_all.sh
```

## Control Center

The control center is the main operator surface. It gives you:

- live queue views for `Needs_Action`, `Pending_Approval`, `Approved`, `Rejected`, and `Done`
- full preview of vault items and one-click moves between stages
- setup visibility for Gmail, WhatsApp, social, finance, and OpenAI
- quick capture for new tasks and manual requests
- briefing generation and dashboard refresh from the UI

---

## How It Works

```
Email arrives → Gmail Watcher detects it → AI drafts reply (in your style)
    → You review in vault/Pending_Approval/ → Approve → Sent
```

The same vault-native flow works for WhatsApp, social media, and manual operator tasks.

---

## Architecture

```
┌─────────────────────────────────────┐
│  Watchers (Gmail, WhatsApp, etc.)   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Obsidian Vault (your local brain)  │
│  - Style guides                     │
│  - Pending approvals                │
│  - Action history                   │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  Orchestrator + AI                  │
│  - Reads your style                 │
│  - Drafts responses                 │
│  - Routes for approval              │
└──────────────┬──────────────────────┘
               ↓
┌─────────────────────────────────────┐
│  MCP Servers (Gmail, Twitter, etc.) │
│  - Executes approved actions        │
└─────────────────────────────────────┘
```

---

## Requirements

- Python 3.13+
- Docker Desktop for Odoo/Postgres
- API keys as needed: OpenAI, Gmail OAuth, Twilio, LinkedIn, Twitter/X, Meta

---

## Project Structure

```
DigitalFTE/
├── control_center/        # Local FastAPI app + polished operator UI
├── vault/                 # Obsidian-native working memory and approvals
├── agents/                # Watchers, orchestrators, sync, webhook server
├── watchers/              # Compatibility imports for legacy paths
├── scripts/               # Launch entrypoints
├── utils/                 # AI drafters and helpers
└── mcp_servers/           # API integrations
```

## Useful Commands

```bash
# start only the control center
python3 scripts/control_center.py

# generate a new weekly briefing
python3 scripts/weekly_audit.py

# run tests
pytest -q
```

---

## License

MIT
