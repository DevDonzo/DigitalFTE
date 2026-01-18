# 🚀 DigitalFTE - Build Your Own Personal AI Employee

An open-source autonomous AI agent system that works 24/7 like a full-time employee. Built with Claude Code, Obsidian, Python, and MCP servers.

**Repository**: https://github.com/DevDonzo/DigitalFTE

**Status**: 🏆 Platinum Tier (Phase 1) - Cloud + Local split architecture with 24/7 cloud agent, local approval/execution, Odoo accounting, and git-based vault sync

---

## What It Does

DigitalFTE automates personal and business tasks across multiple domains:

- **📧 Email Management** - AI monitors Gmail, drafts intelligent replies, you approve before sending
- **💬 WhatsApp Messages** - Receives messages via webhooks, generates contextual responses
- **📱 Social Media** - Auto-posts to LinkedIn, Twitter, Facebook, Instagram
- **💰 Accounting** - Creates invoices & bills in Odoo Community, logs transactions, generates P&L reports (via Odoo JSON-RPC API)
- **📊 Executive Briefing** - Weekly automated summary of revenue, tasks, and key metrics
- **✍️ Personalized Writing** - AI learns your email style and voice, matches your tone naturally
- **🔗 Thread Context** - AI replies reference previous emails in the conversation
- **📎 File Attachments** - Automatically attach PDFs and documents to outgoing emails

**Core Philosophy**:
- 🔒 **Local-first** (Obsidian vault) + Cloud integrations (Gmail, WhatsApp, social APIs)
- 👤 **Human-in-the-loop** - You always review sensitive actions before execution
- 🛡️ **Privacy-focused** - All data stays in your vault, no third-party storage
- 🔧 **Fully customizable** - Adapt to your workflow and business rules

---

## Key Features

### ✨ Advanced Email System
- **AI Email Drafting** - OpenAI generates contextual replies to incoming emails
- **Personalized Voice** - Learns your writing style from past emails or manual configuration
- **Thread Context** - Replies automatically reference previous messages in conversation
- **Tone Analysis** - Warns if a draft doesn't match your typical style
- **Attachments** - Searches Downloads/Desktop, validates files, attaches to emails
- **HITL Approval** - All drafts require your review before sending

### 🤖 AI-Powered Agents
- Email responder (with style matching)
- WhatsApp message handler
- Social media poster
- Invoice generator
- Weekly briefing curator

### 📝 Obsidian Vault Integration
- Local markdown-based memory
- Organized workflow (Needs_Action → Pending_Approval → Approved → Done)
- Full audit trail (90+ days of logs)
- Company handbook for automation rules

### 🔄 Multi-Channel Support
- **Gmail** - Monitor, draft, send emails
- **WhatsApp** - Receive & respond via Twilio webhooks
- **LinkedIn** - Auto-post content
- **Twitter/X** - Post updates and engage
- **Facebook/Instagram** - Social media automation
- **Xero** - Invoicing and accounting

### 🚨 Reliability Features
- Process watchdog (auto-restart failed scripts)
- Error recovery with exponential backoff
- Graceful degradation (continue on partial failures)
- Structured logging with JSONL format
- Health monitoring and alerts

---

## Quick Start (5 Minutes)

### Prerequisites
- Python 3.13+
- Node.js 24+
- Obsidian v1.10.6+
- Git

### 1. Clone & Install

```bash
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE

# Install dependencies
pip install -r requirements.txt
npm install
```

### 2. Configure API Keys

```bash
# Copy template and add your API keys
cp .env.example .env
nano .env  # Edit with your credentials
```

**Required APIs** (start with just email):
- Gmail OAuth 2.0
- OpenAI API key
- (Optional) Twilio, Twitter, Meta, Xero, LinkedIn

See `.env.example` for all options.

### 3. Verify Setup

```bash
python Setup_Verify.py
```

### 4. Configure Your Email Style

Edit `/vault/EmailStyle.md` with your writing preferences:

```markdown
# Your Email Writing Style

## Tone & Voice
Professional but conversational, direct and honest

## Opening Lines
- "Hi [Name]," (for known contacts)
- "Thanks for reaching out on..." (for new conversations)

## Common Phrases
- "I'd be happy to..."
- "Let me know if..."
- "Looking forward to..."

## Closing
Best regards,
[Your Name]
```

The AI will use this to match your voice in all email drafts.

### 5. Run the System

