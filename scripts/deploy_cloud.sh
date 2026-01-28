#!/bin/bash
# Deploy Cloud Orchestrator to Oracle Cloud VM
# Usage: ./scripts/deploy_cloud.sh <VM_IP>

set -e

VM_IP=${1:-""}
if [ -z "$VM_IP" ]; then
    echo "Usage: ./scripts/deploy_cloud.sh <VM_IP>"
    exit 1
fi

echo "🚀 Deploying Cloud Orchestrator to $VM_IP..."

# Create deployment tarball (exclude secrets)
echo "📦 Creating deployment package..."
tar -czf /tmp/digitalfte-cloud.tar.gz \
    --exclude='.env' \
    --exclude='*.token.json' \
    --exclude='whatsapp_session' \
    --exclude='vault/In_Progress' \
    --exclude='vault/Logs/*.jsonl' \
    --exclude='node_modules' \
    --exclude='.git' \
    .

# Copy to VM
echo "📤 Uploading to VM..."
scp /tmp/digitalfte-cloud.tar.gz ubuntu@$VM_IP:/home/ubuntu/

# SSH and setup
echo "⚙️  Setting up on VM..."
ssh ubuntu@$VM_IP << 'ENDSSH'
    cd /home/ubuntu
    tar -xzf digitalfte-cloud.tar.gz
    cd DigitalFTE

    # Install Python dependencies
    python3.13 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

    # Install Node dependencies for MCP servers
    cd mcp_servers/email_mcp && npm install && cd ../..
    cd mcp_servers/odoo_mcp && npm install && cd ../..
    cd mcp_servers/twitter_mcp && npm install && cd ../..
    cd mcp_servers/meta_social_mcp && npm install && cd ../..

    # Setup PM2 for cloud orchestrator
    pm2 delete cloud-orchestrator 2>/dev/null || true
    pm2 start agents/cloud_orchestrator.py --interpreter python3.13 --name cloud-orchestrator
    pm2 save

    # Setup cron for git sync (every 5 minutes)
    (crontab -l 2>/dev/null; echo "*/5 * * * * cd /home/ubuntu/DigitalFTE && git pull origin main && git add vault/Updates && git commit -m 'Cloud: sync updates' && git push origin main") | crontab -

    echo "✅ Cloud deployment complete!"
ENDSSH

echo "✅ Deployment successful!"
echo "📊 Monitor with: ssh ubuntu@$VM_IP 'pm2 logs cloud-orchestrator'"
