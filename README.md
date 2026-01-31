# 🚀 DigitalFTE - Your Personal AI Employee

An open-source autonomous AI agent that works 24/7 like a full-time employee.

🏆 **Built at a 48-hour hackathon** — what started as a weekend project to automate my overflowing inbox turned into a full autonomous agent system.

**Why DigitalFTE?**
- 💰 **Dirt cheap** - ~$1/day max. A full-time AI employee for less than a coffee
- 🔒 **Local-first** - All data stays in your Obsidian vault
- 👤 **Human-in-the-loop** - You review before anything gets sent

---

## What It Does

- **📧 Email** - Monitors Gmail, drafts replies in your voice, you approve before sending
- **💬 WhatsApp** - Receives messages, generates contextual responses
- **📱 Social Media** - Auto-posts to LinkedIn, Twitter, Facebook, Instagram
- **💰 Accounting** - Creates invoices & bills in Odoo, generates P&L reports
- **📊 Weekly Briefing** - Automated summary of revenue, tasks, and metrics

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

Edit `/vault/EmailStyle.md` to teach the AI your writing voice.

---

## Requirements

- Docker Desktop
- Python 3.13+
- Node.js 24+
- API keys: Gmail OAuth, OpenAI (optional: Twilio, Twitter, Meta)

---

## License

MIT
