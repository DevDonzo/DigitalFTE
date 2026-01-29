# Cloud Architecture Deployment Guide

**Status**: Cloud + Local Split Architecture Ready

---

## Architecture Overview

```
┌─────────────────────────────────────┐
│  CLOUD VM (Oracle Free Tier)       │
│  ├─ Gmail Watcher (24/7)           │
│  ├─ Twitter Watcher                │
│  ├─ Cloud Orchestrator              │
│  ├─ Odoo Container (accounting)    │
│  └─ Draft Generator (AI/OpenAI)│
│      ↓                              │
│  Writes: vault/Updates/             │
└─────────────┬───────────────────────┘
              │
         Git Sync (auto)
              │
              ↓
┌─────────────────────────────────────┐
│  LOCAL MACHINE (Your Laptop)        │
│  Reads: vault/Updates/              │
│      ↓                              │
│  Human reviews in Obsidian          │
│      ↓                              │
│  Moves to: vault/Approved/          │
│      ↓                              │
│  Local Orchestrator executes:       │
│  ├─ Send emails (Gmail MCP)        │
│  ├─ Post social (Twitter/Meta MCP)  │
│  ├─ WhatsApp (Twilio)              │
│  ├─ Payments (Odoo MCP)            │
│  └─ Writes: vault/Done/             │
└─────────────────────────────────────┘
```

---

## Quick Start

### 1. Deploy Cloud Agent

```bash
# From local machine
./scripts/deploy_cloud.sh <ORACLE_VM_IP>
```

### 2. Start Local Agent

```bash
# On local machine
./scripts/start_local.sh
```

### 3. Open Obsidian

```bash
open -a Obsidian vault/
```

---

## Detailed Setup

### Cloud VM Setup (Oracle Free Tier)

**1. Create VM** (see DEPLOYMENT_GUIDE.md)
- Ubuntu 22.04
- VM.Standard.A1.Flex (1 OCPU, 6GB RAM)
- Always Free

**2. Setup Git Authentication**

```bash
# On cloud VM
ssh-keygen -t ed25519 -C "cloud-agent@digitalfte"
cat ~/.ssh/id_ed25519.pub
# Add to GitHub deploy keys
```

**3. Clone Repository**

```bash
git clone git@github.com:DevDonzo/DigitalFTE.git
cd DigitalFTE
```

**4. Configure Cloud .env**

```bash
cp .env.example .env.cloud
nano .env.cloud
```

**Cloud .env (SAFE TO SYNC - NO SECRETS)**:
```env
VAULT_PATH=./vault
AGENT_TYPE=cloud
CLOUD_WATCHERS=gmail,twitter,linkedin

# Gmail (read-only watcher)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...

# OpenAI (for drafting)
OPENAI_API_KEY=sk-...

# Twitter (read-only watcher)
TWITTER_API_KEY=...

# LinkedIn (read-only)
LINKEDIN_ACCESS_TOKEN=...

# Odoo (cloud instance)
ODOO_URL=http://localhost:8069
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=...
```

**5. Start Cloud Services**

```bash
# Start Odoo
docker-compose up -d

# Start Cloud Orchestrator
pm2 start agents/cloud_orchestrator.py --interpreter python3.13 --name cloud-orchestrator
pm2 start agents/gmail_watcher.py --interpreter python3.13 --name gmail-watcher

# Save PM2 config
pm2 save
pm2 startup
```

**6. Setup Git Auto-Sync (Cloud → Local)**

```bash
# Create sync script
cat > ~/sync_vault.sh << 'EOF'
#!/bin/bash
cd ~/DigitalFTE
git add vault/Updates vault/Needs_Action
git commit -m "Cloud: sync updates $(date +%Y-%m-%d_%H:%M)" || true
git pull --rebase origin main
git push origin main
EOF

chmod +x ~/sync_vault.sh

# Add to crontab (every 5 minutes)
(crontab -l; echo "*/5 * * * * ~/sync_vault.sh >> ~/sync.log 2>&1") | crontab -
```

---

### Local Machine Setup

**1. Configure Local .env**

```bash
# Use existing .env (includes ALL secrets)
nano .env
```

**Local .env (NEVER SYNC - HAS ALL SECRETS)**:
```env
VAULT_PATH=./vault
AGENT_TYPE=local

# All Gmail credentials (read + write)
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...

# WhatsApp (LOCAL ONLY)
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...

# Payment/Banking (LOCAL ONLY)
ODOO_URL=http://localhost:8069
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=...

# All social media (with post permissions)
TWITTER_API_KEY=...
FACEBOOK_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ACCOUNT_ID=...
```

**2. Setup Git Auto-Pull (Local)**

```bash
# Local machine pulls cloud updates automatically
./scripts/start_local.sh
```

This starts:
- Git auto-pull every 5 minutes
- Local orchestrator (approval monitor)

**3. Monitor in Obsidian**

```bash
open -a Obsidian vault/
```

Watch for new files in:
- `vault/Updates/` - Drafts from cloud
- `vault/Pending_Approval/` - Ready for review

---

## Workflows

### Email Workflow (Platinum Demo)

