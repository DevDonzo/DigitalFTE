# Oracle Cloud Free Tier Deployment Guide

Deploy DigitalFTE to Oracle Cloud Always-Free Virtual Machine (24/7 operation).

## Architecture Overview

```
LOCAL MACHINE (User)
├── Obsidian Vault (source of truth)
├── Local Orchestrator (approvals + execution)
├── WhatsApp Watcher (Twilio webhook)
├── Vault Sync Agent (git pull every 5 min)
└── Secrets: WhatsApp, Banking, Payment creds

                 ↔ Git Push/Pull ↔

ORACLE CLOUD VM (Always-On)
├── Cloud Orchestrator (watchers + drafting)
├── Email Watcher (Gmail polling)
├── Twitter Watcher (X API)
├── LinkedIn Watcher
├── Vault Sync Agent (git push every 5 min)
├── /Updates/ folder (cloud-generated drafts)
└── Secrets: Email, Twitter, LinkedIn creds
```

## Prerequisites

### Local Machine
- Git configured (push/pull access to repo)
- Python 3.10+
- Node.js 18+
- .env with local secrets configured

### Oracle Cloud Account
- Oracle Cloud Free Tier account (free)
- Credit card (for verification, not charged)
- Static IP address allocation

## Step 1: Create Oracle Cloud VM

### 1.1 Access Oracle Cloud Console

1. Sign in: https://cloud.oracle.com
2. Navigate to **Compute → Instances**
3. Click **Create Instance**

### 1.2 Configure Instance

**Basics:**
- **Name**: `digitalfte-cloud-agent`
- **Compartment**: (root)
- **Image**: Ubuntu 22.04 (Always-Free eligible)
- **Shape**: Ampere (ARM) - `VM.Standard.A1.Flex` (Always-Free)
  - **OCPUs**: 2 (4 available)
  - **Memory**: 12 GB

**Networking:**
- **VCN**: Create new or use existing
- **Subnet**: Create new
- **Public IP**: Assign

**Storage:**
- **Boot Volume Size**: 50 GB (within Always-Free limits)

**SSH Key:**
- Select **Generate SSH Key Pair**
- Download private key: `digitalfte-cloud.key`
- **IMPORTANT**: Save this securely!

### 1.3 Create Instance

Click **Create** and wait 2-3 minutes.

Note the **Public IP Address** (e.g., `140.238.xxx.xxx`)

## Step 2: Configure Network Security

### 2.1 Create Security Ingress Rules

In Oracle Cloud Console:

1. Go to **Virtual Cloud Networks → VCN Details**
2. Select **Security Lists → Default Security List**
3. **Add Ingress Rules**:

| Protocol | Source Port | Destination Port | CIDR | Purpose |
|----------|------------|-----------------|------|---------|
| TCP | 22 | 22 | 0.0.0.0/0 | SSH access |
| TCP | 443 | 443 | 0.0.0.0/0 | HTTPS (future) |
| TCP | 8001 | 8001 | YOUR_IP/32 | WhatsApp webhook (optional, from local) |

### 2.2 Get Static IP Address

1. Go to **Networking → Reserved Public IPs**
2. Click **Reserve Public IP Address**
3. Assign to your instance
4. Update DNS (if applicable)

## Step 3: SSH Into Instance

### 3.1 Connect

```bash
# Set permissions on key
chmod 600 digitalfte-cloud.key

# SSH into instance
ssh -i digitalfte-cloud.key ubuntu@<PUBLIC_IP>

# You should now have shell access to Ubuntu VM
```

### 3.2 Initial Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
  git \
  python3.10 \
  python3-pip \
  nodejs \
  npm \
  curl \
  wget \
  htop \
  tmux

# Verify installations
python3 --version  # Should be 3.10+
node --version     # Should be 14+
npm --version      # Should be 6+
git --version      # Should be 2.x+
```

## Step 4: Clone Repository

```bash
# Create directory
mkdir -p ~/projects
cd ~/projects

# Clone repo
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE

