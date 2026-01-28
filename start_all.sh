#!/bin/bash
# Start entire DigitalFTE system (Docker + Agents)

set -e

cd /Users/hparacha/DigitalFTE

echo "🚀 Starting DigitalFTE..."
echo ""

# Start Docker
echo "📦 Starting Docker containers..."
docker-compose up -d
sleep 5

# Check containers
echo ""
echo "✅ Docker Status:"
docker-compose ps | grep -E "(odoo|postgres)"

echo ""
echo "🤖 Starting Agents..."
echo ""

# Create a tmux session or just run in background
nohup python agents/orchestrator.py > logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!

nohup python agents/gmail_watcher.py > logs/gmail_watcher.log 2>&1 &
GMAIL_PID=$!

nohup python agents/watchdog.py > logs/watchdog.log 2>&1 &
WATCHDOG_PID=$!

echo "✅ Agents Started"
echo "   Orchestrator PID: $ORCHESTRATOR_PID"
echo "   Gmail Watcher PID: $GMAIL_PID"
echo "   Watchdog PID: $WATCHDOG_PID"

echo ""
echo "📊 Access Points:"
echo "   Odoo Web:    http://localhost:8069"
echo "   Obsidian:    open -a Obsidian vault/"
echo ""
echo "📝 Log Files:"
echo "   tail -f logs/orchestrator.log"
echo "   tail -f logs/gmail_watcher.log"
echo "   tail -f logs/watchdog.log"
echo ""
echo "🛑 Stop All:"
echo "   kill $ORCHESTRATOR_PID $GMAIL_PID $WATCHDOG_PID"
echo "   docker-compose down"
echo ""
echo "✅ System Running!"
