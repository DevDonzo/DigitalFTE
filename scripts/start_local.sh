#!/bin/bash
# Start Local Orchestrator for Cloud/Local architecture
# Handles approvals and executes actions

set -e

echo "🚀 Starting Local Orchestrator..."

# Check if vault exists
if [ ! -d "vault" ]; then
    echo "❌ Error: vault/ directory not found"
    exit 1
fi

# Check .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

# Start git auto-sync in background (pull every 5 minutes)
echo "🔄 Starting vault sync daemon..."
(
    while true; do
        git pull origin main --rebase 2>/dev/null || true
        sleep 300
    done
) &
SYNC_PID=$!
echo "✅ Vault sync daemon running (PID: $SYNC_PID)"

# Start local orchestrator
echo "🤖 Starting local orchestrator..."
python3 agents/local_orchestrator.py &
LOCAL_PID=$!

echo ""
echo "✅ Local Orchestrator running!"
echo "📊 Monitor: tail -f vault/Logs/local_orchestrator.log"
echo "🛑 Stop: kill $LOCAL_PID $SYNC_PID"
echo ""
echo "Waiting for approvals in: vault/Pending_Approval/"
echo "Review in Obsidian, then move files to vault/Approved/"

# Wait
wait $LOCAL_PID
