#!/bin/bash
echo "🚀 Starting Digital FTE - All Services"
echo ""

cd /Users/hparacha/DigitalFTE

# Kill any existing processes
pkill -f "scripts/orchestrator"
pkill -f "watchers/gmail_watcher"
pkill -f "watchers/whatsapp_watcher"
pkill -f "watchers/linkedin_watcher"
pkill -f "scripts/webhook_server"
pkill -f "scripts/watchdog"
sleep 2

# Start all services
echo "Starting Orchestrator..."
python3 scripts/orchestrator.py > logs/orchestrator.log 2>&1 &

echo "Starting Gmail Watcher..."
python3 watchers/gmail_watcher.py > logs/gmail_watcher.log 2>&1 &

echo "Starting Webhook Server..."
python3 scripts/webhook_server.py > logs/webhook_server.log 2>&1 &

echo "Starting WhatsApp Watcher..."
python3 watchers/whatsapp_watcher.py > logs/whatsapp_watcher.log 2>&1 &

echo "Starting Watchdog..."
python3 scripts/watchdog.py > logs/watchdog.log 2>&1 &

echo "Starting Weekly Audit Scheduler..."
python3 scripts/weekly_audit.py > logs/weekly_audit.log 2>&1 &

sleep 3
echo ""
echo "✅ All services started!"
echo ""
ps aux | grep -E "(orchestrator|gmail_watcher|whatsapp_watcher|webhook_server|watchdog|linkedin_watcher)" | grep -v grep | wc -l
echo "services running"
