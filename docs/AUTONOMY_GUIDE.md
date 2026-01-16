# Autonomous System Architecture Guide

## Overview

The system operates through five autonomous loops that coordinate perception, reasoning, human approval, execution, and resilience. This enables 24/7 operation with minimal manual intervention.

---

## Five Autonomous Loops

### Loop 1: Perception Layer (Watchers)

External sources are monitored continuously for new input:

```
Gmail Watcher (20s interval)  --|
WhatsApp Watcher (Webhook)     |---> vault/Needs_Action/
LinkedIn Watcher (5m interval) |
FileSystem Watcher (Real-time) |
```

**Components**:
- `agents/gmail_watcher.py` - Polls Gmail API for unread important messages
- `agents/whatsapp_watcher.py` - Receives messages via Twilio webhook
- `agents/linkedin_watcher.py` - Polls LinkedIn API for profile activity
- `agents/base_watcher.py` - Abstract base class with common functionality

**Output**: Files created in `vault/Needs_Action/` with standardized markdown format

---

### Loop 2: Reasoning Layer (Orchestrator)

Incoming items are processed and AI-generated responses created:

```
vault/Needs_Action/ (detected)
    |
    v
orchestrator.py (watchdog observer)
    |
    v
Email/WhatsApp/Tweet Drafters (OpenAI)
    |
    v
vault/Pending_Approval/ (awaiting human review)
```

**Process**:
1. Orchestrator detects new files in Inbox using `watchdog.Observer`
2. File type is determined (email, WhatsApp, LinkedIn, tweet)
3. Appropriate drafter (EmailDrafter, WhatsAppDrafter, TweetDrafter) processes the input
4. AI generates response using OpenAI API (gpt-4o-mini)
5. Draft file created in `vault/Pending_Approval/`

**Files**:
- `agents/orchestrator.py` - Main coordination engine
- `utils/email_drafter.py` - Email response generation
- `utils/whatsapp_drafter.py` - WhatsApp response generation
- `utils/tweet_drafter.py` - Social media post generation

---

### Loop 3: Human-in-the-Loop (Review & Approval)

Human operator reviews AI-generated drafts and makes approval decisions:

```
vault/Pending_Approval/ (AI drafts)
    |
    v
Human Review (Obsidian)
    |
    +---> Move to vault/Approved/ (send/post)
    +---> Edit & move to vault/Approved/ (send modified)
    +---> Delete or reject (discard)
```

**Process**:
1. User opens Obsidian and navigates to `vault/Pending_Approval/`
2. Reviews AI-generated draft with confidence score
3. Chooses to approve, edit, or reject
4. Approved files moved to `vault/Approved/`

**Safety**: All outbound actions require explicit human approval before execution

---

### Loop 4: Execution Layer (MCP Servers)

Approved actions are executed through appropriate MCP servers:

```
vault/Approved/ (approved by human)
    |
    v
orchestrator.py (detects file movement)
    |
    v
MCP Servers:
  - Email MCP (Gmail API)
  - WhatsApp MCP (Twilio API)
  - Meta Social MCP (Facebook/Instagram API)
  - Twitter MCP (Twitter/X API)
  - LinkedIn MCP (LinkedIn API)
  - Xero MCP (Accounting API)
    |
    v
External Systems (Gmail, Twilio, APIs)
    |
    v
vault/Done/ (completed, audit logged)
```

**Process**:
1. Orchestrator detects file in `vault/Approved/`
2. Parses file to extract recipient, content, type
3. Routes to appropriate MCP server based on filename
4. MCP server executes the action via external API
5. Result logged to `vault/Logs/`
6. File moved to `vault/Done/`

**MCP Servers** (`mcp_servers/*/index.js`):
- Email: Send/read emails via Gmail API
- WhatsApp: Send messages via Twilio API
- Meta Social: Post to Facebook/Instagram
- Twitter: Post tweets and fetch metrics
- Xero: Create invoices, log transactions
- Browser: Web automation and form filling

---

### Loop 5: Resilience Layer (Watchdog)

System processes are continuously monitored and automatically restarted on failure:

```
Watchdog (30s check interval)
    |
    +-- Check orchestrator.py (PID)
    |
    +-- Check gmail_watcher.py (PID)
    |
    +-- Check whatsapp_watcher.py (PID)
    |
    +-- Check linkedin_watcher.py (PID)
    |
    +-- Check webhook_server.py (PID)
    |
    v
    If process crashed: Auto-restart with exponential backoff
    Max restarts: 10 per hour (prevents restart loops)
    Recovery time: 3-5 seconds
```

**File**: `agents/watchdog.py`

**Configuration**: `scripts/com.digitalfte.watchdog.plist` (macOS launchd)

**Startup**: Loads at system boot via launchd

---

## Bonus Loop: Scheduled Operations

Weekly CEO briefing runs on fixed schedule:

```
Every Monday 8:00 AM (Built into Orchestrator)
    |
    v
orchestrator.py (_periodic_check)
    |
    +-- Count emails processed
    +-- Count tasks completed
    +-- Fetch Xero financial data
    +-- Calculate metrics
    |
    v
vault/Briefings/YYYY-MM-DD_briefing.md
```

**Configuration**: `scripts/schedule_ceo_briefing.plist` (macOS launchd)

**Output**: Markdown briefing with metrics and recommendations

---

## End-to-End Message Flow Example

### Timeline: Email Arrives and Is Processed

```
8:00:00 AM - Email arrives at Gmail server

8:00:05 AM - Gmail Watcher polls (20s interval)
  - Detects unread important email
  - Creates: vault/Needs_Action/EMAIL_client_20260111_080005.md

8:00:06 AM - Orchestrator detects new file
  - Reads email content
  - Calls EmailDrafter
  - OpenAI generates response (gpt-4o-mini)
  - Creates: vault/Pending_Approval/EMAIL_DRAFT_20260111_080006.md
  - Logs action to vault/Logs/2026-01-11.json

8:00:07 AM - Human opens Obsidian
  - Reviews draft in vault/Pending_Approval/
  - Reads AI's suggested response
  - Sees confidence score

8:00:15 AM - Human approves
  - Moves file to vault/Approved/

8:00:16 AM - Orchestrator detects approval
  - Reads approved file
  - Extracts recipient, subject, body
  - Calls Email MCP server
  - Email MCP sends via Gmail API
  - Moves file to vault/Done/
  - Logs success: "Email sent to client@example.com"

Result: Email answered in 16 seconds (plus human review time)
Audit Trail: Complete log entry in vault/Logs/
```

---

## Data Flow Diagram

```
External Input Sources
├── Gmail (Email)
├── WhatsApp (Twilio)
├── LinkedIn API
└── Local filesystem

    ↓

Perception Layer (Watchers)
├── gmail_watcher.py
├── whatsapp_watcher.py
├── linkedin_watcher.py
└── base_watcher.py

    ↓

vault/Needs_Action/ (primary) + vault/Inbox/ (legacy)

    ↓

Reasoning Layer (Orchestrator)
├── orchestrator.py
├── email_drafter.py
├── whatsapp_drafter.py
└── tweet_drafter.py

    ↓

vault/Pending_Approval/

    ↓

Human-in-the-Loop (Obsidian)
├── Review draft
├── Edit if needed
└── Move to Approved/

    ↓

vault/Approved/

    ↓

Execution Layer (MCP Servers)
├── email_mcp
├── whatsapp_mcp
├── meta_social_mcp
├── twitter_mcp
└── xero_mcp

    ↓

External Systems
├── Gmail
├── Twilio
├── Facebook/Instagram
├── Twitter/X
└── Xero

    ↓

vault/Done/ + vault/Logs/
(Completed actions and audit trail)
```

---

## Vault Folder Structure