# Create .env for cloud agent (ONLY cloud secrets)
cat > .env << 'EOF'
# Cloud-Only Secrets (Never send local secrets to cloud!)
OPENAI_API_KEY=sk-...your_key
GMAIL_CLIENT_ID=...
GMAIL_CLIENT_SECRET=...
GMAIL_PROJECT_ID=...
TWITTER_API_KEY=...
TWITTER_API_SECRET=...
TWITTER_BEARER_TOKEN=...
TWITTER_ACCESS_TOKEN=...
TWITTER_ACCESS_TOKEN_SECRET=...
LINKEDIN_ACCESS_TOKEN=...

# Odoo (accessible from cloud, configured locally)
ODOO_URL=http://localhost:8069  # Will be cloud VM's Odoo if deployed
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=password_from_local

# Vault Sync
AGENT_TYPE=cloud
VAULT_PATH=/home/ubuntu/projects/DigitalFTE/vault
GIT_REMOTE=origin
GIT_BRANCH=main
VAULT_SYNC_INTERVAL=300

# System
LOG_LEVEL=INFO
DRY_RUN=false
EOF

# IMPORTANT: Configure git for commits
git config --global user.email "cloud@digitalfte.local"
git config --global user.name "Cloud Agent"
```

## Step 5: Install Python Dependencies

```bash
# Install pip dependencies
pip3 install -r requirements.txt

# Verify key packages
python3 -c "import google.oauth2; import openai; print('✓ Dependencies OK')"
```

## Step 6: Configure Cloud Watchers

### 6.1 Gmail Watcher (Email Monitoring)

```bash
# Test Gmail connection
python3 agents/gmail_watcher.py --test-connection

# If first time, it will prompt for OAuth login
# Follow the browser popup to authorize
```

### 6.2 Twitter Watcher (Tweet Monitoring)

```bash
# Verify Twitter credentials in .env
# No additional setup needed - uses API keys
```

### 6.3 LinkedIn Watcher (Profile Monitoring)

```bash
# Verify LinkedIn token in .env
# Test connection
python3 -c "from agents.linkedin_watcher import LinkedInWatcher; w = LinkedInWatcher(); print('✓ LinkedIn OK')"
```

## Step 7: Set Up Vault Sync

### 7.1 Configure Git SSH Key

```bash
# Generate SSH key for git operations
ssh-keygen -t ed25519 -f ~/.ssh/digitalfte -C "cloud-agent@digitalfte"

# Get public key content
cat ~/.ssh/digitalfte.pub

# Add to GitHub/GitLab:
# 1. Go to repo Settings → Deploy Keys
# 2. Paste public key
# 3. Enable "Allow write access"
```

### 7.2 Update Git Remote

```bash
# Use SSH instead of HTTPS
git remote set-url origin git@github.com:DevDonzo/DigitalFTE.git

# Test connection
git fetch origin
```

## Step 8: Start Cloud Services

### 8.1 Start Vault Sync Agent

```bash
# Run in background using tmux
tmux new-session -d -s vault_sync "cd ~/projects/DigitalFTE && python3 agents/vault_sync_agent.py"

# View logs
tmux attach -t vault_sync

# Detach: Ctrl+B, then D
```

### 8.2 Start Cloud Orchestrator (subset)

```bash
# For now, just start watchers
# Create a cloud-specific orchestrator later

# Start Gmail watcher
tmux new-session -d -s email_watcher "cd ~/projects/DigitalFTE && python3 agents/gmail_watcher.py"

# Start Twitter watcher
tmux new-session -d -s twitter_watcher "cd ~/projects/DigitalFTE && python3 agents/twitter_watcher.py"

# View all tmux sessions
tmux ls
```

### 8.3 Create Systemd Services (Persistent)

Create `/etc/systemd/system/digitalfte-vault-sync.service`:

```bash
sudo tee /etc/systemd/system/digitalfte-vault-sync.service << 'EOF'
[Unit]
Description=DigitalFTE Vault Sync Agent
After=network.target
StartLimitIntervalSec=60
StartLimitBurst=3

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/projects/DigitalFTE
Environment="PYTHONUNBUFFERED=1"
Environment="AGENT_TYPE=cloud"
ExecStart=/usr/bin/python3 agents/vault_sync_agent.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl enable digitalfte-vault-sync
sudo systemctl start digitalfte-vault-sync