```bash
# Terminal 1: Main orchestrator
python agents/orchestrator.py

# Terminal 2: Email monitor
python agents/gmail_watcher.py

# Terminal 3: Health watchdog
python agents/watchdog.py

# Terminal 4: View your vault
open -a Obsidian vault/
```

Your AI Employee is now running! 🎉

---

## How It Works

### Email Workflow Example

```
1. New email arrives at Gmail (unread + important)
   ↓
2. Gmail Watcher detects it (every 20 seconds)
   ↓
3. Creates EMAIL_[id].md in vault/Needs_Action/
   ↓
4. Orchestrator reads and analyzes
   ↓
5. AI drafts intelligent reply (matching your style)
   ↓
6. Routes to vault/Pending_Approval/ for your review
   ↓
7. You review and edit (optional)
   ↓
8. Move to vault/Approved/ to send
   ↓
9. Orchestrator executes (sends via Gmail API)
   ↓
10. Logged to vault/Logs/emails_sent.jsonl
    ↓
11. Moved to vault/Done/
```

**Key**: You always review before anything is sent. Full transparency.

### Personalized Email Voice

The system learns your email style through:

1. **Manual Configuration** (Recommended)
   - Edit `/vault/EmailStyle.md` with your tone, phrases, and examples
   - AI reads this when drafting emails
   - More accurate than auto-learning

2. **Auto-Analysis** (Optional)
   - Run `python utils/email_style_analyzer.py` to analyze real emails
   - Best for established email history
   - Skip if using test/bot-generated emails

### Thread Context & Attachments

**Thread Context**:
- Gmail Watcher fetches full email threads
- Email Drafter includes thread history in prompts
- AI generates 3-5 key point summary
- Replies naturally reference previous messages

**Attachments**:
- Email drafts search Downloads and Desktop for files
- Add attachments to frontmatter:
  ```yaml
  attachments:
    - /Users/[name]/Downloads/invoice.pdf
  ```
- System validates file size (Gmail limit: 25MB)
- Automatically attaches when email is sent

---

## Architecture

```
┌─────────────────────────────────────────┐
│     Perception Layer (Watchers)         │
├─────────────────────────────────────────┤
│ • gmail_watcher.py (Gmail monitoring)   │
│ • whatsapp_watcher.py (Message handler) │
│ • linkedin_watcher.py (Content monitor) │
│ • filesystem_watcher.py (File drops)    │
└────────────────┬────────────────────────┘
                 │
                 ↓
        ┌─────────────────┐
        │  Obsidian Vault │ (Local-First Memory)
        │  (Markdown DB)  │
        └────────┬────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│    Reasoning Layer (Orchestrator)       │
├─────────────────────────────────────────┤
│ • Reads vault files                     │
│ • Uses Claude/OpenAI for reasoning      │
│ • Drafts responses with personalization │
│ • Routes to approval queue              │
└────────────────┬────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────┐
│     Action Layer (MCP Servers)          │
├─────────────────────────────────────────┤
│ • Email MCP (Gmail send/receive)        │
│ • Twitter MCP (X integration)           │
│ • Meta Social MCP (FB/Instagram)        │
│ • Xero MCP (Invoicing/Accounting)       │
│ • Custom tools                          │
└─────────────────────────────────────────┘
```

**Data Flow**: Perception → Memory → Reasoning → Action → Audit

---

## File Structure

