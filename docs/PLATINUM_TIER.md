# Platinum Tier: Cloud + Local AI Employee Architecture

**Status**: Phase 1: Architecture & Implementation
**Estimated**: 60+ hours (Phases 1-3)
**Target**: 24/7 always-on cloud agent + local approval/execution

## Overview

Platinum Tier extends Gold with a **Cloud + Local Split Architecture**:

- **Cloud VM (Oracle Free Tier)**: 24/7 watchers + draft generation
- **Local Machine**: Human approvals + final execution + payment processing
- **Vault Sync**: Git-based file synchronization (audit trail)
- **Claim-by-Move**: Prevent double-work via atomic git commits

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   CLOUD VM (24/7 Always-On)                      │
│                    Oracle Cloud Free Tier                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  CLOUD WATCHERS (Draft-Only)                                    │
│  ├─ Gmail Watcher (polls email)                                 │
│  │  └─ Creates /Updates/EMAIL_draft.md (reply draft)           │
│  │                                                              │
│  ├─ Twitter Watcher (polls mentions)                            │
│  │  └─ Creates /Updates/TWEET_draft.md (response draft)        │
│  │                                                              │
│  └─ LinkedIn Watcher (polls activity)                           │
│     └─ Creates /Updates/POST_draft.md (post draft)             │
│                                                                   │
│  CLOUD ORCHESTRATOR (Subset)                                    │
│  ├─ AI reasoning (draft generation)                         │
│  ├─ Email drafting & style matching                             │
│  ├─ Social post drafting                                        │
│  └─ Create /Pending_Approval/ files for cloud decisions        │
│                                                                   │
│  VAULT SYNC AGENT (Git)                                         │
│  └─ Push /Updates/ every 5 minutes                              │
│  └─ Pull approvals & done items from local                      │
│                                                                   │
│  ⚠️  NO SECRETS: Email only, no WhatsApp/Banking/Payment       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↑
                              │ Git Push/Pull
                              │ (Vault sync, markdown only)
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 LOCAL MACHINE (User Interactive)                │
│                    Obsidian Vault (Mac/Windows/Linux)            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  LOCAL WATCHERS (Execution)                                     │
│  └─ WhatsApp Watcher (Twilio webhook)                           │
│     └─ Processes messages & approvals from user                 │
│                                                                   │
│  LOCAL ORCHESTRATOR (Subset)                                    │
│  ├─ Process /Pending_Approval/ files from cloud                │
│  ├─ Generate /Plans/ for human review                           │
│  ├─ Wait for user approval in /Approved/                        │
│  └─ Execute via MCP servers (Email, Social, Odoo)              │
│                                                                   │
│  MCP SERVERS (Execution-Only)                                   │
│  ├─ Email MCP (sends approved drafts)                           │
│  ├─ Twitter MCP (posts approved tweets)                         │
│  ├─ Social MCP (posts to Facebook/Instagram)                    │
│  └─ Odoo MCP (creates/posts invoices & transactions)           │
│                                                                   │
│  VAULT SYNC AGENT (Git)                                         │
│  └─ Pull /Updates/ from cloud every 5 minutes                   │
│  └─ Push approvals & done items                                 │
│                                                                   │
│  OBSIDIAN DASHBOARD (Single Writer: Local)                      │
│  ├─ /Needs_Action/ (input queue from watchers)                 │
│  ├─ /In_Progress/<agent>/ (claim-by-move)                      │
│  ├─ /Pending_Approval/ (awaiting human review)                 │
│  ├─ /Approved/ (ready for execution)                            │
│  ├─ /Done/ (completed & archived)                               │
│  └─ Dashboard.md (status updated by sync agent)                │
│                                                                   │
│  ⚠️  ALL SECRETS: WhatsApp, Banking, Payment creds            │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Security Boundaries

### Cloud .env (Cloud VM Only)

```env
# Cloud can use these (watchers/drafting)
OPENAI_API_KEY=...
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
TWITTER_API_KEY=...
LINKEDIN_ACCESS_TOKEN=...
AGENT_TYPE=cloud
```

### Local .env (Local Machine Only)