**Cloud Agent (24/7)**:
1. Gmail Watcher detects new email
2. Creates `vault/Needs_Action/email/EMAIL_xxx.md`
3. Cloud Orchestrator reads it
4. Generates draft reply (OpenAI)
5. Writes `vault/Updates/EMAIL_REPLY_xxx.md`
6. Git commits + pushes

**Local Agent (when online)**:
1. Git pulls new updates
2. Reads `vault/Updates/EMAIL_REPLY_xxx.md`
3. Moves to `vault/Pending_Approval/email/`
4. **YOU review in Obsidian**
5. You move to `vault/Approved/`
6. Local Orchestrator detects approval
7. Executes: Sends email via Gmail MCP
8. Logs to `vault/Logs/emails_sent.jsonl`
9. Moves to `vault/Done/`
10. Git commits + pushes

### Social Media Workflow

**Cloud Agent**:
1. Twitter Watcher detects @mention
2. Generates draft reply
3. Writes `vault/Updates/TWITTER_REPLY_xxx.md`

**Local Agent**:
1. You review and approve
2. Local Orchestrator posts via Twitter MCP
3. Logs result

---

## Security Rules

### What Cloud Agent CAN Access:
- ✅ Gmail (read-only API)
- ✅ Twitter/LinkedIn (read-only)
- ✅ OpenAI (draft generation)
- ✅ Odoo (read-only accounting queries)

### What Cloud Agent CANNOT Access:
- ❌ WhatsApp credentials
- ❌ Payment/banking tokens
- ❌ Send email permissions
- ❌ Post to social media permissions

### Git Sync Security:
- ✅ Sync: All `.md` files in vault
- ✅ Sync: `vault/Updates/`, `vault/Needs_Action/`
- ❌ NEVER sync: `.env`, `*.token.json`, `whatsapp_session/`
- ❌ NEVER sync: `vault/In_Progress/` (local tracking only)

---

## Claim-by-Move Rule

Prevents double work when both agents are running:

1. Cloud creates: `vault/Needs_Action/email/EMAIL_123.md`
2. Cloud moves to: `vault/In_Progress/cloud/EMAIL_123.md`
3. Cloud processes and writes draft
4. Local sees file in `/In_Progress/cloud/` → **IGNORES IT**
5. Only after Cloud moves to `/Updates/` does Local process it

**Rule**: First agent to move file to `/In_Progress/<agent>/` owns it.

---

## Monitoring

### Cloud VM

```bash
ssh ubuntu@<VM_IP>

# View orchestrator logs
pm2 logs cloud-orchestrator

# Check git sync
tail -f ~/sync.log

# Check Odoo
docker-compose logs -f odoo
```

### Local Machine

```bash
# View local orchestrator logs
tail -f vault/Logs/local_orchestrator.log

# Check git status
git status

# Monitor approvals
watch -n 5 'ls vault/Pending_Approval/email/'
```

---

## Platinum Demo Test

**Scenario**: Email arrives while local is offline

```bash
# 1. On cloud VM
# Manually create test email
cat > vault/Needs_Action/email/EMAIL_TEST_001.md << 'EOF'
---
from: test@example.com
subject: Test inquiry
type: email
---

Hi, I'm interested in your services. Can you provide pricing?
EOF

git add vault/Needs_Action/email/EMAIL_TEST_001.md
git commit -m "Test: Add email"
git push

# 2. Cloud orchestrator processes it (auto)
# Generates draft in vault/Updates/

# 3. On local machine (pull updates)
git pull

# 4. Check vault/Updates/ for draft
ls vault/Updates/

# 5. Review in Obsidian, move to Approved/

# 6. Local orchestrator sends email (auto)

# 7. Verify in vault/Done/
ls vault/Done/
```

---

## Troubleshooting

### Git conflicts

```bash
# Reset to cloud state
git fetch origin
git reset --hard origin/main
```

### Cloud not syncing

```bash
# Check cron
crontab -l

# Check sync script
~/sync_vault.sh

# View sync log
tail ~/sync.log
```

### Local not pulling updates

```bash
# Check if start_local.sh is running
ps aux | grep local_orchestrator

# Manual pull
git pull origin main
```

---

## Performance

**Expected Latency**:
- Email arrives → Cloud drafts: **< 2 minutes**
- Cloud commits → Local pulls: **< 5 minutes**
- Local approval → Execution: **< 30 seconds**
- Total (email to send): **< 10 minutes** (when local is online)

**Offline Handling**:
- Cloud continues drafting 24/7
- Local executes when online
- No data loss (all in git)

---

## Cost

**Cloud VM (Oracle Free Tier)**: $0/month
**Git hosting (GitHub Free)**: $0/month
**APIs**:
- OpenAI: ~$20-50/month (GPT-4 drafting)
- Gmail API: Free
- Twitter API: Free (basic)

**Total**: ~$20-50/month

---

## Next Steps

1. Deploy cloud agent: `./scripts/deploy_cloud.sh <VM_IP>`
2. Start local agent: `./scripts/start_local.sh`
3. Test email workflow (see Platinum Demo Test)
4. Monitor for 24 hours
5. Verify git sync works
6. Add HTTPS to Odoo (see DEPLOYMENT_GUIDE.md)

---

**Status**: ✅ Cloud Architecture Ready to Deploy
