# Deployment Guide - DigitalFTE

**Comprehensive guide for deploying your Personal AI Employee locally or in the cloud**

---

## Table of Contents

1. [Local Deployment](#local-deployment)
2. [Cloud Deployment (Oracle Free Tier)](#cloud-deployment-oracle-free-tier)
3. [Docker Deployment](#docker-deployment)
4. [Production Checklist](#production-checklist)
5. [Maintenance & Monitoring](#maintenance--monitoring)
6. [Troubleshooting](#troubleshooting)

---

## Local Deployment

### Prerequisites

- macOS, Linux, or Windows 10/11
- Python 3.13+
- Node.js 24+ LTS
- Docker & Docker Compose (for Odoo)
- 8GB RAM minimum (16GB recommended)
- 20GB free disk space

### Step 1: Clone Repository

```bash
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE
```

### Step 2: Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies (for MCP servers)
npm install

# Install MCP servers
cd mcp_servers/email_mcp && npm install && cd ../..
cd mcp_servers/odoo_mcp && npm install && cd ../..
cd mcp_servers/twitter_mcp && npm install && cd ../..
cd mcp_servers/meta_social_mcp && npm install && cd ../..
cd mcp_servers/browser_mcp && npm install && cd ../..
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Minimum Required Environment Variables**:

```env
# Vault Location
VAULT_PATH=./vault

# Gmail (Required for email features)
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=GOCSPX-your_secret
GMAIL_PROJECT_ID=your-project-id

# OpenAI (Required for AI drafting)
OPENAI_API_KEY=sk-...

# Odoo (Required for accounting)
ODOO_URL=http://localhost:8069
ODOO_DB=gte
ODOO_USERNAME=admin
ODOO_PASSWORD=your_secure_password

# Optional APIs
TWILIO_ACCOUNT_SID=AC...
TWILIO_AUTH_TOKEN=...
TWITTER_API_KEY=...
FACEBOOK_ACCESS_TOKEN=...
LINKEDIN_API_KEY=...
```

### Step 4: Start Odoo (Docker)

```bash
# Start Odoo Community Edition
docker-compose up -d

# Wait for Odoo to start (30-60 seconds)
docker-compose logs -f odoo

# Access Odoo web interface
open http://localhost:8069
```

**Odoo Initial Setup**:
1. Create database: `gte`
2. Set master password: `ODOO_PASSWORD` from .env
3. Install modules: `account`, `sale`, `purchase`
4. Create admin user (or use default `admin:admin`)

### Step 5: Run Verification

```bash
python Setup_Verify.py
```

Expected output:
```
✅ Vault structure
✅ MCP servers
✅ Agent Skills
✅ Python modules
```

### Step 6: Start the System

Open 4 terminal windows:

**Terminal 1: Main Orchestrator**
```bash
python agents/orchestrator.py
```

**Terminal 2: Gmail Watcher**
```bash
python agents/gmail_watcher.py
```

**Terminal 3: WhatsApp Webhook Server**
```bash
python agents/webhook_server.py
```

**Terminal 4: Watchdog (Health Monitor)**
```bash
python agents/watchdog.py
```

### Step 7: Open Obsidian Vault

```bash
# Open Obsidian and point to ./vault directory
open -a Obsidian vault/
```

---

## Cloud Deployment (Oracle Free Tier)

### Why Oracle Cloud Free Tier?

- **Always Free**: 2 VMs with 1GB RAM each
- **24/7 uptime**: Perfect for watchers and orchestrator
- **50GB block storage**: Sufficient for logs and vault
- **Free outbound data transfer**: 10TB/month
- **No credit card required**: Truly free

### Architecture

```
┌──────────────────────────────────────┐
│  Cloud VM (Oracle Free Tier)         │
│  • Gmail Watcher (always-on)         │
│  • WhatsApp Webhook (24/7)           │
│  • Odoo Container (Docker)           │
│  • Orchestrator (cloud mode)         │
└────────────────┬─────────────────────┘
                 │
          Git-based sync
                 │
                 ↓
┌──────────────────────────────────────┐
│  Local Machine (Your Laptop)         │
│  • Approval/execution                │
│  • Sensitive actions (payments)      │
│  • Local orchestrator                │
└──────────────────────────────────────┘
```

### Step 1: Create Oracle Cloud Account

1. Go to https://www.oracle.com/cloud/free/
2. Sign up (no credit card required)
3. Verify email
4. Log in to console

### Step 2: Create VM Instance

**Compute → Instances → Create Instance**

- **Image**: Ubuntu 22.04 LTS
- **Shape**: VM.Standard.A1.Flex (ARM, 1 OCPU, 6GB RAM) - Always Free
- **Boot Volume**: 50GB
- **Network**: Default VCN
- **SSH Keys**: Generate or upload your public key

### Step 3: Configure Firewall

**Networking → Virtual Cloud Networks → Security Lists**

Add ingress rules:
- Port 8069 (Odoo web interface)
- Port 8001 (WhatsApp webhook)
- Port 22 (SSH)

### Step 4: Connect to VM

```bash
ssh -i ~/.ssh/oracle_key ubuntu@<VM_PUBLIC_IP>
```

### Step 5: Install Dependencies on VM

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.13
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv python3.13-dev -y

# Install Node.js 24
curl -fsSL https://deb.nodesource.com/setup_24.x | sudo -E bash -
sudo apt install -y nodejs

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Install git
sudo apt install git -y
```

### Step 6: Clone & Setup on VM

```bash
# Clone repository
git clone https://github.com/DevDonzo/DigitalFTE.git
cd DigitalFTE

# Install Python dependencies
python3.13 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Install Node dependencies
npm install

# Setup MCP servers
for mcp in email_mcp odoo_mcp twitter_mcp meta_social_mcp browser_mcp; do
    cd mcp_servers/$mcp && npm install && cd ../..
done

# Copy environment file
cp .env.example .env
nano .env  # Edit with your credentials
```

### Step 7: Start Services with PM2

```bash
# Install PM2 globally
sudo npm install -g pm2

# Start Odoo
docker-compose up -d

# Start watchers and orchestrator with PM2
pm2 start agents/gmail_watcher.py --interpreter python3.13 --name gmail-watcher
pm2 start agents/whatsapp_watcher.py --interpreter python3.13 --name whatsapp-watcher
pm2 start agents/orchestrator.py --interpreter python3.13 --name orchestrator
pm2 start agents/watchdog.py --interpreter python3.13 --name watchdog

# Save PM2 configuration
pm2 save

# Setup PM2 to start on boot
pm2 startup
# Run the command PM2 outputs
```

### Step 8: Configure Nginx Reverse Proxy (Optional)

```bash
# Install Nginx
sudo apt install nginx -y

# Create Odoo site config
sudo nano /etc/nginx/sites-available/odoo
```

**Nginx Configuration**:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8069;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/odoo /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: Setup HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured by default
```

### Step 10: Monitor with PM2

```bash
# View all processes
pm2 list

# View logs
pm2 logs

# Monitor resources
pm2 monit

# Restart a service
pm2 restart orchestrator

# Stop all
pm2 stop all
```

---

## Docker Deployment

### Full Docker Compose Setup

**docker-compose.yml** (all services):

```yaml
version: '3.8'

services:
  # Odoo ERP
  odoo:
    image: odoo:19
    container_name: odoo
    depends_on:
      - db
    ports:
      - "8069:8069"
    environment:
      - HOST=db
      - USER=odoo
      - PASSWORD=${ODOO_PASSWORD}
    volumes:
      - odoo-data:/var/lib/odoo
      - ./odoo-config:/etc/odoo
    restart: always

  # PostgreSQL for Odoo
  db:
    image: postgres:15
    container_name: postgres
    environment:
      - POSTGRES_DB=postgres
      - POSTGRES_USER=odoo
      - POSTGRES_PASSWORD=${ODOO_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data
    restart: always

  # Gmail Watcher
  gmail-watcher:
    build:
      context: .
      dockerfile: Dockerfile.watcher
    container_name: gmail-watcher
    command: python agents/gmail_watcher.py
    volumes:
      - ./vault:/app/vault
      - ./.env:/app/.env
    restart: always

  # Orchestrator
  orchestrator:
    build:
      context: .
      dockerfile: Dockerfile.orchestrator
    container_name: orchestrator
    command: python agents/orchestrator.py
    volumes:
      - ./vault:/app/vault
      - ./.env:/app/.env
    depends_on:
      - odoo
    restart: always

  # Watchdog
  watchdog:
    build:
      context: .
      dockerfile: Dockerfile.watchdog
    container_name: watchdog
    command: python agents/watchdog.py
    volumes:
      - ./vault:/app/vault
      - ./.env:/app/.env
    restart: always

volumes:
  odoo-data:
  db-data:
```

**Dockerfile.watcher**:

```dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "agents/gmail_watcher.py"]
```

**Start all services**:

```bash
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all
docker-compose down
```

---

## Production Checklist

### Security

- [ ] Strong passwords set for all services
- [ ] `.env` file not committed to git (in `.gitignore`)
- [ ] Firewall configured (only necessary ports open)
- [ ] HTTPS enabled for public endpoints
- [ ] SSH key-based authentication (no password login)
- [ ] Odoo admin password changed from default
- [ ] API keys rotated monthly
- [ ] Vault directory backed up regularly

### Configuration

- [ ] All environment variables set in `.env`
- [ ] Gmail OAuth credentials configured
- [ ] OpenAI API key set
- [ ] Odoo database created and configured
- [ ] Twilio webhook URL set (if using WhatsApp)
- [ ] Social media API keys configured
- [ ] MCP servers installed and tested

### Monitoring

- [ ] PM2 configured for auto-restart
- [ ] Watchdog process running
- [ ] Log rotation configured
- [ ] Disk space monitoring enabled
- [ ] Email alerts for system failures
- [ ] Weekly CEO briefing generating successfully

### Performance

- [ ] Sufficient disk space (>10GB free)
- [ ] RAM usage monitored (< 80%)
- [ ] CPU usage acceptable (< 70% sustained)
- [ ] Database backups automated
- [ ] Vault synced to git repository

---

## Maintenance & Monitoring

### Daily Tasks

```bash
# Check system health
pm2 status

# View recent logs
pm2 logs --lines 50

# Check disk space
df -h

# Check Odoo status
docker-compose ps
```

### Weekly Tasks

```bash
# Review CEO briefing
cat vault/Briefings/$(date +%Y-%m-%d)_briefing.md

# Review audit logs
cat vault/Logs/$(date +%Y-%m-%d).json | jq .

# Backup vault
tar -czf backup-$(date +%Y%m%d).tar.gz vault/

# Update dependencies
pip list --outdated
npm outdated
```

### Monthly Tasks

```bash
# Rotate API keys
# Update .env with new credentials

# Update system packages
sudo apt update && sudo apt upgrade -y

# Review and prune old logs
find vault/Logs -name "*.json" -mtime +90 -delete

# Database optimization
docker-compose exec db vacuumdb -U odoo -d gte
```

### Monitoring Dashboard (Optional)

Install Grafana + Prometheus for advanced monitoring:

```bash
# Add monitoring to docker-compose.yml
# See: https://grafana.com/docs/grafana/latest/setup-grafana/installation/docker/
```

---

## Troubleshooting

### Issue: Gmail Watcher not detecting emails

**Solution**:
```bash
# Check credentials
python auth/gmail.py  # Re-authenticate

# Verify token file exists
ls -la ~/.gmail_token.json

# Check logs
pm2 logs gmail-watcher
```

### Issue: Odoo container won't start

**Solution**:
```bash
# Check logs
docker-compose logs odoo

# Restart container
docker-compose restart odoo

# Recreate container
docker-compose down
docker-compose up -d
```

### Issue: MCP server errors

**Solution**:
```bash
# Test MCP server manually
cd mcp_servers/odoo_mcp
node index.js --legacy-stdio
# Type: {"tool": "get_accounts", "input": {}}
# Should return JSON response

# Reinstall dependencies
npm install
```

### Issue: Out of disk space

**Solution**:
```bash
# Find large files
du -sh vault/* | sort -h

# Prune old logs
find vault/Logs -name "*.json" -mtime +90 -delete
find vault/Done -name "*.md" -mtime +180 -delete

# Clean Docker
docker system prune -a
```

### Issue: High memory usage

**Solution**:
```bash
# Identify memory hog
pm2 monit

# Restart services
pm2 restart all

# Increase VM memory (cloud) or reduce concurrent processes
```

---

## Backup & Recovery

### Automated Backups

**Cron job for daily vault backup**:

```bash
# Edit crontab
crontab -e

# Add daily backup at 2 AM
0 2 * * * cd ~/DigitalFTE && tar -czf ~/backups/vault-$(date +\%Y\%m\%d).tar.gz vault/
```

### Manual Backup

```bash
# Backup vault
tar -czf vault-backup.tar.gz vault/

# Backup Odoo database
docker-compose exec db pg_dump -U odoo gte > odoo-backup.sql

# Backup environment
cp .env env-backup.env
```

### Restore from Backup

```bash
# Restore vault
tar -xzf vault-backup.tar.gz

# Restore Odoo database
docker-compose exec -T db psql -U odoo gte < odoo-backup.sql

# Restore environment
cp env-backup.env .env
```

---

## Performance Optimization

### Tips for Fast Operation

1. **Enable caching** for Odoo queries
2. **Limit log file sizes** (rotate after 10MB)
3. **Use SSD storage** for vault directory
4. **Increase PM2 memory limit** if needed
5. **Optimize Docker images** (use slim variants)
6. **Enable Nginx gzip compression**
7. **Schedule intensive tasks** (CEO briefing) for off-peak hours

### Benchmarks (Expected)

- **Gmail check**: < 2 seconds
- **Email draft generation**: < 5 seconds (OpenAI)
- **Odoo invoice creation**: < 3 seconds
- **CEO briefing generation**: < 30 seconds
- **Memory usage**: 200-400 MB (all services)
- **CPU usage**: < 10% idle, < 30% active

---

## Support & Resources

- **Documentation**: See `README.md`, `ARCHITECTURE.md`
- **Issues**: Open GitHub issue at https://github.com/DevDonzo/DigitalFTE/issues
- **Oracle Cloud Docs**: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier.htm
- **Odoo Docs**: https://www.odoo.com/documentation
- **PM2 Docs**: https://pm2.keymetrics.io/docs/usage/quick-start/

---

## Deployment Checklist Summary

### Local Deployment
- [ ] Install dependencies (Python, Node, Docker)
- [ ] Configure `.env` file
- [ ] Start Odoo container
- [ ] Run `Setup_Verify.py`
- [ ] Start watchers, orchestrator, watchdog
- [ ] Open Obsidian vault

### Cloud Deployment (Oracle)
- [ ] Create Oracle Cloud account
- [ ] Create VM instance (Ubuntu 22.04)
- [ ] Configure firewall rules
- [ ] Install dependencies on VM
- [ ] Clone repository and setup
- [ ] Start services with PM2
- [ ] Configure Nginx reverse proxy
- [ ] Setup HTTPS with Let's Encrypt
- [ ] Enable automated backups
- [ ] Monitor with PM2

### Production Readiness
- [ ] Security hardening complete
- [ ] All API keys configured
- [ ] Monitoring enabled
- [ ] Backups automated
- [ ] Documentation reviewed
- [ ] Test end-to-end workflow

---

**Status**: Ready for deployment!

**Estimated Setup Time**:
- Local: 1-2 hours
- Cloud (Oracle): 2-3 hours
- Docker: 30 minutes

**Your DigitalFTE is ready to work 24/7!** 🚀