```env
# Local keeps these (never sync to cloud!)
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_SESSION=...
BANK_ACCOUNT_CODES=...
PAYMENT_TOKENS=...
ODOO_PASSWORD=...
AGENT_TYPE=local
```

### Vault Sync (Git - No Secrets)

**Syncs only**:
- `/vault/Updates/` (cloud drafts)
- `/vault/Needs_Action/` (input)
- `/vault/Pending_Approval/` (awaiting approval)
- `/vault/Approved/` (ready to execute)
- `/vault/Done/` (completed)
- `/vault/Plans/` (reasoning)
- `/vault/Dashboard.md` (status)
- `.md`, `.yaml`, `.json` files only

**Never syncs**:
- `.env` files (any variation)
- `.processed_*` files
- `.whatsapp_*` files
- `*_token.json` files
- `credentials.json`

## Workflow: Email Arriving While Local Offline

### Scenario
*Email arrives at 9:00 AM while user is away. Cloud processes it, creates draft, pushes to git. User returns at 5:00 PM, reviews draft, approves, and local executes the send.*

### Step-by-Step

```
9:00 AM - EMAIL ARRIVES
├─ Cloud Gmail Watcher polls Gmail
│  └─ Detects new email from "Alice Corp"
│
├─ Cloud creates /Updates/EMAIL_001.md
│  ├─ From: alice@corp.example.com
│  ├─ Subject: Project Proposal
│  ├─ Body: [email content]
│  └─ draft_reply: [AI-generated response]
│
└─ Vault Sync Agent (Cloud) pushes to git
   └─ `git add vault/Updates/ && git commit && git push`
   └─ Local will see this next sync

─────────────────────────────────────────────

5:00 PM - USER RETURNS (User goes online)
├─ Local Vault Sync Agent pulls from git
│  ├─ Downloads /Updates/EMAIL_001.md
│  └─ Processes: Needs approval
│
├─ Moves to /Pending_Approval/EMAIL_001.md
│  └─ User notification: "📧 Email draft awaiting approval"
│
└─ User opens Obsidian, reviews:
   ├─ Original email from alice@corp.example.com
   ├─ Suggested reply (drafted by AI on cloud)
   └─ [User reads and makes decision]

─────────────────────────────────────────────

5:05 PM - USER APPROVES
├─ User moves /Pending_Approval/EMAIL_001.md
│  → /Approved/EMAIL_001.md
│  (Git detects file move)
│
├─ User commits:
│  └─ `git add vault/Approved/ && git commit -m "approve: Reply to alice@corp"`
│
└─ User pushes to git
   └─ Cloud will see this on next sync

─────────────────────────────────────────────

5:06 PM - LOCAL EXECUTES
├─ Local Orchestrator detects /Approved/EMAIL_001.md
│
├─ Calls Email MCP (local instance):
│  ├─ Tool: send_email
│  ├─ To: alice@corp.example.com
│  ├─ Subject: Re: Project Proposal
│  ├─ Body: [approved draft from AI]
│  └─ MCP calls Gmail API (user's credentials)
│
├─ Gmail sends email
│  └─ ✅ Email sent successfully
│
├─ Log to /vault/Logs/email_sent.jsonl
│  ├─ timestamp: 2026-01-18T17:06:30Z
│  ├─ action: send_email
│  ├─ status: success
│  ├─ to: alice@corp.example.com
│  └─ message_id: Msg_12345
│
└─ Move to /Done/EMAIL_001_SENT.md
   └─ Archive & mark as complete

─────────────────────────────────────────────

5:07 PM - CLOUD SYNCS NEXT
├─ Cloud Vault Sync (periodic) pulls changes
│
├─ Sees /Approved/EMAIL_001.md (user approved)
│
├─ Updates Dashboard.md
│  └─ Shows: 1 completed email, 0 pending

─────────────────────────────────────────────

RESULT: ✅ Email processed
├─ Cloud drafted: 0 latency (no waiting)
├─ Local approved: User reviewed at convenience
├─ Local executed: Only local can send (user's Gmail auth)
└─ Git audit trail: Every change logged + committed
```

## Claim-by-Move Pattern

Prevents Cloud and Local from claiming the same task:

```
NEEDS_ACTION/EMAIL_001.md         ← New action
         ↓
    (Cloud claims by moving)
         ↓
IN_PROGRESS/cloud/EMAIL_001.md    ← Cloud working on it
         ↓
         (Git commit: "cloud: Processing email")
         ↓
    (30 seconds later, Cloud finishes draft)
         ↓
UPDATES/EMAIL_001.md              ← Cloud output ready
         ↓
    (Local pulls changes, git merge succeeds)
         ↓
PENDING_APPROVAL/EMAIL_001.md     ← Local moves it
         ↓
         (User reviews)
         ↓
APPROVED/EMAIL_001.md             ← User approves
         ↓
    (Local executes via MCP)
         ↓
DONE/EMAIL_001_SENT.md            ← Complete
```

**Safety**: If both Cloud and Local try to claim same task:
```bash
# Cloud moves first:
git add IN_PROGRESS/cloud/EMAIL_001.md

# Local tries to move same file (conflict):
git pull  # Git merge conflict!
# → CONFLICT: Both trying to claim EMAIL_001
# → Must resolve: Mark only in one location
# → Update .gitignore or use vault_sync to prevent
```

## Phases

### Phase 1: Infrastructure ✅ (This task)

- ✅ Remove Xero
- ✅ Set up Odoo (Docker Compose)
- ✅ Create Odoo MCP server
- ✅ Create vault sync agent
- ✅ Prepare Oracle Cloud docs
- → Create cloud_orchestrator.py
- → Create local_orchestrator.py

### Phase 2: Cloud Deployment (Next)

- Deploy to Oracle Cloud Free Tier
- Configure cloud watchers
- Start vault sync
- Test Cloud → Local communication

### Phase 3: Local Integration

- Configure local orchestrator
- Set up approval workflows
- Create Platinum demo flow
- Test full end-to-end

### Phase 4: Production Hardening

- Error recovery
- Health monitoring
- Backup strategies
- Security audit

## File Structure

```
DigitalFTE/
├── .env                          # Local secrets only
├── .env.example                  # Template (no secrets)
├── docker-compose.yml            # Odoo + PostgreSQL
├── odoo.conf                     # Odoo configuration
│
├── agents/
│   ├── orchestrator.py           # Main (original, will split)
│   ├── cloud_orchestrator.py     # NEW: Cloud watchers + drafting
│   ├── local_orchestrator.py     # NEW: Approval + execution
│   ├── vault_sync_agent.py       # NEW: Git sync
│   ├── gmail_watcher.py          # Cloud: Email
│   ├── twitter_watcher.py        # Cloud: Tweets
│   ├── linkedin_watcher.py       # Cloud: LinkedIn
│   └── whatsapp_watcher.py       # Local: WhatsApp webhook
│
├── mcp_servers/
│   ├── email_mcp/                # Gmail (draft + send)
│   ├── twitter_mcp/              # Twitter (post)
│   ├── meta_social_mcp/          # Facebook/Instagram
│   ├── odoo_mcp/                 # Odoo (invoices, payments)
│   └── browser_mcp/              # Future automation
│
├── vault/
│   ├── Dashboard.md              # Status (updated by sync)
│   ├── Company_Handbook.md       # Rules
│   ├── Needs_Action/             # Input queue
│   ├── Updates/                  # Cloud output (git synced)
│   ├── Plans/                    # AI reasoning
│   ├── In_Progress/
│   │   ├── cloud/                # Cloud claiming
│   │   └── local/                # Local claiming
│   ├── Pending_Approval/         # Awaiting human
│   ├── Approved/                 # Ready to execute
│   ├── Done/                     # Completed
│   ├── Logs/                     # Audit trail
│   │   ├── YYYY-MM-DD.json
│   │   ├── vault_sync.jsonl      # Sync audit
│   │   └── odoo_transactions.jsonl
│   └── Accounting/
│       ├── Rates.md
│       └── [Odoo-related docs]
│
└── docs/
    ├── PLATINUM_TIER.md          # This file
    ├── ODOO_SETUP.md             # Local Odoo setup
    ├── ORACLE_CLOUD_DEPLOYMENT.md # Cloud VM setup
    └── [other docs]
```