```
DigitalFTE/
├── README.md                    ← Start here
├── ARCHITECTURE.md              ← System design deep-dive
├── DEMO.md                      ← Walkthrough examples
│
├── vault/                       ← YOUR LOCAL DATABASE (Obsidian)
│   ├── Dashboard.md            ← Status overview
│   ├── Company_Handbook.md     ← Automation rules
│   ├── EmailStyle.md           ← Your writing style profile
│   ├── Needs_Action/           ← Incoming tasks
│   ├── Pending_Approval/       ← Awaiting your review
│   ├── Approved/               ← Ready to execute
│   ├── Done/                   ← Completed tasks
│   └── Logs/                   ← Audit trail (JSONL)
│
├── agents/                      ← SYSTEM AGENTS & WATCHERS
│   ├── orchestrator.py         ← Main engine (1,469 lines)
│   ├── gmail_watcher.py        ← Email monitor
│   ├── whatsapp_watcher.py     ← WhatsApp handler
│   ├── linkedin_watcher.py     ← LinkedIn integration
│   ├── watchdog.py             ← Health monitor
│   ├── webhook_server.py       ← WhatsApp webhooks
│   └── base_watcher.py         ← Base class
│
├── utils/                       ← REASONING UTILITIES
│   ├── email_drafter.py        ← OpenAI email generation (personalized)
│   ├── email_style_analyzer.py ← Learn your writing style
│   ├── attachment_finder.py    ← Find & validate files
│   ├── tweet_drafter.py        ← Tweet generation
│   ├── whatsapp_drafter.py     ← Message generation
│   ├── social_post_drafter.py  ← Multi-platform posts
│   └── error_handler.py        ← Error recovery
│
├── mcp_servers/                 ← ACTION LAYER
│   ├── email_mcp/              ← Gmail integration
│   ├── twitter_mcp/            ← Twitter/X posting
│   ├── meta_social_mcp/        ← Facebook/Instagram
│   └── xero_mcp/               ← Invoicing/Accounting
│
├── auth/                        ← API AUTHENTICATION
│   ├── gmail.py                ← Gmail OAuth 2.0
│   ├── twitter.py              ← Twitter API auth
│   ├── linkedin.py             ← LinkedIn OAuth
│   └── xero.py                 ← Xero OAuth 2.0
│
├── tests/                       ← TEST SUITE
│   ├── test_gmail_watcher.py
│   ├── test_full_workflow.py
│   ├── test_integration.py
│   └── test_email_enhancements.py
│
├── requirements.txt             ← Python dependencies
├── package.json                 ← Node.js dependencies
├── .env.example                 ← Configuration template
└── mcp_config.json             ← MCP server setup
```

---

## Configuration

### Email Style Personalization

Create `/vault/EmailStyle.md` with:

```markdown
# Email Writing Style

## Tone
Professional, direct, friendly

## Opening Lines
- "Hi [Name]," (standard)
- "Thanks for reaching out..." (responding)

## Phrases You Use
- "I'd be happy to..."
- "Looking forward to..."
- "Let me know if you have questions"

## Sentence Style
Short and punchy (1-2 sentences per idea)

## Closing
Best regards,
[Your Name]
```

**Tips**:
- Include real email examples for best results
- Edit anytime to refine your style
- AI uses this for ALL drafts

### Automation Rules (Company_Handbook.md)

```markdown
## Email Automation Rules

- Auto-approve emails under $500
- Escalate customer complaints
- Archive newsletters

## Response Rules

- Inquiry: Professional tone, <2 hour response
- Complaint: Empathetic, solution-focused
- Payment: Factual, include reference numbers
```

### Environment Variables (.env)

```bash
# Gmail
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your_secret
GMAIL_PROJECT_ID=your-project-id

# OpenAI
OPENAI_API_KEY=sk-...

# Optional APIs
TWILIO_ACCOUNT_SID=...
TWITTER_API_KEY=...
FACEBOOK_ACCESS_TOKEN=...
XERO_CLIENT_ID=...
```

---

## Testing

Run the test suite:

```bash
# All tests
pytest tests/

# Specific test
pytest tests/test_email_enhancements.py

# With coverage
pytest --cov=. tests/
```

Tests cover:
- Email monitoring and drafting
- Thread context and attachments
- Style personalization
- Full end-to-end workflows
- Error recovery
- Integration with external APIs

---

## Documentation

- **README.md** ← You are here
- **ARCHITECTURE.md** - System design & data flows
- **DEMO.md** - Step-by-step walkthrough
- **[vault/EmailStyle.md](vault/EmailStyle.md)** - Your writing style template
- **[vault/Company_Handbook.md](vault/Company_Handbook.md)** - Automation rules

---

## Customization

### Add Your Own Watchers

Create a new watcher by extending `BaseWatcher`:

```python
from agents.base_watcher import BaseWatcher

class CustomWatcher(BaseWatcher):
    def __init__(self, vault_path: str):
        super().__init__(vault_path, check_interval=30)

    def check(self):
        # Your custom logic here
        messages = self._fetch_messages()
        for msg in messages:
            self.create_action_file(msg)
```

### Add Your Own Drafters

Create a drafter for any content type:

```python
class CustomDrafter:
    def __init__(self, vault_path: str):
        self.vault = Path(vault_path)
        self.client = OpenAI()

    def draft_response(self, message: dict) -> str:
        # Use OpenAI to generate response
        # Include your style guide
        # Return draft text
```