| Folder | Purpose | Contains |
|--------|---------|----------|
| Inbox/ | Legacy watcher input | Optional legacy flow |
| Needs_Action/ | Primary input | New emails, WhatsApp messages, LinkedIn notifications |
| Needs_Action/ | Processing queue | Items awaiting orchestrator processing |
| Pending_Approval/ | Human review | AI-generated drafts awaiting human approval |
| Approved/ | Execution queue | Approved actions ready to execute |
| Done/ | Completed | Executed actions with results |
| Rejected/ | Discarded | Rejected or deleted items |
| Logs/ | Audit trail | JSON daily logs of all actions |
| Briefings/ | Reports | Weekly CEO briefings with metrics |
| Accounting/ | Financial | Xero integration data |
| Social_Media/ | Content | Social media content library |

---

## Process Management

### Starting the System

**Manual (for debugging)**:
```bash
# Terminal 1
python3 agents/orchestrator.py

# Terminal 2
python3 agents/gmail_watcher.py &
python3 agents/whatsapp_watcher.py &
python3 agents/linkedin_watcher.py &

# Terminal 3
python3 agents/webhook_server.py

# Terminal 4
python3 agents/watchdog.py
```

**Production (auto-start on boot)**:
```bash
cp scripts/com.digitalfte.watchdog.plist ~/Library/LaunchAgents/
cp scripts/schedule_ceo_briefing.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
launchctl load ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

### Monitoring

```bash
# View active processes
ps aux | grep python | grep -E "(orchestrator|watcher|webhook)"

# View watchdog logs
cat vault/Logs/watchdog.out

# View recent actions
tail -f vault/Logs/$(date +%Y-%m-%d).json | jq .

# Check process health
launchctl list | grep digitalfte
```

### Stopping the System

**Manual**:
```bash
pkill -f orchestrator.py
pkill -f watcher.py
pkill -f watchdog.py
```

**Production**:
```bash
launchctl unload ~/Library/LaunchAgents/com.digitalfte.watchdog.plist
launchctl unload ~/Library/LaunchAgents/com.digitalfte.schedule_ceo_briefing.plist
```

---

## Configuration

### Environment Variables

Key configuration in `.env`:

```bash
# Gmail
GMAIL_CLIENT_ID=xxx.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-xxx
GMAIL_PROJECT_ID=your-project-id

# OpenAI (for AI drafting)
OPENAI_API_KEY=xxx

# Xero (accounting)
XERO_CLIENT_ID=xxx
XERO_CLIENT_SECRET=xxx
XERO_TENANT_ID=xxx

# Twilio (WhatsApp)
TWILIO_ACCOUNT_SID=xxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_WHATSAPP_NUMBER=xxx

# Webhook
WEBHOOK_PORT=8001
WHATSAPP_WEBHOOK_VERIFY_TOKEN=xxx

# Vault
VAULT_PATH=./vault
```

See `CREDENTIALS_SETUP.md` for detailed credential configuration.

---

## Performance Characteristics

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Email detection | ~20s (poll interval) | Up to 5 per poll |
| WhatsApp reception | <100ms (webhook) | No limit |
| Draft generation | ~2-5s (OpenAI) | Sequential |
| File movement detection | ~50ms (watchdog) | Real-time |
| Email sending | ~1-2s (Gmail API) | Sequential |
| CEO briefing generation | ~30s (data aggregation) | Weekly |

No performance degradation at scale. System designed to handle 100+ messages per day.

---

## Error Recovery

Failed actions are handled per `ERROR_HANDLING.md`:

1. **Transient failures** (network timeout) - Retry with exponential backoff
2. **API rate limits** - Queue and retry after delay
3. **Invalid data** - Log and move to rejected folder
4. **Missing credentials** - Log and skip (no crash)
5. **External service down** - Continue monitoring; retry when available

All errors logged to `vault/Logs/` for audit and debugging.

---

## Audit & Logging

All actions logged to `vault/Logs/YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-01-11T08:00:16Z",
  "action": "email_sent",
  "source_file": "EMAIL_DRAFT_20260111_080006.md",
  "recipient": "client@example.com",
  "subject": "Project Update",
  "status": "success",
  "duration_ms": 1200,
  "mcp_server": "email_mcp"
}
```

**Retention**: 90 days of daily logs
**Audit Trail**: Complete record of all actions with timestamps
**Compliance**: Suitable for security and operational audits
