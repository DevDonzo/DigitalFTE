#!/bin/bash
echo "🚀 Digital FTE Quick Setup"

# Check prerequisites
echo "Checking prerequisites..."
python3 --version || (echo "❌ Python 3 required" && exit 1)
pip --version || (echo "❌ pip required" && exit 1)

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt || (echo "❌ Failed to install dependencies" && exit 1)

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Edit .env with your API credentials"
fi

# Create vault directories if not exist
mkdir -p vault/{Inbox,Needs_Action,Plans,Pending_Approval,Approved,Rejected,Done,Accounting,Briefings,Social_Media,Logs}

# Verify setup
echo "Verifying setup..."
python Setup_Verify.py

echo ""
echo "✅ Setup complete!"
echo "Next: Get API credentials from NEXT_ACTIONS.md"
