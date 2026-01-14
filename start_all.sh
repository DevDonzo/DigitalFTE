#!/bin/bash
echo "🚀 Starting Digital FTE - All Services"
echo ""

cd /Users/hparacha/DigitalFTE

# Kill any existing processes
pkill -f "agents/orchestrator"
pkill -f "agents/gmail_watcher"
pkill -f "agents/whatsapp_watcher"
pkill -f "agents/webhook_server"
pkill -f "agents/watchdog"
sleep 2

# Start all services from agents/ folder
echo "Starting Orchestrator..."
python3 agents/orchestrator.py > logs/orchestrator.log 2>&1 &

echo "Starting Gmail Watcher..."
python3 agents/gmail_watcher.py > logs/gmail_watcher.log 2>&1 &

echo "Starting Webhook Server..."
python3 agents/webhook_server.py > logs/webhook_server.log 2>&1 &

echo "Starting WhatsApp Watcher..."
python3 agents/whatsapp_watcher.py > logs/whatsapp_watcher.log 2>&1 &

echo "Starting Watchdog..."
python3 agents/watchdog.py > logs/watchdog.log 2>&1 &

sleep 3
echo ""
echo "✅ All services started!"
echo ""
ps aux | grep -E "(orchestrator|gmail_watcher|whatsapp_watcher|webhook_server|watchdog)" | grep -v grep | wc -l
echo "services running"