### Integrate with New APIs

Add MCP servers in `mcp_servers/` for any external service:

```javascript
// mcp_servers/custom_api/index.js
const { Server } = require("@anthropic-ai/sdk/lib/resources");

server.setRequestHandler(CreateMessageRequestSchema, ...)
```

---

## Security & Privacy

- ✅ **Local-first**: All data stored in your Obsidian vault
- ✅ **No cloud storage**: Never synced to cloud by default
- ✅ **Credentials protected**: `.env` file is gitignored
- ✅ **OAuth 2.0**: All APIs use secure authentication
- ✅ **HITL**: Human always reviews before sensitive actions
- ✅ **Audit logging**: Complete trail of all actions (JSONL)
- ✅ **Error handling**: Graceful degradation, no data loss
- ✅ **No data collection**: This is your personal system

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Gmail API 403` | Run: `python auth/gmail.py` (re-authenticate) |
| Port 8001 in use | Kill: `lsof -i :8001 \| grep LISTEN \| awk '{print $2}' \| xargs kill -9` |
| `ModuleNotFoundError` | Run: `pip install -r requirements.txt` |
| No emails detected | Check Gmail has "unread" + "important" labels |
| Email style not applied | Make sure `/vault/EmailStyle.md` exists and has content |
| Attachments not working | Verify file paths are absolute (e.g., `/Users/name/Downloads/file.pdf`) |

---

## Performance

Typical resource usage:

- **Memory**: ~150-200 MB (watchers + orchestrator)
- **CPU**: <5% idle, <20% during processing
- **Disk**: ~50-100 MB per month (logs + vault)
- **Cost**: ~$50-500/month (depends on API usage)

---

## Contributing

We welcome contributions! Here's how:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Add tests for new functionality
5. Commit with clear messages
6. Push and open a pull request

**Areas for contribution**:
- New watchers (Slack, Teams, etc.)
- Additional drafters (for SMS, Discord, etc.)
- Enhanced style matching algorithms
- Better attachment handling
- Testing improvements
- Documentation

---

## Roadmap

- [ ] Web dashboard for vault management
- [ ] Mobile app for approvals
- [ ] Multi-user support
- [ ] Advanced scheduling (vs cron)
- [ ] ML-based style learning
- [ ] Calendar integration
- [ ] CRM integration
- [ ] Chat interface for quick approvals

---

## License

MIT License - See LICENSE file for details

---

## Support

- **Questions?** Check ARCHITECTURE.md or DEMO.md
- **Found a bug?** Open an issue on GitHub
- **Have ideas?** Discussions welcome!
- **Need help?** See the Troubleshooting section

---

## FAQ

**Q: Can I use this for my business?**
A: Yes! It's designed for both personal and business use. Customize the rules in Company_Handbook.md.

**Q: What if the AI generates something wrong?**
A: The Human-in-the-Loop system requires your approval before anything is sent. You always review first.

**Q: Can I run multiple instances?**
A: Yes, but each needs its own vault directory and API keys. Consider using different Gmail accounts or filters.

**Q: Is my data private?**
A: Completely. Everything is stored locally in Obsidian. API keys are in .env (gitignored). No telemetry.

**Q: Can I customize the AI prompts?**
A: Yes! Edit `/vault/EmailStyle.md` or modify the drafters in `utils/`.

---

## Credits

Built with:
- [Claude/OpenAI](https://openai.com) - AI language models
- [Obsidian](https://obsidian.md) - Local markdown database
- [Claude Code](https://claude.com/claude-code) - Development environment
- [Google APIs](https://developers.google.com) - Gmail, Calendar
- [Twilio](https://twilio.com) - WhatsApp integration
- [Twitter API v2](https://developer.twitter.com) - Social media
- [Xero](https://developer.xero.com) - Accounting

---

## Citation

If you use DigitalFTE in your research or project, please cite:

```bibtex
@software{digitalfte2026,
  title={DigitalFTE: Personal AI Employee System},
  author={DevDonzo},
  year={2026},
  url={https://github.com/DevDonzo/DigitalFTE}
}
```

---

## Get Started

1. Clone the repo
2. Run `Setup_Verify.py`
3. Edit `/vault/EmailStyle.md` with your voice
4. Start the watchers
5. Monitor your vault in Obsidian

---

**DigitalFTE** - Enterprise-grade autonomous AI agent system for personal and business automation.