# Check status
sudo systemctl status digitalfte-vault-sync

# View logs
sudo journalctl -u digitalfte-vault-sync -f
```

Create similar services for each watcher:
- `digitalfte-gmail-watcher.service`
- `digitalfte-twitter-watcher.service`
- `digitalfte-linkedin-watcher.service`

## Step 9: Monitor Cloud Agent

### 9.1 Check Health

```bash
# SSH into cloud VM
ssh -i digitalfte-cloud.key ubuntu@<PUBLIC_IP>

# Check services
sudo systemctl status digitalfte-*

# View recent vault sync
tail -50 /home/ubuntu/projects/DigitalFTE/vault/Logs/vault_sync.jsonl

# Check for errors in email watcher
tail -100 /home/ubuntu/projects/DigitalFTE/vault/Logs/email_watcher.log
```

### 9.2 Monitor Disk/Memory

```bash
# SSH into VM
ssh -i digitalfte-cloud.key ubuntu@<PUBLIC_IP>

# Check resources
df -h          # Disk usage
free -h        # Memory usage
htop           # Real-time monitoring (press q to exit)

# Check uptime
uptime
```

### 9.3 Restart Services

```bash
# Restart vault sync
sudo systemctl restart digitalfte-vault-sync

# Restart all
sudo systemctl restart digitalfte-*

# Check logs after restart
sudo journalctl -u digitalfte-vault-sync -n 50
```

## Step 10: Integrate with Local Machine

### 10.1 Configure Local .env

On LOCAL machine, ensure .env has:

```env
# Local-Only Secrets (NEVER push to cloud!)
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_SESSION_PATH=...

# Banking/Payment creds
XERO_CLIENT_SECRET=...  # Or equivalent for banking system
BANK_ACCOUNT_CODE=...

# Vault Sync (Local)
AGENT_TYPE=local
VAULT_SYNC_INTERVAL=300
GIT_REMOTE=origin
GIT_BRANCH=main
```

### 10.2 Start Local Vault Sync

```bash
# On LOCAL machine
python3 agents/vault_sync_agent.py

# Should pull from origin (cloud's pushes)
# And manage /Pending_Approval/ folder
```

### 10.3 Test Cloud ↔ Local Communication

1. **Create test file on cloud**:
   ```bash
   # SSH into cloud
   ssh -i digitalfte-cloud.key ubuntu@<PUBLIC_IP>

   # Create test update
   echo "Test from cloud" > /home/ubuntu/projects/DigitalFTE/vault/Updates/test_cloud.md

   # Push to git
   cd /home/ubuntu/projects/DigitalFTE
   git add vault/Updates/test_cloud.md
   git commit -m "test: Cloud update"
   git push origin main
   ```

2. **Pull on local**:
   ```bash
   # Local machine
   git pull origin main
   ls vault/Updates/  # Should see test_cloud.md
   ```

3. **Delete test file** and commit to confirm sync works bidirectionally.

## Step 11: Backup Strategy

### 11.1 Database Backups

If deploying Odoo to cloud VM:

```bash
# Daily backup script
cat > ~/backup_odoo.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR
docker-compose exec -T postgres pg_dump -U odoo gte | \
  gzip > $BACKUP_DIR/odoo_backup_$(date +%Y%m%d_%H%M%S).sql.gz
find $BACKUP_DIR -type f -name "*.gz" -mtime +30 -delete  # Keep 30 days
EOF

chmod +x ~/backup_odoo.sh

