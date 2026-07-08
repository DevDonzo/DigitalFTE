# 🚀 DigitalFTE - Your Personal AI Employee

An open-source autonomous AI agent that works 24/7 like a full-time employee.

🏆 **Built at a 48-hour hackathon** — what started as a weekend project to automate my overflowing inbox turned into a full autonomous agent system.

**Why DigitalFTE?**
- 💰 **Dirt cheap** - ~$1/day max. A full-time AI employee for less than a coffee
- 🔒 **Local-first** - All data stays in your Obsidian vault
- 👤 **Human-in-the-loop** - You review before anything gets sent
- ✍️ **Sounds like YOU** - Learns your writing style across all channels

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
# Clone and configure
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE
cp .env.example .env
nano .env  # Add your Gmail, OpenAI keys

# Start everything
./start_all.sh
```

**That's it.** Odoo + PostgreSQL spin up in Docker, agents start running.

- Odoo UI: http://localhost:8069
- Vault: `open -a Obsidian vault/`
- Stop: `./stop_all.sh && docker-compose down`

---

## How It Works

```
Email arrives → Gmail Watcher detects it → AI drafts reply (in your style)
    → You review in vault/Pending_Approval/ → Approve → Sent
```

The same flow works for WhatsApp, social media, and everything else. You're always in control.

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

- Docker Desktop
- Python 3.13+
- Node.js 24+
- API keys: Gmail OAuth, OpenAI (optional: Twilio, Twitter, Meta)

---

## Project Structure

```
DigitalFTE/
├── vault/                 # Your local Obsidian database
│   ├── EmailStyle.md      # Your writing personality
│   ├── Needs_Action/      # Incoming tasks
│   ├── Pending_Approval/  # Awaiting your review
│   └── Done/              # Completed tasks
├── agents/                # Watchers & orchestrator
├── utils/                 # AI drafters (email, tweet, etc.)
└── mcp_servers/           # API integrations
```

---

## License

MIT