## Environment Variables

### Cloud VM (.env)

```env
# Only cloud secrets
AGENT_TYPE=cloud
OPENAI_API_KEY=sk-...
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
TWITTER_API_KEY=...

# Vault sync
VAULT_PATH=/home/ubuntu/projects/DigitalFTE/vault
GIT_REMOTE=origin
GIT_BRANCH=main
VAULT_SYNC_INTERVAL=300
```

### Local Machine (.env)

```env
# Only local secrets
AGENT_TYPE=local
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_SESSION_PATH=...
ODOO_PASSWORD=...

# Vault sync
VAULT_PATH=/Users/user/DigitalFTE/vault
GIT_REMOTE=origin
GIT_BRANCH=main
VAULT_SYNC_INTERVAL=300
```

## Integration Checklist

- [ ] Odoo running locally (Docker Compose)
- [ ] Odoo MCP server working
- [ ] Cloud VM provisioned (Oracle Cloud)
- [ ] Cloud watchers running (Gmail, Twitter, LinkedIn)
- [ ] Vault sync agent working (git push/pull)
- [ ] Local vault sync agent pulling changes
- [ ] Cloud/Local folder structure created
- [ ] Security: No secrets in synced files
- [ ] Claim-by-move testing passed
- [ ] Platinum demo flow end-to-end tested

## Monitoring Dashboard

Local Obsidian Dashboard.md shows:

```markdown
# DigitalFTE Status

**Updated**: 2026-01-18 17:30:00

## Queue Status

| Stage | Count |
|-------|-------|
| Needs Action | 3 |
| In Progress (Cloud) | 1 |
| In Progress (Local) | 0 |
| Pending Approval | 2 |
| Approved (Ready) | 1 |
| Done (Completed) | 47 |

## Agents Status

| Agent | Type | Last Sync | Status |
|-------|------|-----------|--------|
| Cloud VM | Always-On | 5 min ago | ✅ Healthy |
| Local Sync | Periodic | 2 min ago | ✅ Synced |
| Odoo | Local | OK | ✅ Running |

## Recent Activity

- 17:06: Email reply sent to alice@corp.example.com
- 17:00: Cloud drafted Twitter response (pending approval)
- 16:55: Vault sync: Pulled 2 cloud updates
```

## Performance Targets

- **Email draft generation**: < 30 seconds (cloud, async)
- **Cloud → Local sync**: Every 5 minutes
- **Local → Cloud push**: Immediate (on approval)
- **Final execution**: < 10 seconds (from approval)
- **Total latency** (email arrival → send): < 1 hour (includes human review time)

## Troubleshooting Guide

### Cloud Not Pushing

```bash
# SSH into cloud VM
ssh -i key.pem ubuntu@IP

# Check service
systemctl status digitalfte-vault-sync

# Check git
cd ~/projects/DigitalFTE
git log --oneline -5
git remote -v

# Push manually
git push origin main
```

### Local Not Pulling

```bash
# Check sync agent
ps aux | grep vault_sync

# Manual pull
cd ~/DigitalFTE
git pull origin main

# Verify /Updates/ was pulled
ls -la vault/Updates/
```

### Approval Not Working

```bash
# Check /Approved/ folder
ls -la vault/Approved/

# Check orchestrator logs
tail -100 vault/Logs/orchestrator.log

# Try manual execution
python3 agents/local_orchestrator.py --debug
```

## Next Steps

1. ✅ Phase 1: Infrastructure done (Odoo, Sync, Cloud docs)
2. → Phase 2: Create cloud_orchestrator.py
3. → Phase 3: Create local_orchestrator.py
4. → Phase 4: Test full Platinum demo
5. → Phase 5: Deploy to Oracle Cloud
6. → Phase 6: Production hardening

## References

- [Git-Based Vault Sync](../agents/vault_sync_agent.py)
- [Odoo MCP Server](../mcp_servers/odoo_mcp/README.md)
- [Oracle Cloud Deployment](./ORACLE_CLOUD_DEPLOYMENT.md)
- [Odoo Local Setup](./ODOO_SETUP.md)