# Schedule daily (crontab -e)
# 0 2 * * * /home/ubuntu/backup_odoo.sh
```

### 11.2 Vault Backups

Vault is already backed up via git. Configure GitHub branch protection:

**GitHub → Settings → Branches → Branch Protection**
- Require pull request reviews
- Require status checks to pass
- Dismiss stale reviews when new commits pushed

## Step 12: Troubleshooting

### Cannot SSH

```bash
# Verify key permissions (local machine)
ls -la digitalfte-cloud.key  # Should be 600

# Verify security rules in Oracle Console
# Must have port 22 (SSH) open from your IP

# Test connectivity
ssh -vvv -i digitalfte-cloud.key ubuntu@<PUBLIC_IP>
```

### Services Not Starting

```bash
# Check systemd status
sudo systemctl status digitalfte-*

# View error logs
sudo journalctl -u digitalfte-vault-sync -n 100 -p error

# Try running manually to see error
cd ~/projects/DigitalFTE
python3 agents/vault_sync_agent.py
```

### Git Push Fails on Cloud

```bash
# Verify SSH key
ssh -T git@github.com  # Should authenticate without password

# Check git config
git config --list | grep user

# Update remote
git remote -v
git remote set-url origin git@github.com:DevDonzo/DigitalFTE.git
```

### Out of Storage

```bash
# Check disk usage
df -h

# Clean old logs (if not synced)
rm -f /home/ubuntu/projects/DigitalFTE/vault/Logs/*.json.old

# Expand volume in Oracle Console if needed
# (requires instance stop + volume resize)
```

## Step 13: Cost Management

Oracle Cloud Always-Free includes:

- **1x VM.Standard.A1.Flex** (2 OCPUs, 12 GB RAM) ✓
- **200 GB storage** ✓
- **1 TB outbound data transfer/month** ✓

**Tips to avoid charges**:
- Use only Ampere (ARM) shapes, not x86
- Keep volume under 200 GB
- Monitor data transfer (vault sync uses minimal bandwidth)
- Set up billing alerts

View usage: **Billing → Cost Analysis**

## Monitoring & Alerts

### 13.1 Email Alerts

Create CloudWatch-like monitoring script:

```bash
cat > ~/check_cloud_health.sh << 'EOF'
#!/bin/bash

# Check if services are running
FAILED=0
for service in digitalfte-vault-sync digitalfte-gmail-watcher; do
  if ! systemctl is-active --quiet $service; then
    echo "ALERT: $service is not running"
    FAILED=1
  fi
done

# Check disk space
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
  echo "ALERT: Disk usage at ${DISK_USAGE}%"
  FAILED=1
fi

# Check available memory
FREE_MEM=$(free | grep Mem | awk '{print ($3/$2)*100}')
if (( $(echo "$FREE_MEM > 80" | bc -l) )); then
  echo "ALERT: Memory usage at ${FREE_MEM}%"
  FAILED=1
fi

exit $FAILED
EOF

chmod +x ~/check_cloud_health.sh

# Run hourly
# 0 * * * * /home/ubuntu/check_cloud_health.sh
```

## Next Steps

1. ✅ Cloud VM running on Oracle Cloud
2. ✅ Git vault sync pushing cloud updates
3. ✅ Watchers (Email, Twitter, LinkedIn) active
4. → Create cloud_orchestrator.py (draft generation)
5. → Create local_orchestrator.py (approval + execution)
6. → Test Platinum demo flow

## Support & Docs

- **Oracle Cloud Docs**: https://docs.oracle.com/en-us/iaas/
- **Always Free Limits**: https://www.oracle.com/cloud/free/
- **SSH Troubleshooting**: https://docs.oracle.com/en-us/iaas/Content/Compute/References/SSHTroubleshooting.htm
- **Networking**: https://docs.oracle.com/en-us/iaas/Content/Network/

## Security Checklist

- [ ] SSH key backed up securely
- [ ] .env with only cloud secrets (no local creds)
- [ ] Git credentials configured via SSH (not HTTPS)
- [ ] Firewall rules minimal (only needed ports)
- [ ] Regular vault backups via git
- [ ] Systemd services set to auto-restart
- [ ] Disk space monitored
- [ ] Memory monitored
- [ ] Error logs reviewed weekly
