#!/bin/bash
# Start the real orchestrator with the legacy vault-sync loop.

set -e

echo "🚀 Starting DigitalFTE orchestrator..."

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

# Start the sole approval executor.
echo "🤖 Starting orchestrator..."
python3 scripts/orchestrator.py &
ORCHESTRATOR_PID=$!

echo ""
echo "✅ Orchestrator running!"
echo "📊 Monitor the current terminal output"
echo "🛑 Stop: kill $ORCHESTRATOR_PID $SYNC_PID"
echo ""
echo "Waiting for approvals in: vault/Pending_Approval/"
echo "Review in Obsidian, then move files to vault/Approved/"

# Wait
wait $ORCHESTRATOR_PID
